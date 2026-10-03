#!/usr/bin/env python3
"""Offline preparation validator. Never imports the application or activates protocols."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Annotated, Literal, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, ValidationError, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
Hash = Annotated[str, StringConstraints(pattern=r'^[0-9a-f]{64}$')]
Sha = Annotated[str, StringConstraints(pattern=r'^[0-9a-f]{40}$')]
PacketId = Annotated[str, StringConstraints(pattern=r'^R(?:0[1-9]|1[0-6])$')]
FindingId = Annotated[str, StringConstraints(pattern=r'^RG-(?:0[1-9]|1[0-9]|2[0-7])$')]
ClaimId = Annotated[str, StringConstraints(pattern=r'^claim:RG-(?:0[1-9]|1[0-9]|2[0-7])$')]
SourceId = Annotated[str, StringConstraints(pattern=r'^gate:S(?:0[1-9]|1[0-6])$')]
EXPECTED_PERMISSIONS = {'push_review_branch': False, 'push_main': True, 'merge_main': False,
                        'deploy': False, 'live_provider_calls': False, 'access_real_user_data': False}
BASE = '7516c9487346d8c3f0cc0b6224bdfe7354f5153a'
CLINICAL_MODULES = {'sleep_education', 'thought_record', 'worry_rumination', 'activity_self_kindness',
                    'grounding_relaxation', 'dream_irt', 'questionnaires', 'clinical_sleep_window',
                    'trauma_processing_diagnosis_medication'}
C6 = '1d30db9677f2c7b6f07145e8c0c5263969f39d3e'
PACK_MANIFEST_SHA256 = '383b157ef83709c683e8d4349c2ffc1c67c1d1c5db8932240ab7c1183b531cf9'
EXTERNAL_FILES = ('INPUT_MANIFEST.json', 'REVIEW_FINDINGS.json', 'PRIMARY_SOURCE_CHECKS.json',
                  'PACKET_DISPOSITIONS.json', 'MODULE_ADMISSION_DRAFT.json',
                  'ADMISSION_EVAL_CANDIDATES.jsonl', 'REPOSITORY_CHECKPOINT.json')


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

    @model_validator(mode='before')
    @classmethod
    def exact_boolean_types(cls, value):
        if isinstance(value, dict):
            for key, field in cls.model_fields.items():
                if key not in value or get_origin(field.annotation) is not Literal:
                    continue
                args = get_args(field.annotation)
                if all(type(a) is bool for a in args) and type(value[key]) is not bool:
                    raise ValueError('Boolean must be JSON true/false')
                if all(type(a) is int for a in args) and type(value[key]) is not int:
                    raise ValueError('Integer must be JSON integer')
        return value


class Permissions(Strict):
    push_review_branch: Literal[False]
    push_main: Literal[True]
    merge_main: Literal[False]
    deploy: Literal[False]
    live_provider_calls: Literal[False]
    access_real_user_data: Literal[False]


class Receipt(Strict):
    id: PacketId
    filename: Text
    bytes: Annotated[int, Field(gt=0)]
    sha256: Hash
    raw_claimed_status: Text
    external_receipt: Literal['RECEIVED_AND_EXTRACTED_IN_CHATGPT']
    local_receipt: Literal['MANIFEST_ONLY_NOT_LOCALLY_RECEIVED']
    local_bytes_verified: Literal[False]
    external_review_status: Literal['SCOPE_AND_CONSISTENCY_SCREENED']
    full_evidence_review: Literal['NOT_COMPLETED']
    rights_status: Literal['NOT_CLEARED_AS_A_WHOLE']
    content_status: Literal['NOT_APPROVED']
    finding_ids: list[FindingId]


Access = Literal['PUBLISHER_ABSTRACT_AND_POSITION_STATEMENTS', 'OFFICIAL_PDF_TARGETED_TEXT_AND_PAGE_IMAGES',
                 'PUBLISHER_FULL_TEXT_TARGETED_SECTIONS', 'INDEXED_PRIMARY_ABSTRACT_METADATA',
                 'PUBLISHER_AND_AUTHOR_REPOSITORY_ABSTRACT', 'PUBLISHER_INDEXED_ABSTRACT',
                 'PUBLISHER_ABSTRACT_METHODS_RESULTS', 'RIGHTSHOLDER_PUBLIC_STATEMENT',
                 'RIGHTSHOLDER_CURRENT_POLICY_PAGE', 'OFFICIAL_GUIDANCE_PAGE', 'OFFICIAL_STATUTORY_EXCERPT',
                 'OFFICIAL_PDF_TARGETED_TEXT_AND_PAGE_IMAGE', 'OFFICIAL_CURRENT_DOCUMENTATION',
                 'OFFICIAL_CURRENT_POLICY', 'OFFICIAL_LANDING_METADATA_ONLY']


class Source(Strict):
    id: SourceId
    external_id: Text
    record_sha256: Hash
    title: Text
    url: Annotated[str, StringConstraints(pattern=r'^https://\S+$')]
    checked_on: Text
    access_extent: Access
    checked_locator: Text
    observed: Text
    limits: Text
    verification_origin: Literal['EXTERNAL_REVIEW_NOT_RECHECKED_LOCALLY']
    local_source_bytes_sha256: None


class Claim(Strict):
    id: Annotated[str, StringConstraints(pattern=r'^claim:RG-(?:0[1-9]|1[0-9]|2[0-7])$')]
    finding_id: FindingId
    packet_ids: Annotated[list[PacketId], Field(min_length=1)]
    raw_claimed_status: Text
    raw_position: Text
    source_ids: list[SourceId]
    source_bindings: dict[SourceId, Hash]
    external_review_status: Text
    actual_local_verification: Literal['MAPPING_ONLY_NOT_PRIMARY_RECHECK']
    evidence_status: Literal['SCOPED_EXTERNAL_CHECK', 'NEEDS_VERIFICATION']
    applicability: Literal['NO_AUTOMATIC_TRANSFER_TO_APP']
    rights_status: Literal['NOT_REVIEWED_FOR_EXACT_USE']
    content_status: Literal['NOT_REVIEWED']
    scientific_validation: Literal[False]


class Finding(Strict):
    id: FindingId
    title: Text
    packets: Annotated[list[PacketId], Field(min_length=1)]
    raw_locators: Annotated[list[Text], Field(min_length=1)]
    basis: Text
    raw_position: Text
    review_finding: Text
    required_action: Text
    blocks: Annotated[list[Text], Field(min_length=1)]
    primary_source_ids: list[Text]
    status: Literal['OPEN_FOR_CANONICAL_INTEGRATION']


class Correction(Strict):
    id: FindingId
    supplied_finding: Finding
    finding_sha256: Hash
    integration_status: Literal['INTEGRATED_AS_DERIVED_DECISION']
    content_resolution: Literal['OPEN_DEPENDENT_GATE']
    derived_decision: Text
    claim_id: Text


class Rights(Strict):
    status: Literal['NOT_REVIEWED', 'POLICY_CHECKED', 'RIGHTS_CLEARED']
    basis: Literal['PUBLIC_LICENSE', 'PUBLIC_PERMISSION', 'INDIVIDUAL_GRANT', 'OWN_ORIGINAL'] | None
    locator: Text | None
    material_hash: Hash | None
    language: Text | None
    use_scope: Text | None
    reviewed_by: Text | None
    reviewed_on: Text | None


class Approval(Strict):
    module_id: Text
    version: Text
    content_hash: Hash
    claim_bindings: dict[ClaimId, Hash]
    source_bindings: dict[SourceId, Hash]
    reviewer: Text
    reviewer_role: Literal['QUALIFIED_CLINICAL_REVIEWER', 'CONTENT_REVIEWER']
    reviewed_on: Text
    scope: Text
    rights_hash: Hash
    technical_sha: Sha


class TechnicalCheck(Strict):
    command: Text
    exit_code: Literal[0]
    environment: Text


class TechnicalReceipt(Strict):
    implementation_sha: Sha
    checks: Annotated[list[TechnicalCheck], Field(min_length=1)]
    evidence_locator: Text


class Module(Strict):
    id: Text
    version: Text
    proposed_disposition: Text
    research_packets: Annotated[list[PacketId], Field(min_length=1)]
    boundary: Text
    draft_status: Literal['DRAFT_NOT_RUNTIME']
    clinical_sensitive: bool
    required_reviewer_role: Literal['QUALIFIED_CLINICAL_REVIEWER', 'CONTENT_REVIEWER']
    exact_content_hash: Hash | None
    intended_scope: Text
    claim_ids: list[Text]
    finding_ids: list[FindingId]
    missing_gates: Annotated[list[Text], Field(min_length=1)]
    smallest_next_step: Text
    allowed_actions: Annotated[list[Text], Field(min_length=1)]
    forbidden_actions: Annotated[list[Text], Field(min_length=1)]
    rollback: Text
    rights: Rights
    evidence_status: Literal['NOT_REVIEWED', 'EVIDENCE_REVIEWED']
    content_status: Literal['NOT_REVIEWED', 'CONTENT_REVIEWED']
    technical_status: Literal['NOT_RUN', 'TECHNICALLY_TESTED']
    technical_sha: Sha | None
    technical_receipt: TechnicalReceipt | None
    approval: Approval | None
    activation_status: Literal['OFF']
    runtime_activation_authorized_by_this_pack: Literal[False]
    qualified_clinical_review_record: None


class M6Review(Strict):
    implementation_sha: Literal[C6]
    evidence_sha: Literal[BASE]
    external_verdict: Literal['ACCEPT_ENGINEERING_AND_BOUNDED_EARLY_HARDWARE']
    tested_hardware_build: Literal['0.6.0-debug']
    final_build: Literal['0.6.1-debug']
    final_build_hardware: Literal['NOT_RUN']
    note_id: Literal['M6-N01']
    note: Text


class Registry(Strict):
    schema_version: Literal[1]
    registry_version: Literal['0.1.0']
    status: Literal['PREPARATION_ONLY_NOT_RUNTIME']
    base_sha: Literal[BASE]
    review_pack_sha256: Hash
    local_review_pack: Literal['MANIFEST_VERIFIED_SAFE_EXTRACT']
    permissions: Permissions
    receipts: Annotated[list[Receipt], Field(min_length=16, max_length=16)]
    sources: Annotated[list[Source], Field(min_length=16, max_length=16)]
    claims: Annotated[list[Claim], Field(min_length=27, max_length=27)]
    corrections: Annotated[list[Correction], Field(min_length=27, max_length=27)]
    modules: Annotated[list[Module], Field(min_length=16, max_length=16)]
    m6_review: M6Review
    active_clinical_protocols: Literal[0]


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode()).hexdigest()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def read_json(path: Path):
    if path.is_symlink() or any(p.is_symlink() for p in path.parents):
        raise ValueError('Symlink input refused')
    if path.stat().st_size > 2_000_000:
        raise ValueError('Oversized JSON input')
    return json.loads(path.read_text(), object_pairs_hook=unique_pairs)


def check_date(value: str) -> bool:
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def approval_gates(module: Module, sources: dict[str, Source], claims: dict[str, Claim]) -> list[str]:
    """Assess a shadow candidate only; even a complete receipt cannot activate anything."""
    gates = []
    if module.exact_content_hash is None:
        gates.append('MISSING_CONTENT_HASH')
    if module.evidence_status != 'EVIDENCE_REVIEWED':
        gates.append('EVIDENCE_REVIEW_REQUIRED')
    if module.content_status != 'CONTENT_REVIEWED':
        gates.append('CONTENT_REVIEW_REQUIRED')
    rights = module.rights
    if (rights.status != 'RIGHTS_CLEARED' or any(getattr(rights, k) is None for k in
            ('basis', 'locator', 'material_hash', 'language', 'use_scope', 'reviewed_by', 'reviewed_on'))):
        gates.append('EXACT_RIGHTS_REQUIRED')
    elif (rights.material_hash != module.exact_content_hash or rights.use_scope != module.intended_scope
          or not check_date(rights.reviewed_on)):
        gates.append('INCOMPATIBLE_RIGHTS')
    if (module.technical_status != 'TECHNICALLY_TESTED' or module.technical_sha is None
            or module.technical_receipt is None or module.technical_receipt.implementation_sha != module.technical_sha):
        gates.append('EXACT_TECHNICAL_EVIDENCE_REQUIRED')
    if module.clinical_sensitive and module.required_reviewer_role != 'QUALIFIED_CLINICAL_REVIEWER':
        gates.append('QUALIFIED_REVIEWER_REQUIRED')
    source_bindings = {}
    claim_bindings = {}
    for cid in module.claim_ids:
        claim = claims.get(cid)
        if claim is None:
            gates.append('MISSING_CLAIM')
            continue
        claim_bindings[cid] = digest(claim.model_dump())
        # Scoped external checks do not approve an arbitrary future AI adaptation.
        gates.append('APPLICABILITY_REVIEW_REQUIRED')
        if claim.evidence_status != 'SCOPED_EXTERNAL_CHECK':
            gates.append('UNRESOLVED_CLAIM')
        for sid in claim.source_ids:
            source = sources.get(sid)
            if source is None:
                gates.append('MISSING_SOURCE')
            elif claim.source_bindings.get(sid) != source.record_sha256:
                gates.append('SOURCE_HASH_DRIFT')
            else:
                source_bindings[sid] = source.record_sha256
    a = module.approval
    if a is None:
        gates.append('ACCOUNTABLE_APPROVAL_REQUIRED')
    else:
        expected = (module.id, module.version, module.exact_content_hash, module.intended_scope,
                    module.required_reviewer_role, digest(rights.model_dump()), module.technical_sha)
        actual = (a.module_id, a.version, a.content_hash, a.scope, a.reviewer_role,
                  a.rights_hash, a.technical_sha)
        if expected != actual or not check_date(a.reviewed_on):
            gates.append('STALE_OR_INCOMPATIBLE_APPROVAL')
        if a.claim_bindings != claim_bindings or a.source_bindings != source_bindings:
            gates.append('STALE_DEPENDENCY_APPROVAL')
    if module.proposed_disposition in {'EXCLUDED_V1', 'DEFERRED'}:
        gates.append(module.proposed_disposition)
    return sorted(set(gates))


class Attestation(Strict):
    """Typed mechanical metadata, not a medical result or instruction parser."""
    raw_claimed_status: Text = 'UNVERIFIED'
    untrusted_text: str = ''
    independent_check: bool = False
    search_execution: Literal['SIMULATED', 'EXECUTED', 'UNVERIFIED'] = 'UNVERIFIED'
    access: Literal['NONE', 'ABSTRACT_ONLY', 'TARGETED_FULLTEXT'] = 'NONE'
    citation_candidates: list[Text] = []
    doi: Text | None = None
    adjacent_reference: Text | None = None
    delivery: Literal['GUIDED', 'AUTONOMOUS_AI', 'UNKNOWN'] = 'UNKNOWN'
    requested_delivery: Literal['GUIDED', 'AUTONOMOUS_AI', 'UNKNOWN'] = 'UNKNOWN'
    user_confirmed: bool = False
    data_status: Literal['PRESENT', 'UNKNOWN', 'NO_RECORDS', 'PERMISSION_DENIED'] = 'UNKNOWN'
    observed_value: float | None = None
    benchmark_status: Literal['NOT_RUN', 'PASS'] = 'NOT_RUN'
    benchmark_sha: Sha | None = None
    checklist_checked: bool = False
    checklist_sha: Sha | None = None
    requested_health_types: list[Text] = []
    hardware_build: Text | None = None
    requested_hardware_build: Text | None = None
    residual_risk_claim: Text | None = None
    narrative: Literal['FICTION', 'REAL_LIFE'] = 'FICTION'
    explicit_real_life_request: bool = False
    exercise_complete: bool = False
    cosmetics_enabled: bool = False
    permissions: Permissions = Field(default_factory=lambda: Permissions(**EXPECTED_PERMISSIONS))


def assess_attestation(a: Attestation) -> dict:
    """Produces evidence labels only. No reads, shell, egress, or permission mutation."""
    health = {'Sleep', 'Steps', 'Exercise'}
    return {
        'raw_claimed_status': a.raw_claimed_status,
        'evidence': 'SCOPED_CHECK' if a.independent_check else 'UNVERIFIED',
        'search_verified': a.search_execution == 'EXECUTED' and a.independent_check,
        'fulltext_verified': a.access == 'TARGETED_FULLTEXT' and a.independent_check,
        'access': a.access,
        'citation_resolved': len(set(a.citation_candidates)) == 1,
        'identifier_needs_mapping': a.adjacent_reference is not None,
        'doi_preserved': a.doi,
        'applicability_gap': a.delivery != a.requested_delivery,
        'user_acknowledgement': a.user_confirmed,
        'causality_validated': False,
        'available_value': a.observed_value if a.data_status == 'PRESENT' else None,
        'engineering_check_verified': a.checklist_checked and a.checklist_sha is not None,
        'benchmark_verified': a.benchmark_status == 'PASS' and a.benchmark_sha is not None,
        'excluded_health_types': sorted(set(a.requested_health_types) - health),
        'hardware_binding_valid': a.hardware_build is not None and a.hardware_build == a.requested_hardware_build,
        'absolute_assurance_accepted': False,
        'author_diagnosis': False,
        'current_request_requires_separate_review': a.explicit_real_life_request,
        'neutral_functions_unchanged': True,
        'penalty': False,
        'permissions': a.permissions.model_dump(),
        'activation': 'OFF',
    }


def validate_registry(data: dict, external: dict | None = None) -> dict:
    errors = []
    unresolved = []
    modules = data.get('modules') if isinstance(data, dict) else None
    active_count = (sum(m.get('activation_status') == 'ACTIVE' for m in modules if isinstance(m, dict))
                    if isinstance(modules, list) else None)
    try:
        r = Registry.model_validate(data)
    except ValidationError as exc:
        # Do not echo potentially sensitive/untrusted field values.
        errors = ['.'.join(map(str, e['loc'])) + ': ' + e['type'] for e in exc.errors()]
        return {'structural_status': 'FAIL', 'errors': errors, 'unresolved': [],
                'active_clinical_protocols': active_count, 'activation_status': 'FORBIDDEN'}
    collections = [r.receipts, r.sources, r.claims, r.corrections, r.modules]
    for rows in collections:
        if len({x.id for x in rows}) != len(rows):
            errors.append('Duplicate registry IDs')
    receipts = {x.id: x for x in r.receipts}
    sources = {x.id: x for x in r.sources}
    claims = {x.id: x for x in r.claims}
    corrections = {x.id: x for x in r.corrections}
    if set(receipts) != {f'R{i:02}' for i in range(1, 17)}:
        errors.append('Incomplete packet inventory')
    if set(sources) != {f'gate:S{i:02}' for i in range(1, 17)}:
        errors.append('Incomplete source inventory')
    if set(corrections) != {f'RG-{i:02}' for i in range(1, 28)}:
        errors.append('Incomplete finding inventory')
    if r.review_pack_sha256 != 'feeec2a0d830eaef3fb5d4a80d2b6b88168a534317b53885db4e20ea5554e6c4':
        errors.append('Archive identity mismatch')
    for source in r.sources:
        original = {k: v for k, v in source.model_dump().items()
                    if k not in {'id', 'external_id', 'record_sha256', 'verification_origin'}}
        original['id'] = source.external_id
        if source.record_sha256 != digest(original):
            errors.append('Source record hash mismatch: ' + source.id)
        if not check_date(source.checked_on):
            errors.append('Invalid source date: ' + source.id)
        if source.id != 'gate:' + source.external_id:
            errors.append('Source namespace mismatch: ' + source.id)
    for receipt in r.receipts:
        if any(fid not in corrections for fid in receipt.finding_ids):
            errors.append('Unknown receipt finding: ' + receipt.id)
    for c in r.corrections:
        f = c.supplied_finding
        if c.id != f.id or c.finding_sha256 != digest(f.model_dump()):
            errors.append('Finding content/hash mismatch: ' + c.id)
        if c.derived_decision != f.required_action:
            errors.append('Derived decision mismatch: ' + c.id)
        if c.claim_id != 'claim:' + c.id or c.claim_id not in claims:
            errors.append('Missing finding claim: ' + c.id)
        if not set(f.packets) <= set(receipts) or not {'gate:' + s for s in f.primary_source_ids} <= set(sources):
            errors.append('Unresolved finding references: ' + c.id)
        unresolved.append({'id': c.id, 'status': c.content_resolution, 'blocks': f.blocks})
    for c in r.claims:
        finding = corrections.get(c.finding_id)
        if finding is None:
            errors.append('Unknown claim finding: ' + c.id)
            continue
        f = finding.supplied_finding
        expected_sources = ['gate:' + sid for sid in f.primary_source_ids]
        if (c.id != 'claim:' + f.id or c.packet_ids != f.packets or c.raw_position != f.raw_position
                or c.source_ids != expected_sources or c.external_review_status != f.basis):
            errors.append('Claim mapping mismatch: ' + c.id)
        if set(c.source_bindings) != set(c.source_ids):
            errors.append('Missing/extra source bindings: ' + c.id)
        for sid in c.source_ids:
            if sid not in sources or c.source_bindings.get(sid) != sources[sid].record_sha256:
                errors.append('Source hash drift or missing source: ' + c.id)
        expected_status = 'SCOPED_EXTERNAL_CHECK' if c.source_ids else 'NEEDS_VERIFICATION'
        if c.evidence_status != expected_status:
            errors.append('Unsupported evidence promotion: ' + c.id)
    for m in r.modules:
        if not set(m.research_packets) <= set(receipts):
            errors.append('Unknown module packet: ' + m.id)
        expected_findings = sorted(c.id for c in r.corrections if set(c.supplied_finding.packets) & set(m.research_packets))
        if m.finding_ids != expected_findings or m.claim_ids != ['claim:' + f for f in expected_findings]:
            errors.append('Incomplete module dependencies: ' + m.id)
        gates = approval_gates(m, sources, claims)
        if m.rights.status == 'RIGHTS_CLEARED' and any(x in gates for x in ('EXACT_RIGHTS_REQUIRED', 'INCOMPATIBLE_RIGHTS')):
            errors.append('Incomplete exact rights promotion: ' + m.id)
        expected_role = 'QUALIFIED_CLINICAL_REVIEWER' if m.id in CLINICAL_MODULES else 'CONTENT_REVIEWER'
        if (m.clinical_sensitive != (m.id in CLINICAL_MODULES) or m.required_reviewer_role != expected_role
                or m.version != '0.1.0-draft' or m.intended_scope != m.boundary):
            errors.append('Draft scope/reviewer mismatch: ' + m.id)
        if not set(gates) <= set(m.missing_gates):
            errors.append('Missing gates omitted from draft: ' + m.id)
        if (set(m.allowed_actions) != {'METADATA_REVIEW', 'SYNTHETIC_PREPARATION_TESTS'}
                or set(m.forbidden_actions) != {'CLINICAL_ACTIVATION', 'PRIVATE_DATA_ACCESS', 'UNSCOPED_PROVIDER_CALLS'}):
            errors.append('Draft permissions mismatch: ' + m.id)
        unresolved.append({'module': m.id, 'computed_missing_gates': gates,
                           'declared_missing_gates': m.missing_gates, 'next_step': m.smallest_next_step})
        if m.approval is not None and gates:
            errors.append('Invalid/stale approval receipt: ' + m.id)
        if m.evidence_status != 'NOT_REVIEWED' or m.content_status != 'NOT_REVIEWED' or m.technical_status != 'NOT_RUN':
            errors.append('Unsupported module review promotion: ' + m.id)
    if external is not None:
        inputs = {x['id']: x for x in external['INPUT_MANIFEST.json']['inputs']}
        packets = {x['id']: x for x in external['PACKET_DISPOSITIONS.json']['packets']}
        fs = {x['id']: x for x in external['REVIEW_FINDINGS.json']['findings']}
        ss = {'gate:' + x['id']: x for x in external['PRIMARY_SOURCE_CHECKS.json']['sources']}
        ms = {x['id']: x for x in external['MODULE_ADMISSION_DRAFT.json']['modules']}
        if set(ms) != {m.id for m in r.modules}:
            errors.append('Draft module inventory drift')
        for receipt in r.receipts:
            i, p = inputs.get(receipt.id, {}), packets.get(receipt.id, {})
            if (receipt.sha256 != i.get('sha256') or receipt.sha256 != p.get('input_sha256')
                    or receipt.filename != i.get('filename') or receipt.bytes != i.get('bytes')
                    or receipt.raw_claimed_status != i.get('raw_status') or receipt.finding_ids != p.get('finding_ids')):
                errors.append('External intake mismatch: ' + receipt.id)
        for c in r.corrections:
            if c.supplied_finding.model_dump() != fs.get(c.id):
                errors.append('Supplied finding drift: ' + c.id)
        for s in r.sources:
            original = ss.get(s.id, {})
            if s.record_sha256 != digest(original) or any(getattr(s, k) != v for k, v in original.items() if k != 'id'):
                errors.append('External source ledger drift: ' + s.id)
        for m in r.modules:
            original = ms.get(m.id, {})
            for k in ('proposed_disposition', 'research_packets', 'boundary', 'runtime_activation_authorized_by_this_pack',
                      'qualified_clinical_review_record', 'exact_content_hash'):
                if getattr(m, k) != original.get(k):
                    errors.append('External module draft drift: ' + m.id)
    return {'structural_status': 'FAIL' if errors else 'PASS', 'errors': sorted(set(errors)),
            'unresolved': unresolved, 'findings_preserved': len(r.corrections),
            'findings_content_closed': 0, 'packets_received_externally': len(r.receipts),
            'raw_locally_received': 0, 'active_clinical_protocols': active_count, 'activation_status': 'OFF'}


def validate_directory(root: Path) -> dict:
    errors = []
    external = {}
    try:
        manifest_path = root / 'external/PACK_MANIFEST.json'
        manifest = read_json(manifest_path)
        if hashlib.sha256(manifest_path.read_bytes()).hexdigest() != PACK_MANIFEST_SHA256:
            errors.append('Review pack manifest identity mismatch')
        files = {f['path']: f for f in manifest['files']}
        if len(files) != 11 or len(manifest['files']) != 11:
            errors.append('Review pack manifest inventory mismatch')
        for name in EXTERNAL_FILES:
            path = root / 'external' / name
            if path.is_symlink():
                raise ValueError('Symlink input refused')
            # Check parent containment before reading JSONL bytes too.
            if not path.resolve().is_relative_to(root.resolve()) or any(p.is_symlink() for p in path.parents):
                raise ValueError('Unsafe external input path')
            if path.stat().st_size > 2_000_000:
                raise ValueError('Oversized external input')
            blob = path.read_bytes()
            entry = files[name]
            if len(blob) != entry['bytes'] or hashlib.sha256(blob).hexdigest() != entry['sha256']:
                errors.append('External review payload hash mismatch: ' + name)
            external[name] = ([json.loads(line, object_pairs_hook=unique_pairs) for line in blob.decode().splitlines()]
                              if name.endswith('.jsonl') else read_json(path))
        cases = external['ADMISSION_EVAL_CANDIDATES.jsonl']
        if {c['id'] for c in cases} != {f'G{i:02}' for i in range(1, 25)} or len(cases) != 24:
            errors.append('Supplied scenario inventory mismatch')
        result = validate_registry(read_json(root / 'registry.json'), external)
        for name, schema in schemas().items():
            if read_json(root / 'schemas' / name) != schema:
                errors.append('Schema/tooling drift: ' + name)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return {'structural_status': 'FAIL', 'errors': ['Input/schema failure: ' + type(exc).__name__],
                'unresolved': [], 'active_clinical_protocols': None, 'activation_status': 'FORBIDDEN'}
    result['errors'].extend(errors)
    if result['errors']:
        result['structural_status'] = 'FAIL'
    return result


def key_closed(value):
    if isinstance(value, dict):
        if 'patternProperties' in value:
            value['additionalProperties'] = False
        for child in value.values():
            key_closed(child)
    elif isinstance(value, list):
        for child in value:
            key_closed(child)
    return value


def schemas() -> dict:
    return {name + '.schema.json': key_closed(cls.model_json_schema()) for name, cls in
            [('registry', Registry), ('receipt', Receipt), ('source', Source), ('claim', Claim),
             ('correction', Correction), ('module', Module), ('approval', Approval), ('attestation', Attestation)]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1] / 'research/admission')
    args = p.parse_args()
    result = validate_directory(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(result['structural_status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
