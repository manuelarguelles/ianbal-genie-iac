import copy, json, tempfile, unittest
from pathlib import Path
from evaluation.validate import validate_series, sha, file_sha

class FinalValidation(unittest.TestCase):
    def fixture(self, root, scores=(17, 16, 18)):
        cases=[{'case_id':f'I{i:02}', 'question':f'Q{i}', 'reference':{'rows':[[str(i)]]}} for i in range(1,21)]
        gold={'cases':cases, 'dataset_sha256':sha(cases), 'rubric':'fixed', 'rubric_sha256':sha('fixed'), 'judge':'fixed-judge'}
        def save(path,obj):
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj))
        save(root/'gold20.json',gold)
        for n,score in enumerate(scores):
            v=f'V{n}'; cfg={'title':'demo','warehouse_id':'w','description':'d','serialized_space':{'version':2,'instructions':{'text_instructions':[{'id':'a','content':[f'full prompt {v}']}]}}}
            desired=copy.deepcopy(cfg)
            source={'commit':str(n)*40,'desired':desired,'benchmark_sha256':'same-runner','runner_sha256':'wrapper'}
            save(root/f'final-sources/{v}.json',source)
            rows=[{**c,'correctness':i<score,'relevance':True,'error':None,'judge_error':None} for i,c in enumerate(cases)]
            report={'space_id':'same-space','version':v,'cases':rows,'dataset_sha256':gold['dataset_sha256'],'rubric_sha256':gold['rubric_sha256'],'judge':'fixed-judge','runner_sha256_at_start':'same-runner','run_id':v}
            cfg['serialized_space']=json.dumps(cfg['serialized_space'])
            save(root/f'reports/{v}-config.json',cfg)
            report['config_sha256']=sha(cfg['serialized_space'])
            rp=root/f'reports/{v}.json';save(rp,report)
            prov={'version':v,'commit':str(n)*40,'space_id':'same-space','config_stable':True,'runner_sha256':'wrapper','config_sha256':sha(desired),'report_sha256':file_sha(rp),'started_at_utc':f'2026-09-23T{10+n}:01:00+00:00','completed_at_utc':f'2026-09-23T{10+n}:02:00+00:00','deployment_at_utc':f'2026-09-23T{10+n}:00:00+00:00','deployment':{'at_utc':f'2026-09-23T{10+n}:00:00+00:00','verified':True,'commit':str(n)*40,'space_id':'same-space','desired':desired}}
            save(root/f'reports/{v}-provenance.json',prov)

    def test_regression_is_reported_not_hidden(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);out=validate_series(root)
            self.assertEqual([x['correct'] for x in out['versions']],[17,16,18])
            self.assertEqual(out['deltas'][0]['net'], -1)
            self.assertEqual(out['deltas'][0]['regressed'],['I17'])
            self.assertEqual(out['deltas'][1]['corrected'],['I17','I18'])

    def test_changed_report_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);p=root/'reports/V0.json';p.write_text(p.read_text()+' ')
            with self.assertRaisesRegex(ValueError,'reporte'):validate_series(root)

    def test_non_sequential_deployment_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);p=root/'reports/V1-provenance.json';d=json.loads(p.read_text());d['deployment_at_utc']='2026-09-23T09:00:00+00:00';p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'secuencial'):validate_series(root)

    def test_wrong_commit_configuration_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);p=root/'final-sources/V1.json';d=json.loads(p.read_text());d['desired']['title']='other';p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'commit'):validate_series(root)

    def test_incomplete_capture_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);p=root/'reports/V2.json';d=json.loads(p.read_text());d['cases'].pop();p.write_text(json.dumps(d));prov=root/'reports/V2-provenance.json';a=json.loads(prov.read_text());a['report_sha256']=file_sha(p);prov.write_text(json.dumps(a))
            with self.assertRaisesRegex(ValueError,'20'):validate_series(root)

    def test_evaluated_configuration_snapshot_must_match_deployment(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);p=root/'reports/V1-config.json';d=json.loads(p.read_text());d['title']='different agent';p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'capturada'):validate_series(root)

    def test_runner_differs_from_git_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);p=root/'final-sources/V1.json';d=json.loads(p.read_text());d['runner_sha256']='changed';p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'runner'):validate_series(root)

    def test_inconsistent_deployment_timestamp_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);p=root/'reports/V1-provenance.json';d=json.loads(p.read_text());d['deployment']['at_utc']='2026-09-23T08:00:00+00:00';p.write_text(json.dumps(d))
            with self.assertRaisesRegex(ValueError,'fecha'):validate_series(root)
