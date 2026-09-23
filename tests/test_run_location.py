import unittest
from evaluation.location import workspace_root

class RunLocation(unittest.TestCase):
    def test_old_receipts_keep_original_location(self):
        self.assertEqual(workspace_root({}), '/Shared/ianbal-genie-iac')
    def test_new_series_uses_distinct_root(self):
        self.assertEqual(workspace_root({'workspace_root':'/Shared/ianbal-practica-ana/'}),'/Shared/ianbal-practica-ana')
    def test_unsafe_or_filesystem_paths_rejected(self):
        for path in ['/Workspace/Shared/test','/Shared','/Shared/a/../b','relative','/Shared/a b','/Shared/a//b']:
            with self.subTest(path=path),self.assertRaises(ValueError):workspace_root({'workspace_root':path})
