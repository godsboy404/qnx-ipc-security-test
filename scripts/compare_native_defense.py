"""Verify paired native runs, then save a new comparison without changing them."""
import argparse
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from ipcsec.native import compare_policy

p=argparse.ArgumentParser()
p.add_argument('baseline');p.add_argument('defense')
args=p.parse_args()
result=compare_policy(args.baseline,args.defense)
run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8]
dest=root/'evidence/native-comparisons'/run_id
dest.mkdir(parents=True,exist_ok=False)
(dest/'comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2));print(dest)
