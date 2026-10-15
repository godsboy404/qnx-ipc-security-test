"""Check run identity and file integrity, never certify execution authenticity."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
runs = sorted((root/'evidence/runs').glob('*'))
if not runs:
    raise SystemExit('No runs found; generate demo first')
for folder in runs:
    manifest = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['run_id'] == folder.name
    assert manifest['backend'] == 'simulation'
    for name, digest in manifest['evidence_hashes'].items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == digest, name
    rows = [json.loads(line) for line in (folder/'results.jsonl').read_text(encoding='utf-8').splitlines()]
    cases = [json.loads(line) for line in (folder/'cases.jsonl').read_text(encoding='utf-8').splitlines()]
    summary = json.loads((folder/'summary.json').read_text(encoding='utf-8'))
    assert summary['total'] == len(rows) == len(cases)
    assert [r['case_id'] for r in rows] == [c['case_id'] for c in cases]
    for row in rows:
        assert row['run_id'] == manifest['run_id']
        assert row['source_version'] == manifest['source_version']
        assert row['backend'] == 'simulation'
        assert row['isolation'] == 'INCONCLUSIVE'
        if row['decision'] != 'ALLOW':
            assert row['target_outcome'] == 'NOT_SENT'
    assert summary['qnx_crash_count'] is None
    assert summary['isolation_success_rate'] is None
    print(manifest['scenario'], len(rows), 'integrity and linkage checked')
print('Checks verify stored consistency, not independent execution or QNX outcomes')
