#!/usr/bin/env python3
"""Heuristic public-packet scan; never reads denied filesystem paths or prints values."""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path
from check_docs import public_files, SECRET_PATTERNS

PATTERNS = SECRET_PATTERNS + (
    re.compile(r'\b(?:10\.(?:\d{1,3}\.){2}\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b'),
    re.compile(r'https?://[^\s/@:]+:[^\s/@]+@'),
)
TEXT_SUFFIXES = {'.md','.txt','.json','.tsv','.py'}

def scan(root: Path, include_generated: bool = False) -> dict:
    root = root.resolve()
    files, errors = public_files(root)
    if include_generated:
        generated = root/'generated/chatgpt_context'
        if generated.is_symlink():
            errors.append('Generated directory is a symlink (not read)')
        elif generated.is_dir():
            extra, denied = public_files(generated)
            files.extend(extra); errors.extend(denied)
        else:
            errors.append('Requested generated snapshots are missing')
    metrics = {'worktree_text_files':0, 'git_objects':0, 'git_text_objects':0}
    def inspect(blob: bytes, locator: str):
        text = blob.decode('utf-8', errors='replace')
        if any(pattern.search(text) for pattern in PATTERNS):
            errors.append(f'Potential sensitive pattern (value withheld): {locator}')
    for path in files:
        if path.suffix in TEXT_SUFFIXES or path.name == '.gitignore':
            inspect(path.read_bytes(), str(path.relative_to(root)))
            metrics['worktree_text_files'] += 1
    def git(*args):
        return subprocess.run(['git',*args],cwd=root,text=True,capture_output=True,check=True).stdout
    history = 'NOT_RUN_NO_LOCAL_GIT'
    try:
        top = git('rev-parse','--show-toplevel').strip()
        if Path(top).resolve() == root:
            history = 'SCANNED_ALL_LOCAL_OBJECTS_INCLUDING_UNREACHABLE_AND_STAGED'
            for row in git('cat-file','--batch-all-objects','--batch-check=%(objectname) %(objecttype)').splitlines():
                oid, kind = row.split()
                metrics['git_objects'] += 1
                if kind in {'blob','commit','tag'}:
                    blob = subprocess.run(['git','cat-file',kind,oid],cwd=root,
                                          capture_output=True,check=True).stdout
                    inspect(blob, f'git-object:{oid}')
                    metrics['git_text_objects'] += 1
    except (OSError,subprocess.CalledProcessError):
        if (root/'.git').exists():
            errors.append('Git object scan failed; output withheld')
            history = 'FAILED'
    return {'status':'FAIL' if errors else 'PASS','errors':errors,'metrics':metrics,
            'git_scope':history,'generated_included':include_generated,
            'limitations':'Heuristics for token/private-key/private-IPv4/URL-credential patterns and denied paths. Not proof of absence of personal data, account IDs, private endpoints, copyright problems, runtime egress or secure storage. Dependency caches are excluded.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    p.add_argument('--include-generated',action='store_true')
    args=p.parse_args(); result=scan(args.root,args.include_generated)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return int(result['status'] != 'PASS')

if __name__=='__main__':
    raise SystemExit(main())
