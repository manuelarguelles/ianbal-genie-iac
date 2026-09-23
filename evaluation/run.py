"""Job Python: captura una versión ya desplegada. No modifica ni mejora el Space."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys



def stamp():
    return datetime.now(timezone.utc).isoformat()


def normalized(config):
    space = json.loads(config['serialized_space']) if isinstance(config['serialized_space'], str) else config['serialized_space']
    for entry in space.get('instructions', {}).get('text_instructions', []):
        entry['content'] = [''.join(entry['content'])]
    return {**{k: config.get(k, '') for k in ('title', 'description', 'warehouse_id')}, 'serialized_space': space}


def main():
    global b
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--version', choices=['V0','V1','V2'], required=True)
    ap.add_argument('--state', required=True)
    ap.add_argument('--receipt', required=True)
    ap.add_argument('--code-root', required=True, help='Ruta explícita: el runtime no garantiza __file__')
    args = ap.parse_args()
    os.environ['S07_REMOTE'] = '1'
    sys.path.insert(0, args.code_root)
    import benchmark as b
    b.ROOT = Path(args.state)
    b.ROOT.mkdir(parents=True, exist_ok=True)
    receipt = json.loads(Path(args.receipt).read_text())
    w = b.client()
    provenance = b.ROOT / 'reports' / f'{args.version}-provenance.json'
    if provenance.exists() or (b.ROOT / 'reports' / f'{args.version}.json').exists():
        raise ValueError('Esta versión ya tiene evidencia; no se sobrescribe ni se repite para elegir mejor nota')
    before = w.genie.get_space(receipt['space_id'], include_serialized_space=True).as_dict()
    assert normalized(before) == receipt['desired'], 'La configuración remota no coincide con el commit desplegado'
    # El gold se ejecuta una sola vez, después del deploy V0. V1/V2 deben reutilizarlo.
    if not (b.ROOT / 'gold20.json').exists():
        assert args.version == 'V0', 'Falta congelar referencias en V0'
        b.save(b.ROOT / 'ianbal-v0-config.json', before)
        b.save(b.ROOT / 'benchmark20-original.json', json.loads(before['serialized_space'])['benchmarks'])
        b.freeze()
    audit = {'version': args.version, 'commit': receipt['commit'], 'space_id': receipt['space_id'],
             'deployment_at_utc': receipt['at_utc'], 'started_at_utc': stamp(), 'completed_at_utc': None,
             'config_sha256': b.sha(normalized(before)), 'deployment': receipt,
             'runner_sha256': hashlib.sha256((Path(args.code_root) / 'run.py').read_bytes()).hexdigest()}
    b.save(provenance, audit)
    b.run(args.version, receipt['space_id'])
    after = w.genie.get_space(receipt['space_id'], include_serialized_space=True).as_dict()
    assert normalized(after) == receipt['desired'], 'Drift durante la evaluación: conservar evidencia y revisar'
    report_path = b.ROOT / 'reports' / f'{args.version}.json'
    report = json.loads(report_path.read_text())
    assert len(report['cases']) == 20, 'Captura incompleta'
    audit.update(completed_at_utc=stamp(), config_stable=True,
                 report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
                 dataset_sha256=report['dataset_sha256'], rubric_sha256=report['rubric_sha256'],
                 judge=report['judge'], summary=report['summary'], run_id=report['run_id'])
    b.save(provenance, audit)
    print(json.dumps({k:v for k,v in audit.items() if k != 'deployment'}), flush=True)


if __name__ == '__main__':
    main()
