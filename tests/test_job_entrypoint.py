import unittest
from pathlib import Path

class JobEntrypoint(unittest.TestCase):
    def test_databricks_exec_without_file_global_can_load_entrypoint(self):
        path=Path(__file__).resolve().parents[1]/'evaluation/run.py'
        namespace={'__name__':'job_test'}
        exec(compile(path.read_text(),str(path),'exec'),namespace)
        self.assertTrue(callable(namespace['main']))
