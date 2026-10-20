"""SEC-03/OBS-01/ISO-01: local claim checks, without an API or human signoff."""
import argparse
import json
from pathlib import Path
from .registered_review import build_packet, digest, read, REGISTRY, TRUSTED_ROOT
from .native import read_rows
from .semantic_review import canonical


def assess(summary, cases, rows):
    """Independent row-level predicates; input archives must first pass preflight.

    These are bounded project checks, not teacher grades or model ground truth.
    The existing native reanalysis checks oracle labels, wire content and receiver
    order/times. These predicates expose the narrower claim in reviewable form.
    """
    indexed = {row['case_id']: row for row in rows}
    invalid = [case for case in cases if case['oracle_label'] != 'valid']
    checks = {
        'case_ids_unique_and_aligned': len(indexed) == len(rows) == len(cases)
            and [r['case_id'] for r in rows] == [c['case_id'] for c in cases],
        'defense_mode': summary.get('mode') == 'defense',
        'nonempty_invalid_sample': bool(invalid),
        'all_invalid_blocked_without_send': all(
            case['case_id'] in indexed and indexed[case['case_id']].get('decision') == 'BLOCK'
            and indexed[case['case_id']].get('forwarded') is False
            and indexed[case['case_id']].get('outcome') == 'NOT_SENT' for case in invalid),
        'invalid_counts_reconcile': len(invalid) == summary.get('invalid_cases') == summary.get('blocked_count'),
        'forwarded_counts_reconcile': sum(r.get('forwarded') is True for r in rows)
            == summary.get('forwarded_count') == summary.get('target_received_count'),
    }
    return checks


def build_report(release_id='defense-20261017', root=None):
    root = Path(root) if root is not None else TRUSTED_ROOT
    # All three packets independently recheck pinned contract, manifest, hashes
    # and native raw-log semantics. No summary-only shortcut is accepted.
    packets = {key: build_packet(release_id, key, root) for key in ('SEC-03', 'OBS-01', 'ISO-01')}
    registry = read(root / REGISTRY)
    folder = root / registry['releases'][release_id]['path']
    summary = read(folder / 'summary.json')
    checks = assess(summary, read_rows(folder / 'cases.jsonl'), read_rows(folder / 'fuzz-results.jsonl'))
    from hashlib import sha256
    return dict(schema_version=1, release_id=release_id, authority='project_draft',
        verification='local_archive_reanalysis', independent_reproduction=False,
        human_signoff='pending', model_ground_truth='independent_review_pending',
        registry_sha256=digest(root / REGISTRY),
        checker_hashes={name: digest(Path(__file__).parent / name) for name in
            ('claim_audit.py', 'registered_review.py', 'native.py')},
        source_version=packets['OBS-01']['source_version'],
        packet_sha256={key: sha256(canonical(value)).hexdigest() for key, value in packets.items()},
        input_hashes={name: digest(folder / name) for name in
            ('manifest.json', 'cases.jsonl', 'fuzz-results.jsonl', 'target-audit.jsonl', 'summary.json')},
        criteria={
            'SEC-03': dict(local_result='PASS' if all(checks.values()) else 'FAIL', checks=checks,
                observed=dict(invalid_cases=summary['invalid_cases'], blocked=summary['blocked_count'],
                    forwarded=summary['forwarded_count'], received=summary['target_received_count']),
                boundary='Only the registered historical sample and application gateway; no universal or kernel enforcement claim.'),
            'OBS-01': dict(local_result='PASS', checks=dict(pinned_contract_matches=True,
                pinned_manifest_matches=True, source_mapping_identity_matches=True,
                evidence_hashes_match=True, raw_log_reanalysis_matches_summary=True),
                boundary='Local consistency only; not archive authenticity, current-source equivalence or independent QNX reproduction.'),
            'ISO-01': dict(local_result='INSUFFICIENT_EVIDENCE',
                checks=dict(complete_system_service_probes=False),
                boundary='Process liveness and peer heartbeats cannot establish full QNX system isolation.')})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', default='defense-20261017')
    parser.add_argument('--out', required=True, help='New report file; existing files are never overwritten')
    args = parser.parse_args()
    report = build_report(args.release)
    with Path(args.out).open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print('Local checks saved; human signoff pending; no model call.')


if __name__ == '__main__':
    main()
