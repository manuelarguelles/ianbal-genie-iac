"""Valida evidencia histórica; no llama al agente ni altera el workspace."""
from datetime import datetime
import hashlib
import json
from pathlib import Path


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_series(root):
    root = Path(root)
    gold = read(root / 'gold20.json')
    require(sha(gold['cases']) == gold['dataset_sha256'], 'Gold alterado')
    require(sha(gold['rubric']) == gold['rubric_sha256'], 'Rúbrica alterada')
    expected = {c['case_id']: c for c in gold['cases']}
    require(len(gold['cases']) == len(expected) == 20, 'Se requieren 20 casos únicos')
    versions, reports, commits, spaces, runners = [], [], set(), set(), set()
    previous_end = None
    for version in ('V0', 'V1', 'V2'):
        rp = root / 'reports' / f'{version}.json'
        report = read(rp)
        audit = read(root / 'reports' / f'{version}-provenance.json')
        source = read(root / 'final-sources' / f'{version}.json')
        require(audit.get('config_stable') is True and audit.get('completed_at_utc'), 'Evaluación incompleta o drift')
        require(file_sha(rp) == audit['report_sha256'], 'Hash del reporte no coincide')
        require(report['version'] == audit['version'] == version, 'Etiqueta de versión inconsistente')
        deployment = audit['deployment']
        require(deployment['verified'] is True, 'Despliegue sin verificar')
        require(audit['runner_sha256'] == source['runner_sha256'], 'El runner no coincide con Git')
        require(report['runner_sha256_at_start'] == source['benchmark_sha256'], 'El benchmark no coincide con Git')
        require(audit['commit'] == deployment['commit'] == source['commit'], 'No coincide commit de fuente/deploy/evaluación')
        require(source['desired'] == deployment['desired'], 'Configuración distinta al commit')
        require(sha(source['desired']) == audit['config_sha256'], 'Hash de configuración distinto al commit')
        captured = read(root / 'reports' / f'{version}-config.json')
        require(sha(captured['serialized_space']) == report['config_sha256'], 'Hash de configuración capturada alterado')
        captured_space = json.loads(captured['serialized_space'])
        for entry in captured_space.get('instructions', {}).get('text_instructions', []):
            entry['content'] = [''.join(entry['content'])]
        captured_config = {**{k:captured.get(k, '') for k in ('title','description','warehouse_id')}, 'serialized_space':captured_space}
        require(captured_config == source['desired'], 'Configuración capturada por benchmark no coincide con el commit')
        require(report['space_id'] == audit['space_id'] == deployment['space_id'], 'Space diferente')
        for key in ('dataset_sha256', 'rubric_sha256', 'judge'):
            require(report[key] == gold[key], f'No comparable: {key}')
        rows = report['cases']
        require(len(rows) == 20 and {c['case_id'] for c in rows} == set(expected), 'Captura sin los 20 casos únicos')
        for case in rows:
            reference = expected[case['case_id']]
            require(case['question'] == reference['question'] and case['reference'] == reference['reference'], 'Pregunta o referencia alterada')
            require(type(case.get('correctness')) is bool or case.get('error') or case.get('judge_error'), 'Juicio ausente sin error registrado')
        deployed = datetime.fromisoformat(audit['deployment_at_utc'])
        started = datetime.fromisoformat(audit['started_at_utc'])
        ended = datetime.fromisoformat(audit['completed_at_utc'])
        require(deployed <= started <= ended, 'Orden temporal inválido')
        require(previous_end is None or previous_end <= deployed, 'El despliegue no fue secuencial: comenzó antes de terminar la evaluación anterior')
        require(audit['deployment_at_utc'] == deployment['at_utc'], 'La fecha del despliegue no coincide con el recibo')
        previous_end = ended
        commits.add(audit['commit']); spaces.add(report['space_id']); runners.add(report['runner_sha256_at_start'])
        judged = sum(type(c.get('correctness')) is bool for c in rows)
        correct = sum(c.get('correctness') is True for c in rows)
        versions.append({'version': version, 'commit': audit['commit'], 'space_id': report['space_id'],
                         'correct': correct, 'judged': judged, 'attempted': len(rows),
                         'execution_errors': sum(bool(c.get('error')) for c in rows),
                         'judge_errors': sum(bool(c.get('judge_error')) for c in rows),
                         'deployment_at_utc': audit['deployment_at_utc'], 'started_at_utc': audit['started_at_utc'],
                         'completed_at_utc': audit['completed_at_utc'], 'run_id': report['run_id'],
                         'config_sha256': audit['config_sha256'], 'report_sha256': audit['report_sha256']})
        reports.append(report)
    require(len(spaces) == 1, 'No se evaluó el mismo Space en las tres versiones')
    require(len(commits) == 3, 'Se requieren tres commits distintos')
    require(len(runners) == 1, 'El evaluador cambió entre versiones')
    deltas = []
    for old, new in zip(reports, reports[1:]):
        a = {c['case_id']: c.get('correctness') for c in old['cases']}
        b = {c['case_id']: c.get('correctness') for c in new['cases']}
        corrected = [k for k in a if a[k] is False and b[k] is True]
        regressed = [k for k in a if a[k] is True and b[k] is False]
        unpaired = [k for k in a if type(a[k]) is not bool or type(b[k]) is not bool]
        deltas.append({'from': old['version'], 'to': new['version'], 'corrected': corrected,
                       'regressed': regressed, 'unpaired': unpaired, 'net': len(corrected)-len(regressed),
                       'interpretation': 'incompleto: revisar errores' if unpaired else 'mejora observada' if len(corrected)>len(regressed) else 'sin mejora neta'})
    return {'integrity_verified': True, 'sequential_deployments': True, 'same_space': True,
            'versions': versions, 'deltas': deltas, 'dataset_sha256': gold['dataset_sha256'],
            'rubric_sha256': gold['rubric_sha256'], 'judge': gold['judge'],
            'human_review': 'pending', 'reference_issues': read(root / 'reference-issues.json') if (root / 'reference-issues.json').exists() else [], 'limitations': ['20 preguntas conocidas; no prueba de generalización',
            'El juez LLM puede variar; una sola corrida por versión', 'Referencias nominales con distintas monedas requieren revisión humana',
            'Los hashes vinculan capturas y archivos exportados de Git; no son una firma criptográfica externa']}
