import io
import unittest
from databricks.sdk.errors import ResourceDoesNotExist
from deploy.upload import ensure_file

class Workspace:
    def __init__(self):self.files={}
    def download(self,path):
        if path not in self.files:raise ResourceDoesNotExist('missing')
        return io.BytesIO(self.files[path])
    def upload(self,path,content,**kw):
        if path in self.files:raise AssertionError('must not overwrite')
        self.files[path]=content

class UploadTests(unittest.TestCase):
    def test_existing_identical_revision_reusable(self):
        w=Workspace();w.files['r']=b'code';ensure_file(w,'r',b'code');self.assertEqual(w.files['r'],b'code')
    def test_changed_revision_rejected(self):
        w=Workspace();w.files['r']=b'original'
        with self.assertRaises(ValueError):ensure_file(w,'r',b'different')
        self.assertEqual(w.files['r'],b'original')
    def test_missing_file_created(self):
        w=Workspace();ensure_file(w,'r',b'code');self.assertEqual(w.files['r'],b'code')
