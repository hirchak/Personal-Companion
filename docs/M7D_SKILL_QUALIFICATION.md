# M7D specialist qualification packages — CANDIDATE / OFF

Five metadata-only files in `skills/qualification/` are mechanically ready for independent admission
review. This is not content readiness, evidence closure, clinical qualification or permission to activate.
`PYTHONPATH=. .venv/bin/python scripts/qualify_m7d_skills.py --check` checks exact canonical dependencies.
The runtime loader reads only four original neutral skills from `skills/conversation/`; it denies every
specialist ID and never loads qualification metadata into prompts.

| Candidate | Exact canonical modules | Exclusions |
|---|---|---|
| cbt_reflection | thought_record | Diagnosis, forced disputation, irrational labels |
| worry_rumination | worry_rumination | Reassurance loops, unreviewed worry postponement |
| sleep_review | sleep_education, clinical_sleep_window, expanded_health_access | CBT-I, SRT/compression, personalized window, diagnosis, Health access |
| nightmare_review | dream_irt | IRT content, exposure, trauma processing, PTSD/symbolic certainty |
| grounding | grounding_relaxation | Improvised dosing/steps, bypass of exact M7A admission |

Each package preserves module ID/version, packet/claim/finding IDs, unresolved gates, reviewer role,
rights/evidence/content status, null clinical review/content hash, input/stop contracts, proposed output
schema and synthetic denial cases. Registry SHA binds the package. RAW16 are external manifest only,
locally received0; do not interpret metadata as locally available research. Findings27 OPEN, clinical0.
Future practice flow remains candidate -> UI -> explicit click -> exact M7A admission -> package.
No therapeutic scripts, practice steps or new health permissions are delivered in M7D.
