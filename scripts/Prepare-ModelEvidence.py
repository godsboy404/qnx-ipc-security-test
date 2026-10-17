"""Prepare bounded derived excerpts only after native archive revalidation (OBS-01)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ipcsec.native import verify_archived
from ipcsec.semantic_review import identity, canonical
from ipcsec.model_calibration import prepare, sha

root = Path(__file__).resolve().parents[1]
run = root/'evidence/native-fuzz-runs/20261017T122327Z-0b2f7718'
summary, manifest = verify_archived(run)
source = identity(manifest['source_hashes'])
verification = dict(run_id=manifest['run_id'], manifest_sha256=sha(run/'manifest.json'),
    evidence_member_count=len(manifest['evidence_hashes']),
    evidence_hash_mapping_sha256=identity(manifest['evidence_hashes']),
    local_verifier='ipcsec.native.verify_archived',
    local_verifier_sha256=sha(root/'ipcsec/native.py'),
    local_reanalysis_matches_archived_summary=True,
    note='Local hash and causal checks only; not independent peer reproduction or cryptographic authenticity.')
evidence = [dict(id='archived-native-summary', source_version=source, level='qnx_native',
                 excerpt=canonical(summary).decode('utf-8')),
            dict(id='local-native-reverification', source_version=source, level='qnx_native',
                 excerpt=canonical(verification).decode('utf-8'))]
scopes = {
    'REAL-SEC-03': ('SEC-03', 'Only this archived defense run: verify the reported 94 malformed cases were blocked without forwarding, based on local reanalysis that reconciles request and independent receiver logs. No claim of all possible inputs, kernel enforcement, or current source equivalence.'),
    'REAL-OBS-01': ('OBS-01', 'Only local archived evidence consistency: source identity is the SHA256 of the archived source_hashes mapping; original evidence hashes were rechecked and raw-log reanalysis matched summary. Assess this limited consistency claim, not authenticity, independent reproduction or current-source equivalence.'),
    'REAL-ISO-01': ('ISO-01', 'Assess full QNX system isolation from the supplied archived native run. Process liveness and peer heartbeats alone cannot establish full system-service health or crash isolation.'),
}
cases = {name: dict(criterion_id=criterion, scope=scope, source_version=source,
    approved_na=False, complete_system_probes=False, evidence=evidence)
    for name, (criterion, scope) in scopes.items()}
answers = {name: dict(expected='INSUFFICIENT_EVIDENCE' if name=='REAL-ISO-01' else 'PASS',
    oracle_author='AI-authored bounded interpretation of locally reverified native evidence; human review pending')
    for name in cases}
print(prepare(root/'evidence/model-review-runs/20261017-deepseek-native-review-v2', cases, answers))
