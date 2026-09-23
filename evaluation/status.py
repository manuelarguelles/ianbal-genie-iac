"""Consulta una corrida enviada: no crea trabajos, no infiere y no modifica evidencia."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deploy.genie_space import ROOT, read, client
from evaluation.location import workspace_root


def check_report_origin(submitted, version, space_id, report, provenance):
    if any(x.get('version') != version or x.get('space_id') != space_id for x in [report, provenance]):
        raise ValueError('El reporte pertenece a otra versión o Space; no se mezclan series')
    if provenance.get('commit') != submitted['commit']:
        raise ValueError('El commit del reporte no coincide con el envío')


def main():
    from databricks.sdk.errors import ResourceDoesNotExist
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('version', choices=['V0', 'V1', 'V2'])
    args = ap.parse_args()
    env = read(ROOT / '.local/classroom.json')
    path = ROOT / f'.local/submits/{args.version}.json'
    if not path.exists():
        raise SystemExit('No hay envío local registrado para ' + args.version + '. Usa la carpeta de la serie correcta; no relances para buscar una corrida.')
    submitted = read(path)
    w = client(env)
    if submitted.get('host') and submitted['host'].rstrip('/') != w.config.host.rstrip('/'):
        raise ValueError('El perfil actual apunta a otro workspace que el envío')
    remote = workspace_root({'workspace_root': submitted.get('workspace_root', '/Shared/ianbal-genie-iac')})
    space_id = submitted.get('space_id') or read(ROOT / f'.local/receipts/{args.version}.json')['space_id']
    job = w.jobs.get_run(submitted['run_id'])
    info = {'version': args.version, 'commit': submitted['commit'], 'job_run_id': submitted['run_id'],
            'job_url': job.run_page_url, 'job_state': job.state.as_dict(),
            'captured_cases': None, 'summary': None, 'mlflow_url': None}
    try:
        with w.workspace.download(remote + '/state/reports/' + args.version + '.json') as f:
            report = json.load(f)
        with w.workspace.download(remote + '/state/reports/' + args.version + '-provenance.json') as f:
            provenance = json.load(f)
        check_report_origin(submitted, args.version, space_id, report, provenance)
        info['captured_cases'] = len(report['cases'])
        info['summary'] = report.get('summary')
        if report.get('run_id'):
            info['mlflow_url'] = w.config.host.rstrip('/') + '/ml/experiments/' + str(report['experiment_id']) + '/runs/' + report['run_id']
    except ResourceDoesNotExist:
        info['note'] = 'El reporte o su procedencia aún no están disponibles. Consulta el estado y los logs del Job; pendiente no significa 0 aciertos.'
    print(json.dumps(info, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
