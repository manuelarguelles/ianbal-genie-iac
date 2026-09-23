import unittest, math, tempfile, json
from pathlib import Path
import benchmark as b
class Metrics(unittest.TestCase):
 def test_save_creates_output_directory(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'reports'/'V0.json';b.save(p,{'ok':True});self.assertTrue(json.loads(p.read_text())['ok'])
 def test_pending_is_not_zero_percent(self):
  s=b.summarize([]);self.assertEqual(s['judged'],0);self.assertIsNone(s['median_s']);self.assertEqual(s['planned'],20)
 def test_denominators_keep_errors_and_unjudged(self):
  rows=[{'latency_s':1,'correctness':True,'relevance':True},{'latency_s':2,'correctness':False,'relevance':True},{'latency_s':3,'error':'timeout','correctness':None}]
  s=b.summarize(rows);self.assertEqual((s['attempted'],s['judged'],s['correct'],s['execution_errors']),(3,2,1,1));self.assertEqual(s['p95_s'],3)
 def test_p95_twenty_is_nineteenth(self):
  rows=[{'latency_s':i,'correctness':True,'relevance':True} for i in range(1,21)]
  self.assertEqual(b.summarize(rows)['p95_s'],19)
 def test_sql_incomplete_is_rejected(self):
  with self.assertRaises(ValueError):b.complete_statement({'status':{'state':'SUCCEEDED'},'manifest':{'total_row_count':2},'result':{'data_array':[['1']]}})
 def test_hash_order_is_canonical(self):self.assertEqual(b.sha({'a':1,'b':2}),b.sha({'b':2,'a':1}))
class ComparisonIntegrity(unittest.TestCase):
 def test_changed_reference_is_rejected(self):
  original=b.ROOT
  with tempfile.TemporaryDirectory() as tmp:
   try:
    b.ROOT=Path(tmp)
    cases=[{'case_id':'I01','question':'q','reference':{'rows':[['1']]}}]
    b.save(b.ROOT/'gold20.json',{'cases':cases,'dataset_sha256':b.sha(cases)})
    b.save(b.ROOT/'reports'/'V0.json',{'version':'V0','dataset_sha256':b.sha(cases),'rubric_sha256':'r','judge':'j','cases':[{'case_id':'I01','question':'q','reference':{'rows':[['2']]},'latency_s':1,'correctness':True,'relevance':True}]})
    with self.assertRaisesRegex(AssertionError,'Referencia o pregunta alterada'):b.compare()
   finally:b.ROOT=original
if __name__=='__main__':unittest.main()
