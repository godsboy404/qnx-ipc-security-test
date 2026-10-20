"""Display a verified local self-check report without running any work."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ipcsec.local_check import verify, verify_generated


def _print_report(report):
    print('Local self-check summary')
    print('------------------------')
    print('Run ID:           ' + report['run_id'])
    print('Overall status:   ' + report['status'])
    print('Execution scope:  ' + report['scope'])
    print('Course gate:      ' + report['course_gate'])
    print('Peer reproduced:  ' + ('yes' if report['peer_reproduced'] else 'no'))
    print('QNX live run:     ' + ('yes' if report['qnx_live_execution'] else 'no'))
    print('Model API called: ' + ('yes' if report['model_api_called'] else 'no'))
    print()
    print('Steps')
    print('-----')
    print(f'{"#":>2}  {"Name":<30} {"Status":<6} {"Elapsed (ms)":>12}')
    for index, step in enumerate(report['steps'], start=1):
        print(f'{index:>2}  {step["name"]:<30} {step["status"]:<6} {step["elapsed_ms"]:>12}')
    print()
    print(f'Checked steps: {len(report["steps"])} / {len(report["expected_steps"])}')
    print('Evidence scope: ' + report['scope'])
    print('Note: this display confirms stored report and linked-evidence verification;')
    print('      it does not establish course approval, peer reproduction, or independence.')


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            'Display a previously saved local self-check after full verification. '
            'Exit 0 means the report was verified and displayed; it does not '
            'mean the stored self-check status is PASS.'
        )
    )
    parser.add_argument('--folder', required=True, help='Saved local-check run folder')
    args = parser.parse_args(argv)
    folder = Path(args.folder).resolve()
    try:
        report = verify(folder)
        verify_generated(ROOT, report)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f'Local self-check verification failed: {exc}', file=sys.stderr)
        return 1
    _print_report(report)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
