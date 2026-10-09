import hashlib
import json
import zipfile

import pytest

from scripts.m8e_q02_intake import IntakeError, PACKETS, inspect_inputs


def inputs(tmp_path):
    rows = []
    for packet in PACKETS:
        path = tmp_path / (packet + '_RAW.docx')
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>ORIGINAL_SYNTHETIC_SECRET_SENTINEL</w:t></w:r></w:p></w:body></w:document>')
        rows.append({'name': path.name, 'size_bytes': path.stat().st_size,
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (tmp_path / 'manifest.sha256.json').write_text(json.dumps({'files': rows}))
    return rows


def test_receipt_never_exports_text_or_path(tmp_path):
    inputs(tmp_path)
    receipt = inspect_inputs(tmp_path)
    assert len(receipt['files']) == 10
    assert all(row['paragraph_count_including_tables'] == 1 for row in receipt['files'])
    assert 'SENTINEL' not in json.dumps(receipt)
    assert str(tmp_path) not in json.dumps(receipt)
    assert all(row['rights_status'] == 'RIGHTS_UNKNOWN' for row in receipt['files'])


@pytest.mark.parametrize('replacement', ['../private.docx', '/private.docx', 'R07_RAW.docx', 'R02_RAW.docx'])
def test_manifest_cannot_expand_scope_or_duplicate(tmp_path, replacement):
    rows = inputs(tmp_path)
    rows[0]['name'] = replacement
    (tmp_path / 'manifest.sha256.json').write_text(json.dumps({'files': rows}))
    with pytest.raises(IntakeError, match='Q02_EXACT_TEN_INPUTS_REQUIRED'):
        inspect_inputs(tmp_path)


def test_changed_bytes_fail_even_same_size(tmp_path):
    inputs(tmp_path)
    p = tmp_path / 'R01_RAW.docx'
    blob = p.read_bytes()
    p.write_bytes(bytes([blob[0] ^ 1]) + blob[1:])
    with pytest.raises(IntakeError, match='Q02_SOURCE_HASH_MISMATCH'):
        inspect_inputs(tmp_path)


def test_symlink_denied_without_following(tmp_path):
    inputs(tmp_path)
    p = tmp_path / 'R01_RAW.docx'
    p.unlink()
    p.symlink_to(tmp_path / 'R02_RAW.docx')
    with pytest.raises(IntakeError, match='Q02_SOURCE_MISSING_OR_SYMLINK'):
        inspect_inputs(tmp_path)


def test_missing_source_not_replaced_by_other_file(tmp_path):
    inputs(tmp_path)
    (tmp_path / 'R01_RAW.docx').unlink()
    with pytest.raises(IntakeError, match='Q02_SOURCE_MISSING_OR_SYMLINK'):
        inspect_inputs(tmp_path)
