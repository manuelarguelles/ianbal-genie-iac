import unittest
from evaluation.status import check_report_origin

class StatusOrigin(unittest.TestCase):
    def test_matching_report_is_accepted(self):
        check_report_origin({'commit':'a'},'V0','space-a',{'version':'V0','space_id':'space-a'}, {'commit':'a','version':'V0','space_id':'space-a'})
    def test_different_series_report_rejected(self):
        for report, provenance in [({'version':'V0','space_id':'space-b'},{'commit':'a','version':'V0','space_id':'space-b'}),({'version':'V0','space_id':'space-a'},{'commit':'b','version':'V0','space_id':'space-a'})]:
            with self.assertRaises(ValueError):check_report_origin({'commit':'a'},'V0','space-a',report,provenance)
