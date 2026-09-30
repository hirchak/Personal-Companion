#!/usr/bin/env python3
"""Build four ChatGPT snapshots from an explicit list of public canonical files."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from check_docs import validate, state_fields


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def git_head(root: Path) -> str | None:
    # Do not mistake an enclosing unrelated repository for this project.
    try:
        top = subprocess.run(['git','rev-parse','--show-toplevel'], cwd=root,
                             text=True,capture_output=True,check=True).stdout.strip()
        if Path(top).resolve() != root.resolve():
            return None
        return subprocess.run(['git','rev-parse','HEAD'], cwd=root, text=True,
                              capture_output=True,check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def contained_source(root: Path, rel: str) -> Path:
    source = (root/rel).resolve()
    if not source.is_relative_to(root.resolve()) or not source.is_file():
        raise ValueError(f'Unsafe or missing source: {rel}')
    if any(part in {'private','vault','private_context','quarantine'} for part in Path(rel).parts):
        raise ValueError(f'Private path is not allowed: {rel}')
    return source


def build(root: Path, out: Path) -> dict:
    errors, _, _ = validate(root)
    if errors:
        raise ValueError('Documentation checks failed: ' + '; '.join(errors))
    if not out.resolve().is_relative_to((root/'generated').resolve()):
        raise ValueError('Output must be inside repo/generated/ to avoid overwriting canonical files')
    out.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((root/'.project/project.json').read_text(encoding='utf-8'))
    groups = json.loads((root/'.project/context_map.json').read_text(encoding='utf-8'))
    state = state_fields((root/'STATE.md').read_text(encoding='utf-8'))
    created = datetime.now(timezone.utc).isoformat(timespec='seconds')
    # Source hashes, not timestamp, identify content. Unknown commit remains null.
    head = git_head(root)
    manifest = {'format_version':1,'spec_version':cfg['spec_version'],
                'generated_at_utc':created,'repo_url':cfg['repo_url'],'source_commit':head,
                'snapshot_only':True,'private_content_included':False,
                'sources':{},'outputs':{}}
    for output, base_sources in groups.items():
        sources = list(base_sources)
        if output == '04_DELIVERY_AND_CURRENT_STATE.md':
            for field, prefix in [('current_goal_path','prompts/'),
                                  ('current_contract_path','docs/'),
                                  ('report_path','reports/')]:
                extra = state.get(field)
                if extra:
                    if not isinstance(extra,str) or not extra.startswith(prefix):
                        raise ValueError(f'STATE {field} must be an explicit public {prefix} path')
                    if extra not in sources:
                        sources.append(extra)
        parts = [f'# {output.removesuffix(".md")}\n',
                 f'Spec version: {cfg["spec_version"]} · Spec date: {cfg["spec_date"]}\n',
                 f'Generated: {created} · Source commit: {head or "UNKNOWN / not a repository commit"}\n',
                 f'Repository: {cfg["repo_url"] or "NOT_SET"}\n',
                 '**SNAPSHOT. Для поточного стану перевірити GitHub STATE/HANDOFF і точний SHA.**\n',
                 'Цей файл автоматично зібрано з канонічних public-safe документів. '
                 'Не редагувати його як незалежне ТЗ.\n']
        for rel in sources:
            source=contained_source(root,rel)
            blob=source.read_bytes()
            sha=digest(blob)
            manifest['sources'][rel]=sha
            parts.append(f'\n---\n\n## Канонічне джерело: `{rel}`\n\nSHA-256: `{sha}`\n\n')
            parts.append(blob.decode('utf-8').strip()+'\n')
        payload='\n'.join(parts).encode('utf-8')
        (out/output).write_bytes(payload)
        manifest['outputs'][output]=digest(payload)
    instructions=(root/'context/PROJECT_INSTRUCTIONS.txt').read_bytes()
    (out/'PROJECT_INSTRUCTIONS.txt').write_bytes(instructions)
    manifest['sources']['context/PROJECT_INSTRUCTIONS.txt']=digest(instructions)
    manifest['outputs']['PROJECT_INSTRUCTIONS.txt']=digest(instructions)
    (out/'SNAPSHOT_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return manifest


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    args=parser.parse_args()
    root=args.root.resolve()
    try:
        result=build(root,root/'generated/chatgpt_context')
    except (OSError,ValueError,KeyError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr)
        return 1
    print('Built four Markdown snapshots + project instructions + hash manifest.')
    print('Source commit:', result['source_commit'] or 'UNKNOWN')
    print('Destination:',root/'generated/chatgpt_context')
    return 0

if __name__=='__main__':
    sys.exit(main())
