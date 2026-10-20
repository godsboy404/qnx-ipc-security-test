"""Internal E3 witness: Python implementation vs native-policy host oracle.

No QNX execution. Native C is statically consistent with the host oracle here.
"""
import sys
import hashlib
import json
import uuid
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ipcsec.model import Case
from ipcsec.defense import Defense
from ipcsec.native import policy_expectations

root=Path(__file__).resolve().parents[1]
cfg=json.loads((root/'configs/lab.json').read_text(encoding='utf-8'))
times=[0]*10+[900]+[1000]*10
cases=[Case(f'RATE-WITNESS-{i:02d}').record() for i in range(len(times))]
defense=Defense(cfg)
host=[defense.decide(Case(**case),time)[0] for case,time in zip(cases,times)]
native=policy_expectations(cases,[dict(begin_ns=t*1000000) for t in times],
                           dict(mode='defense',authorization='allow'))
rows=[dict(case=case,time_ms=time,simulation=left,native_host_oracle=right)
      for case,time,left,right in zip(cases,times,host,native)]
dest=root/'evidence/review-runs'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
dest.mkdir(parents=True,exist_ok=False)
def write(name,value):
    (dest/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
write('witness.json',rows)
mismatches=[r['case']['case_id'] for r in rows if r['simulation']!=r['native_host_oracle']]
write('summary.json',dict(status='REPRODUCED_INTERNAL_FINDING' if mismatches else 'PASS_HOST_REGRESSION',finding_id='INT-F-01',
    backend='host-simulation-and-native-oracle',qnx_live_execution=False,formal_E3=False,
    mismatch_case_ids=mismatches,
    total_cases=len(rows),human_signoff='pending'))
sources=('ipcsec/defense.py','ipcsec/native.py','native/qnx/include/lab_policy.h',
         'configs/lab.json','scripts/Reproduce-RateAccounting.py')
write('manifest.json',dict(source_hashes={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sources},
    evidence_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir()},
    evidence_source='local_internal_review',formal_E3=False,human_signoff='pending'))
print(dest)
print((dest/'summary.json').read_text(encoding='utf-8'))
raise SystemExit(1 if mismatches else 0)
