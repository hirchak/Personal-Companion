"""Regression tests for the documentation tooling, not for the future application."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_docs import validate, public_files
from build_chatgpt_context import build

class DocToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)/'repo'
        files, errors = public_files(ROOT)
        if errors:
            raise RuntimeError('Unsafe test source tree: ' + '; '.join(errors))
        for source in files:
            target = self.root/source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source,target)
    def tearDown(self):
        self.temp.cleanup()
    def test_pristine(self):
        self.assertEqual(validate(self.root)[0],[])
    def test_missing_required(self):
        (self.root/'AGENTS.md').unlink()
        self.assertTrue(validate(self.root)[0])
    def test_permission_mismatch(self):
        p=self.root/'.project/project.json';obj=json.loads(p.read_text())
        obj['permissions']['deploy']=True;p.write_text(json.dumps(obj))
        self.assertTrue(any('Permission mismatch' in e for e in validate(self.root)[0]))
    def test_broken_link(self):
        with (self.root/'README.md').open('a') as f:f.write('\n[broken](missing-doc.md)\n')
        self.assertTrue(any('Broken local link' in e for e in validate(self.root)[0]))
    def test_private_file_denied(self):
        (self.root/'PRIVATE_test.md').write_text('synthetic placeholder')
        self.assertTrue(any('Forbidden' in e for e in validate(self.root)[0]))
    def test_denied_content_never_read(self):
        from unittest.mock import patch
        (self.root/'vault').mkdir()
        denied = self.root/'vault/note.md'
        denied.write_bytes(b'\xff')
        secret = self.root/'.env.local'
        secret.write_bytes(b'\xff')
        original = Path.read_text
        def guarded(path, *args, **kwargs):
            if path in (denied,secret):
                raise AssertionError('Denied content was read')
            return original(path,*args,**kwargs)
        with patch.object(Path,'read_text',guarded):
            errors = validate(self.root)[0]
        self.assertTrue(any('vault' in e for e in errors))
        self.assertTrue(any('.env.local' in e for e in errors))
    def test_symlink_source_denied(self):
        (self.root/'docs/linked.md').symlink_to(self.root/'README.md')
        self.assertTrue(any('symlink' in e for e in validate(self.root)[0]))
    def test_missing_pointer_denied(self):
        p=self.root/'STATE.md'
        p.write_text(p.read_text().replace('current_contract_path: docs/M1_CONTRACT.md',
                                         'current_contract_path: docs/MISSING.md'))
        self.assertTrue(any('STATE pointer' in e for e in validate(self.root)[0]))
    def test_fake_secret_detected(self):
        (self.root/'synthetic-test.txt').write_text('ghp_'+'Z'*40)
        self.assertTrue(any('Potential secret' in e for e in validate(self.root)[0]))
    def test_goal_length(self):
        (self.root/'prompts/GOAL_START.txt').write_text('/goal '+'x'*4001)
        self.assertTrue(any('4000' in e for e in validate(self.root)[0]))
    def test_unknown_source(self):
        with (self.root/'README.md').open('a') as f:f.write('\nUnknown [S99].\n')
        self.assertTrue(any('Unknown source' in e for e in validate(self.root)[0]))
    def test_snapshot_integrity(self):
        out=self.root/'generated/chatgpt_context';man=build(self.root,out)
        self.assertEqual(len(list(out.glob('*.md'))),4)
        self.assertIn('prompts/M0_BOOTSTRAP.md',man['sources'])
        for name,sha in man['outputs'].items():
            self.assertEqual(hashlib.sha256((out/name).read_bytes()).hexdigest(),sha)
    def test_output_cannot_overwrite_repo(self):
        with self.assertRaises(ValueError):build(self.root,self.root)
    def test_output_symlink_escape_denied(self):
        external=Path(self.temp.name)/'external';external.mkdir()
        (self.root/'generated').symlink_to(external,target_is_directory=True)
        with self.assertRaises(ValueError):
            build(self.root,self.root/'generated/chatgpt_context')
        self.assertEqual(list(external.iterdir()),[])
    def test_snapshot_file_symlink_denied(self):
        external=Path(self.temp.name)/'external.md';external.write_text('synthetic original')
        out=self.root/'generated/chatgpt_context';out.mkdir(parents=True)
        name=next(iter(json.loads((self.root/'.project/context_map.json').read_text())))
        (out/name).symlink_to(external)
        with self.assertRaises(ValueError):build(self.root,out)
        self.assertEqual(external.read_text(),'synthetic original')
    def test_dynamic_goal_and_report(self):
        (self.root/'prompts/M1_TEST.md').write_text('# Synthetic current goal')
        (self.root/'reports/M1_TEST.md').write_text('# Synthetic current report')
        p=self.root/'STATE.md';s=p.read_text().replace('prompts/M0_BOOTSTRAP.md','prompts/M1_TEST.md').replace('report_path: null','report_path: reports/M1_TEST.md');p.write_text(s)
        out=self.root/'generated/chatgpt_context';man=build(self.root,out)
        self.assertIn('prompts/M1_TEST.md',man['sources'])
        self.assertIn('reports/M1_TEST.md',man['sources'])
        self.assertNotIn('prompts/M0_BOOTSTRAP.md',man['sources'])

if __name__=='__main__':unittest.main()
