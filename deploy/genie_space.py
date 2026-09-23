"""Configuración como código: render, create, plan, apply y export de Genie.

Los JSON completos y backups son locales. Nunca modifica el Space fuente.
"""
import argparse
import copy
import difflib
import hashlib
import json
from pathlib import Path
import uuid
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text())


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    path.chmod(0o600)


def canonical(value):
    value = copy.deepcopy(value)
    for entry in value.get('instructions', {}).get('text_instructions', []):
        entry['content'] = [''.join(entry['content'])]
    return value


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def render(base, prompt, env):
    space = canonical(base)
    entries = space.setdefault('instructions', {}).setdefault('text_instructions', [])
    if len(entries) != 1:
        raise ValueError('Se requiere exactamente un contenedor text_instructions')
    # Este archivo ES el prompt completo: reemplaza contenido, nunca añade una base oculta.
    entries[0]['content'] = [prompt]
    return {**{k: env[k] for k in ('title', 'description', 'warehouse_id')}, 'serialized_space': space}


def git_revision():
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True)
    if dirty.strip():
        raise ValueError('Haz commit antes de desplegar: el árbol Git debe estar limpio')
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()


def now():
    return datetime.now(timezone.utc).isoformat()


def remote(w, space_id):
    # REST documentado: el SDK instalado todavía no expone etag en update_space.
    raw = w.api_client.do('GET', f'/api/2.0/genie/spaces/{space_id}', query={'include_serialized_space': True})
    data = {k: raw.get(k, '') for k in ('title', 'description', 'warehouse_id')}
    data['serialized_space'] = canonical(json.loads(raw['serialized_space']))
    return data, raw.get('etag')


def make_plan(current, desired, space_id, host):
    return {'space_id': space_id, 'host': host.rstrip('/'), 'before_sha256': digest(current),
            'desired_sha256': digest(desired), 'changed': current != desired, 'desired': desired}


def check_plan(plan, current, host):
    if plan['host'] != host.rstrip('/'):
        raise ValueError('El plan pertenece a otro workspace')
    if plan['before_sha256'] != digest(current):
        raise ValueError('Drift desde el plan: vuelve a ejecutar plan y revisar el diff')
    if plan['desired_sha256'] != digest(plan['desired']):
        raise ValueError('El artefacto deseado cambió después del plan')


def desired_for(env):
    return render(read(ROOT / 'agente/space.json'),
                  (ROOT / 'agente/instrucciones.md').read_text(), env)


def client(env):
    from databricks.sdk import WorkspaceClient
    return WorkspaceClient(profile=env['profile'])


def apply_plan(w, plan, state_dir):
    before, etag = remote(w, plan['space_id'])
    check_plan(plan, before, w.config.host)
    run = Path(state_dir) / uuid.uuid4().hex
    save(run / 'before.json', before)
    save(run / 'plan.json', plan)
    changed = before != plan['desired']
    if changed:
        if not etag:
            raise ValueError('Este workspace no devolvió ETag; no se aplica sin control de concurrencia')
        payload = copy.deepcopy(plan['desired'])
        payload['serialized_space'] = json.dumps(payload['serialized_space'], ensure_ascii=False)
        payload['etag'] = etag  # Rechaza una edición concurrente posterior al GET.
        w.api_client.do('PATCH', f"/api/2.0/genie/spaces/{plan['space_id']}", body=payload)
    after, _ = remote(w, plan['space_id'])
    save(run / 'after.json', after)
    receipt = {'space_id': plan['space_id'], 'changed': changed,
               'verified': digest(after) == plan['desired_sha256'],
               'before_sha256': digest(before), 'after_sha256': digest(after),
               'url': f"{w.config.host.rstrip('/')}/genie/rooms/{plan['space_id']}"}
    save(run / 'receipt.json', receipt)
    if not receipt['verified']:
        raise ValueError(f'El export no coincide con lo aplicado; revisa {run}')
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['render', 'create', 'plan', 'apply', 'export'])
    parser.add_argument('--env', default='.local/classroom.json')
    parser.add_argument('--label', default='manual', help='Etiqueta de evidencia; no selecciona otra configuración')
    parser.add_argument('--out', default='.local/plan.json')
    parser.add_argument('--plan', default='.local/plan.json')
    args = parser.parse_args()
    env_path = ROOT / args.env
    env = read(env_path)
    commit = git_revision()
    if args.command == 'render':
        save(ROOT / args.out, desired_for(env))
        print(f'Render offline guardado: {args.out}')
        return
    w = client(env)
    if args.command == 'create':
        if env.get('space_id'):
            raise ValueError('El entorno ya tiene Space. Usa plan/apply para actualizarlo')
        desired = desired_for(env)
        payload = {**desired, 'serialized_space': json.dumps(desired['serialized_space'], ensure_ascii=False)}
        result = w.genie.create_space(**payload)
        # Persistir inmediatamente el ID permite recuperar un fallo de verificación sin duplicarlo.
        env['space_id'] = result.space_id
        save(env_path, env)
        actual, _ = remote(w, result.space_id)
        receipt = {'space_id': result.space_id, 'verified': actual == desired, 'sha256': digest(actual), 'commit': commit, 'at_utc': now(), 'desired': desired}
        save(ROOT / '.local/create-receipt.json', receipt)
        if not receipt['verified']:
            raise ValueError('Creado pero no coincide con el render. Revisar antes de continuar')
        save(ROOT / '.local/deployed.json', receipt)
        save(ROOT / f'.local/receipts/{args.label}.json', receipt)
        print(json.dumps({k:v for k,v in receipt.items() if k != 'desired'}))
        return
    if not env.get('space_id'):
        raise ValueError('Ejecuta create para crear el Space de práctica primero')
    if args.command == 'apply':
        plan = read(ROOT / args.plan)
        if plan['space_id'] != env['space_id']:
            raise ValueError('El plan apunta a un Space diferente al entorno seleccionado')
        if plan.get('commit') != commit:
            raise ValueError('El commit cambió desde el plan; genera otro plan')
        receipt = apply_plan(w, plan, ROOT / '.local/deployments')
        receipt.update(commit=commit, at_utc=now(), desired=plan['desired'])
        save(ROOT / '.local/deployed.json', receipt)
        save(ROOT / f'.local/receipts/{args.label}.json', receipt)
        print(json.dumps({k:v for k,v in receipt.items() if k != 'desired'}))
        return
    current, _ = remote(w, env['space_id'])
    if args.command == 'export':
        save(ROOT / args.out, current)
        print(f'Export guardado: {args.out}')
        return
    desired = desired_for(env)
    plan = make_plan(current, desired, env['space_id'], w.config.host)
    plan['commit'] = commit
    save(ROOT / args.out, plan)
    before_lines = json.dumps(current, ensure_ascii=False, indent=2).splitlines()
    after_lines = json.dumps(desired, ensure_ascii=False, indent=2).splitlines()
    print('\n'.join(difflib.unified_diff(before_lines, after_lines, fromfile='Databricks actual', tofile=commit[:12])))
    print(f"changed={plan['changed']}; plan={args.out}")


if __name__ == '__main__':
    main()
