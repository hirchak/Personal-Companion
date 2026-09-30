"""Synthetic scanner tests, including a secret removed from the working tree."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_privacy import scan

class PrivacyToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()
    def test_public_text(self):
        (self.root/'README.md').write_text('Synthetic note only')
        self.assertEqual(scan(self.root)['status'],'PASS')
    def test_denied_file_not_read(self):
        (self.root/'auth.json').write_bytes(b'\xff')
        original=Path.read_bytes
        def guarded(path,*args,**kwargs):
            if path.name=='auth.json':
                raise AssertionError('Denied file was read')
            return original(path,*args,**kwargs)
        with patch.object(Path,'read_bytes',guarded):
            self.assertEqual(scan(self.root)['status'],'FAIL')
    def test_history_and_staged_blob(self):
        def git(*args):
            return subprocess.run(['git',*args],cwd=self.root,capture_output=True,check=True)
        git('init','-b','synthetic')
        p=self.root/'synthetic.txt'; token='ghp_'+'Z'*40
        p.write_text(token); git('add','--','synthetic.txt')
        staged=scan(self.root)
        self.assertTrue(any('git-object:' in e for e in staged['errors']))
        git('-c','user.name=Synthetic Reviewer','-c','user.email=synthetic@example.invalid',
            'commit','-m','synthetic fixture')
        p.write_text('clean synthetic content');git('add','--','synthetic.txt')
        git('-c','user.name=Synthetic Reviewer','-c','user.email=synthetic@example.invalid',
            'commit','-m','remove synthetic pattern')
        result=scan(self.root)
        self.assertEqual(result['status'],'FAIL')
        self.assertTrue(any('git-object:' in e for e in result['errors']))
        self.assertNotIn(token,json.dumps(result))
    def test_generated_snapshot_scanned(self):
        folder=self.root/'generated/chatgpt_context';folder.mkdir(parents=True)
        (folder/'snapshot.md').write_text('sk-'+'Z'*40)
        self.assertEqual(scan(self.root)['status'],'PASS')
        self.assertEqual(scan(self.root,include_generated=True)['status'],'FAIL')

if __name__=='__main__':
    unittest.main()
