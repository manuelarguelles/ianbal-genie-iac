"""Sube el evaluador del commit actual y lanza un Job Python serverless, no un notebook."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deploy.genie_space import ROOT, read, save, client, git_revision

REMOTE = '/Shared/ianbal-genie-iac'


def main():
    from databricks.sdk.service.workspace import ImportFormat
    from databricks.sdk.service.jobs import SubmitTask, SparkPythonTask, Source, JobEnvironment
    from databricks.sdk.service.compute import Environment
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('version', choices=['V0', 'V1', 'V2'])
    args = ap.parse_args()
    commit = git_revision()
    env = read(ROOT / '.local/classroom.json')
    receipt = read(ROOT / '.local/deployed.json')
    assert receipt['commit'] == commit, 'El commit actual todavía no está desplegado'
    assert receipt['space_id'] == env['space_id']
    local_submit = ROOT / f'.local/submits/{args.version}.json'
    if local_submit.exists():
        raise ValueError('Ya se envió esta versión; consulta su run_id antes de actuar')
    w = client(env)
    revision = REMOTE + '/revisions/' + commit
    w.workspace.mkdirs(revision)
    w.workspace.mkdirs(REMOTE + '/state/receipts')
    for name in ['benchmark.py', 'run.py']:
        w.workspace.upload(revision + '/' + name, (ROOT / 'evaluation' / name).read_bytes(), format=ImportFormat.AUTO, overwrite=False)
    receipt_path = REMOTE + '/state/receipts/' + args.version + '.json'
    w.workspace.upload(receipt_path, (ROOT / '.local/deployed.json').read_bytes(), format=ImportFormat.AUTO, overwrite=False)
    environment = JobEnvironment(environment_key='benchmark', spec=Environment(environment_version='5', dependencies=['mlflow[databricks]==3.16.0', 'databricks-sdk==0.140.0', 'openai==3.16.2']))
    result = w.jobs.submit(run_name=f'Ianbal-IaC-{args.version}-{commit[:8]}',
        tasks=[SubmitTask(task_key='benchmark', spark_python_task=SparkPythonTask(
            python_file='/Workspace' + revision + '/run.py', source=Source.WORKSPACE,
            parameters=['--version', args.version, '--state', '/Workspace' + REMOTE + '/state', '--receipt', '/Workspace' + receipt_path]),
            environment_key='benchmark', max_retries=0)], environments=[environment], timeout_seconds=3600)
    save(local_submit, {'run_id':result.run_id, 'commit':commit, 'version':args.version, 'kind':'spark_python_task'})
    print(f'{args.version}: run_id={result.run_id}, commit={commit}')


if __name__ == '__main__':
    main()
