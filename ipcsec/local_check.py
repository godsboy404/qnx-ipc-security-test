"""REL-01/OBS-01: bounded author-side host checks, never peer reproduction."""
import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED_DIRS = ('runs', 'change-runs', 'review-runs')
STEPS = (
    ('tests', ('-m', 'unittest', 'discover', '-s', 'tests', '-v')),
    ('simulation-demo', ('-m', 'ipcsec', 'demo')),
    ('deterministic-calibration', ('-m', 'ipcsec', 'calibrate')),
    ('single-case-replay', ('-m', 'ipcsec', 'replay', '--case-id', 'CASE-0001')),
    ('change-rehearsal', ('-m', 'ipcsec.change_rehearsal', 'run')),
    ('rate-accounting-regression', ('scripts/Reproduce-RateAccounting.py',)),
    ('local-claims', ('-m', 'ipcsec.claim_audit', '--out', '{claim_report}')),
    ('historical-evidence-audit', ('-m', 'ipcsec.handoff', 'audit')),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def source_hashes(root):
    # Exclude generated evidence, build, caches and calibration output.
    files = [root / name for name in ('AGENTS.md', 'pyproject.toml')]
    for name in ('ipcsec', 'scripts', 'configs', 'native', 'tests'):
        files.extend(p for p in (root / name).rglob('*') if p.is_file()
            and p.suffix.lower() in ('.py', '.ps1', '.json', '.c', '.h', '.sh')
            and '__pycache__' not in p.parts)
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(files)}


def run(root=None):
    root = Path(root).resolve() if root is not None else ROOT
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    folder = root / 'evidence/local-check-runs' / run_id
    folder.mkdir(parents=True, exist_ok=False)
    before = source_hashes(root)
    save(folder / 'source-files.json', before)
    previous = {p for kind in GENERATED_DIRS for p in (root / 'evidence' / kind).glob('*/manifest.json')}
    steps = []
    for name, arguments in STEPS:
        args = [str(folder / 'claim-report.json') if arg == '{claim_report}' else arg for arg in arguments]
        command = [sys.executable, *args]
        started = datetime.now(timezone.utc).isoformat()
        clock = time.perf_counter()
        timed_out = False
        with (folder / (name + '.log')).open('wb') as output:
            try:
                result = subprocess.run(command, cwd=root, stdin=subprocess.DEVNULL,
                    stdout=output, stderr=subprocess.STDOUT, timeout=60, shell=False)
                code = result.returncode
            except subprocess.TimeoutExpired:
                timed_out, code = True, None
            except OSError as exc:
                # Record the class, not environment contents or credential values.
                output.write(('Launch failed: ' + type(exc).__name__).encode('ascii'))
                code = None
        steps.append(dict(name=name, command=command, started_utc=started,
            elapsed_ms=round((time.perf_counter() - clock) * 1000, 3),
            exit_code=code, timed_out=timed_out, status='PASS' if code == 0 and not timed_out else 'FAIL',
            log=name + '.log'))
        if steps[-1]['status'] != 'PASS':
            break  # No automatic retries or attempts to hide a failed step.
    stable = before == source_hashes(root)
    generated = {p for kind in GENERATED_DIRS for p in (root / 'evidence' / kind).glob('*/manifest.json')} - previous
    passed = len(steps) == len(STEPS) and all(s['status'] == 'PASS' for s in steps) and stable
    report = dict(schema_version=1, run_id=run_id, status='PASS' if passed else 'FAIL',
        execution_kind='author_host_self_check', source_unchanged=stable,
        python_version=sys.version, steps=steps, expected_steps=[name for name, _ in STEPS],
        generated_runs={p.parent.relative_to(root).as_posix(): sha(p) for p in sorted(generated)},
        qnx_live_execution=False, model_api_called=False, peer_reproduced=False,
        formal_E1=False, formal_E2=False, formal_E3=False, human_signoff='pending',
        course_gate='PENDING', scope='Host self-check and historical archive reanalysis only.')
    save(folder / 'summary.json', report)
    save(folder / 'manifest.json', dict(schema_version=1, source_hashes=before,
        evidence_source='author_host_self_check',
        evidence_hashes={p.name: sha(p) for p in sorted(folder.iterdir())}))
    return folder, report


def verify(folder):
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    hashes = manifest['evidence_hashes']
    required = {'summary.json', 'source-files.json'}
    if not required.issubset(hashes):
        raise ValueError('Missing self-check dependencies')
    for name, value in hashes.items():
        if Path(name).name != name or '/' in name or '\\' in name or ':' in name:
            raise ValueError('Unsafe self-check member')
        if sha(folder / name) != value:
            raise ValueError('Changed self-check evidence: ' + name)
    report = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
    if json.loads((folder / 'source-files.json').read_text(encoding='utf-8')) != manifest['source_hashes']:
        raise ValueError('Source snapshot mismatch')
    names = [name for name, _ in STEPS]
    steps = report['steps']
    if report['expected_steps'] != names or [s['name'] for s in steps] != names[:len(steps)] or len(steps) > len(names):
        raise ValueError('Unexpected self-check sequence')
    for step in steps:
        if step['log'] != step['name'] + '.log' or step['log'] not in hashes:
            raise ValueError('Missing command log')
        elapsed = step.get('elapsed_ms')
        if (isinstance(elapsed, bool) or not isinstance(elapsed, (int, float))
                or elapsed < 0
                or (isinstance(elapsed, float) and not math.isfinite(elapsed))):
            raise ValueError('Invalid elapsed_ms for step: ' + step['name'])
        expected = 'PASS' if step['exit_code'] == 0 and not step['timed_out'] else 'FAIL'
        if step['status'] != expected:
            raise ValueError('Command result mismatch')
    expected = 'PASS' if len(steps) == len(names) and all(s['status'] == 'PASS' for s in steps) and report['source_unchanged'] else 'FAIL'
    if report['status'] != expected or (expected == 'PASS' and 'claim-report.json' not in hashes):
        raise ValueError('Self-check disposition mismatch')
    if report['execution_kind'] != 'author_host_self_check' or report['human_signoff'] != 'pending' or report['course_gate'] != 'PENDING':
        raise ValueError('Unsupported self-check authority')
    if any(report[k] is not False for k in ('qnx_live_execution', 'model_api_called', 'peer_reproduced', 'formal_E1', 'formal_E2', 'formal_E3')):
        raise ValueError('Unsupported self-check claim')
    return report


def verify_generated(root, report):
    """Recheck linked generated artifacts; hashes alone are not semantic checks."""
    from .handoff import safe_path, manifest_integrity
    from .simulation_evidence import verify as verify_simulation
    from .change_rehearsal import verify as verify_change
    for name, value in report['generated_runs'].items():
        parts = name.split('/')
        if len(parts) != 3 or parts[0] != 'evidence' or parts[1] not in GENERATED_DIRS:
            raise ValueError('Unexpected generated artifact')
        folder = safe_path(root, name)
        if sha(folder / 'manifest.json') != value:
            raise ValueError('Generated manifest changed')
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        manifest_integrity(folder, manifest)
        if parts[1] == 'runs':
            verify_simulation(folder)
        elif parts[1] == 'change-runs':
            verify_change(folder)
        else:
            summary = json.loads((folder / 'summary.json').read_text(encoding='utf-8'))
            if summary.get('finding_id') != 'INT-F-01' or summary.get('mismatch_case_ids') != []:
                raise ValueError('Rate-accounting regression failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('run', 'verify'))
    parser.add_argument('--folder')
    args = parser.parse_args()
    if args.action == 'run':
        folder, report = run()
        print(folder)
    else:
        if not args.folder:
            parser.error('--folder is required for verify')
        report = verify(args.folder)
    verify_generated(ROOT, report)
    print('Author host self-check:', report['status'], '; peer reproduction: false')
    if report['status'] != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
