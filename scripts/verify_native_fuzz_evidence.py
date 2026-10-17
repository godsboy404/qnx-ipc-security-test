"""Read-only verification of archived native fuzz evidence and its manifest."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ipcsec.native import verify_archived

root = Path(__file__).resolve().parents[1]
folders = [Path(sys.argv[1])] if len(sys.argv) > 1 else sorted((root/'evidence/native-fuzz-runs').glob('*'))
if not folders:
    raise SystemExit('No native fuzz evidence')
failures=0
for folder in folders:
    try:
        summary, _ = verify_archived(folder)
        print(f'{folder.name}: PASS ({summary["cases"]} cases; isolation INCONCLUSIVE)')
    except (ValueError, KeyError, OSError) as exc:
        failures+=1
        print(f'{folder.name}: FAIL ({exc})')
raise SystemExit(1 if failures else 0)
