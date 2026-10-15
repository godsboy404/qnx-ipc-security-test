"""Validate preserved native smoke records; does not certify global QNX security."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
runs = sorted((root/'evidence/native-runs').glob('*/manifest.json'))
if not runs:
    raise SystemExit('No completed native runs')
for path in runs:
    manifest = json.loads(path.read_text(encoding='utf-8-sig'))
    assert manifest['backend'] == 'qnx-native'
    assert manifest['run_id'] == path.parent.name
    for name, digest in manifest['hashes'].items():
        assert hashlib.sha256((path.parent/name).read_bytes()).hexdigest() == digest, name
    assert (path.parent/'hello.txt').read_text(encoding='utf-8-sig').strip() == 'Hello QNX: course toolchain smoke test'
    for name, expected_count, payload in (('normal.jsonl',100,4),('empty.jsonl',1,0),('restarted.jsonl',100,4)):
        records = [json.loads(line) for line in (path.parent/name).read_text(encoding='utf-8-sig').splitlines()]
        assert len(records) == expected_count
        assert len({r['case_id'] for r in records}) == expected_count
        for row in records:
            assert row['status'] == 'PASS' and row['return_code'] == 0
            assert row['backend'] == 'qnx-native'
            assert row['criterion_id'] == 'IPC-01'
            assert row['payload_bytes'] == payload and row['dcmd_bytes'] == 16 + payload
            assert row['elapsed_ns'] >= 0
    print(path.parent.name, '201 legal native requests and file integrity verified')
print('Scope: local runner, legal devctl ECHO and owned server restart; no fault-isolation or peer signoff claim')
