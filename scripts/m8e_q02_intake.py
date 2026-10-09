"""Read only the ten explicitly supplied Q02 inputs; emit metadata, never RAW text.

This is receipt/integrity evidence, not source verification, rights clearance or
clinical review. No recursive discovery, extraction, network or candidate loading.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile
from xml.etree import ElementTree

PACKETS = ('R01', 'R02', 'R03', 'R04', 'R05', 'R06', 'R08', 'R09', 'R11', 'R12')
NAMES = {packet + '_RAW.docx' for packet in PACKETS}
MAX_FILE = 32 * 1024 * 1024
MAX_XML = 16 * 1024 * 1024
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


class IntakeError(ValueError):
    """Fixed public-safe code only; never include filesystem/provider/input text."""


def inspect_inputs(directory):
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise IntakeError('Q02_INPUT_DIRECTORY_REQUIRED')
    manifest = directory / 'manifest.sha256.json'
    if manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_size > 65536:
        raise IntakeError('Q02_MANIFEST_INVALID')
    try:
        value = json.loads(manifest.read_text())
    except (OSError, UnicodeError, ValueError):
        raise IntakeError('Q02_MANIFEST_INVALID') from None
    files = value.get('files') if isinstance(value, dict) else None
    if (not isinstance(files, list) or len(files) != len(NAMES)
            or any(not isinstance(row, dict) for row in files)
            or {row.get('name') for row in files if isinstance(row.get('name'), str)} != NAMES):
        raise IntakeError('Q02_EXACT_TEN_INPUTS_REQUIRED')
    rows = []
    for row in files:
        name = row['name']  # exact allowlist above; never arbitrary relative paths
        expected = row.get('sha256')
        size = row.get('size_bytes')
        if (not isinstance(expected, str) or not re.fullmatch('[0-9a-f]{64}', expected)
                or type(size) is not int or not 0 < size <= MAX_FILE):
            raise IntakeError('Q02_MANIFEST_INVALID')
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise IntakeError('Q02_SOURCE_MISSING_OR_SYMLINK')
        if path.stat().st_size != size:
            raise IntakeError('Q02_SOURCE_SIZE_MISMATCH')
        blob = path.read_bytes()
        actual = hashlib.sha256(blob).hexdigest()
        if actual != expected:
            raise IntakeError('Q02_SOURCE_HASH_MISMATCH')
        try:
            # No zip extraction or relationship following. Only bounded document XML.
            with zipfile.ZipFile(path) as archive:
                matches = [i for i in archive.infolist() if i.filename == 'word/document.xml']
                if len(matches) != 1 or matches[0].file_size > MAX_XML:
                    raise IntakeError('Q02_DOCX_XML_INVALID')
                xml = archive.read(matches[0])
            if b'<!DOCTYPE' in xml or b'<!ENTITY' in xml:
                raise IntakeError('Q02_DOCX_XML_INVALID')
            body = ElementTree.fromstring(xml).find(W + 'body')
            if body is None:
                raise IntakeError('Q02_DOCX_XML_INVALID')
            paragraphs = sum(1 for _ in body.iter(W + 'p'))
            tables = sum(1 for _ in body.iter(W + 'tbl'))
        except (OSError, zipfile.BadZipFile, KeyError, ElementTree.ParseError, RuntimeError):
            raise IntakeError('Q02_DOCX_XML_INVALID') from None
        rows.append({'packet_id': name[:3], 'name': name, 'sha256': actual,
                     'size_bytes': size, 'paragraph_count_including_tables': paragraphs,
                     'table_count': tables, 'receipt_status': 'SOURCE_RECEIVED',
                     'evidence_status': 'RAW_UNREVIEWED', 'rights_status': 'RIGHTS_UNKNOWN',
                     'qualified_content_review': 'PENDING'})
    return {'schema_version': 1, 'status': 'SOURCE_INTEGRITY_PASS',
            'manifest_sha256': hashlib.sha256(manifest.read_bytes()).hexdigest(),
            'files': sorted(rows, key=lambda row: row['packet_id']),
            'raw_text_exported': False, 'network_calls': 0, 'clinical_activation': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = inspect_inputs(args.input_dir)
    except IntakeError as error:
        print(json.dumps({'status': 'FAIL', 'code': str(error)}))
        return 2
    except OSError:
        print(json.dumps({'status': 'FAIL', 'code': 'Q02_INPUT_UNREADABLE'}))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
