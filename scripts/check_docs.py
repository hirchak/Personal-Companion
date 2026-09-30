#!/usr/bin/env python3
"""Validate documentation consistency. This is NOT a security or clinical audit."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = (
    'README.md', 'START_HERE.md', 'AGENTS.md', 'STATE.md', 'HANDOFF.md',
    '.project/project.json', '.project/context_map.json', 'docs/ARCHITECTURE.md',
    'docs/PRIVACY_SECURITY.md', 'docs/OFFLINE_SYNC.md', 'docs/SAFETY.md',
    'docs/WORKFLOW.md', 'docs/ROADMAP.md', 'docs/TESTING.md',
    'research/RESEARCH_PLAN.md', 'research/MASTER_RESEARCH_PROMPT.md',
    'research/SOURCES.md', 'research/sources.json',
    'prompts/M0_BOOTSTRAP.md', 'prompts/GOAL_START.txt',
    'context/PROJECT_INSTRUCTIONS.txt', '.gitignore',
)
EXCLUDED = {'.git', 'generated', '__pycache__', '.venv', 'node_modules'}
FORBIDDEN_DIRS = {'private', 'vault', 'private_context', 'user-data', 'user_data', 'quarantine'}
FORBIDDEN_EXTENSIONS = {'.sqlite', '.sqlite3', '.db', '.key', '.pem', '.p12', '.wav', '.m4a'}
SECRET_PATTERNS = (
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b'),
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{40,}\b'),
    re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{24,}\b'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
)

def scalar(raw: str):
    value = raw.strip()
    if value in ('null', '~'):
        return None
    if value in ('true', 'false'):
        return value == 'true'
    return value.strip('"\'')


def state_fields(text: str) -> dict:
    if not text.startswith('---\n'):
        raise ValueError('STATE.md needs simple YAML front matter')
    sections = text.split('---', 2)
    if len(sections) < 3:
        raise ValueError('Unclosed STATE front matter')
    result = {}
    for line in sections[1].splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        key, sep, value = line.partition(':')
        if not sep or key.strip() in result:
            raise ValueError(f'Invalid/duplicate STATE field: {key}')
        result[key.strip()] = scalar(value)
    return result


def validate(root: Path) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warnings: list[str] = []
    metrics = {'files_checked': 0, 'json_checked': 0, 'local_links_checked': 0,
               'research_prompts': 0, 'snapshot_source_files': 0}
    for name in REQUIRED:
        if not (root/name).is_file():
            errors.append(f'Missing required file: {name}')
    if errors:
        return errors, warnings, metrics

    files = [p for p in root.rglob('*') if p.is_file()
             and not set(p.relative_to(root).parts).intersection(EXCLUDED)]
    for path in files:
        rel = path.relative_to(root)
        metrics['files_checked'] += 1
        if path.is_symlink():
            errors.append(f'Symlink needs explicit review: {rel}')
            continue
        if (set(rel.parts).intersection(FORBIDDEN_DIRS) or path.name.startswith('PRIVATE_')
                or path.suffix in FORBIDDEN_EXTENSIONS
                or path.name in ('.env', 'auth.json', 'credentials.json')):
            errors.append(f'Forbidden private/secret file in documentation packet: {rel}')
        if path.suffix not in {'.md', '.txt', '.json', '.tsv', '.py'} and path.name != '.gitignore':
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            errors.append(f'Expected UTF-8: {rel}')
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f'Potential secret pattern (do not print its value): {rel}')
        if path.suffix == '.json':
            try:
                json.loads(text)
                metrics['json_checked'] += 1
            except json.JSONDecodeError as exc:
                errors.append(f'Invalid JSON: {rel}: {exc.msg}')
        if path.suffix == '.md':
            fences = sum(1 for line in text.splitlines() if line.strip().startswith('```'))
            if fences % 2:
                errors.append(f'Unpaired Markdown code fence: {rel}')
            # This checks explicit Markdown local links, not prose paths or external URLs.
            for link in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)', text):
                target = link.strip().split('#', 1)[0]
                if not target or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', target):
                    continue
                metrics['local_links_checked'] += 1
                resolved = (path.parent / target).resolve()
                if not resolved.is_relative_to(root.resolve()):
                    errors.append(f'Local link escapes repo: {rel}: {target}')
                elif not resolved.exists():
                    errors.append(f'Broken local link: {rel}: {target}')

    try:
        cfg = json.loads((root/'.project/project.json').read_text())
        st = state_fields((root/'STATE.md').read_text())
        for sk, ck in [('repo_url','repo_url'), ('review_branch','review_branch'),
                       ('project_slug','project_slug'), ('packet_version','spec_version')]:
            if st.get(sk) != cfg.get(ck):
                errors.append(f'STATE vs project.json mismatch: {sk}')
        perms = cfg.get('permissions', {})
        for sk, pk in [('push_authorized','push_review_branch'),
                       ('deployment_authorized','deploy'),
                       ('paid_or_subscription_calls_authorized','live_provider_calls'),
                       ('real_user_data_allowed_in_development','access_real_user_data')]:
            if st.get(sk) != perms.get(pk):
                errors.append(f'Permission mismatch: {sk}')
        if st.get('repo_url') is None:
            warnings.append('Repository URL is intentionally unset; remote review has not happened.')
        if st.get('implementation_status') == 'NOT_STARTED':
            warnings.append('Application implementation is NOT_STARTED; doc checks are not application tests.')
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        errors.append(f'Metadata validation error: {exc}')

    try:
        mapping = json.loads((root/'.project/context_map.json').read_text())
        if len(mapping) != 4:
            errors.append('Exactly four context groups expected')
        seen = set()
        for output, inputs in mapping.items():
            if Path(output).name != output or not output.endswith('.md'):
                errors.append(f'Unsafe snapshot filename: {output}')
            for name in inputs:
                source = (root/name).resolve()
                if not source.is_relative_to(root.resolve()) or not source.is_file():
                    errors.append(f'Missing/unsafe snapshot source: {name}')
                if name in seen:
                    errors.append(f'Duplicate canonical snapshot source: {name}')
                seen.add(name)
        metrics['snapshot_source_files'] = len(seen)
    except (ValueError, TypeError) as exc:
        errors.append(f'Context map error: {exc}')

    for n in range(1,17):
        path = root/f'research/prompts/R{n:02d}.md'
        if not path.exists():
            errors.append(f'Missing research brief: R{n:02d}')
        else:
            metrics['research_prompts'] += 1
    goal = (root/'prompts/GOAL_START.txt').read_text().strip()
    if not goal.startswith('/goal ') or len(goal.removeprefix('/goal ')) > 4000:
        errors.append('Initial /goal missing or exceeds the documented 4000-character objective limit')
    try:
        sources = json.loads((root/'research/sources.json').read_text())
        ids = [s['id'] for s in sources]
        if len(ids) != len(set(ids)):
            errors.append('Duplicate source IDs')
        valid = set(ids)
        for path in files:
            if path.suffix == '.md':
                for sid in re.findall(r'\[(S\d{2})\]',path.read_text(encoding='utf-8')):
                    if sid not in valid:
                        errors.append(f'Unknown source ID {sid}: {path.relative_to(root)}')
    except (ValueError, KeyError) as exc:
        errors.append(f'Source registry error: {exc}')
    return errors, warnings, metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    errors, warnings, metrics = validate(args.root.resolve())
    result = {'status': 'PASS' if not errors else 'FAIL', 'errors': errors,
              'warnings': warnings, 'metrics': metrics,
              'scope': 'Documentation structure only; not exhaustive privacy, security, clinical or app verification.'}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(result['status'] + ' — documentation checks')
        for msg in errors:
            print('ERROR:',msg)
        for msg in warnings:
            print('NOTE:',msg)
        print(json.dumps(metrics,ensure_ascii=False))
        print(result['scope'])
    return 1 if errors else 0

if __name__ == '__main__':
    sys.exit(main())
