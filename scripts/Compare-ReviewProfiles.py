"""OBS-01 / engineering E1 pilot: compare frozen requests, outcomes and measured costs.

No network. No claim of independent labels, statistical significance or formal E1.
"""
import hashlib
import json
import sys
import uuid
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ipcsec.model_calibration import verify

root=Path(__file__).resolve().parents[1]
snapshots={
    'default_reasoning':'20261019-deepseek-schema2-native-v1',
    'no_reasoning':'20261019-deepseek-schema2-nothinking-native-v1',
    'criterion_routing':'20261019-deepseek-schema2-routed-native-v1',
}
reports={};baseline=None
for name,snapshot in snapshots.items():
    folder=root/'evidence/model-review-runs'/snapshot
    summary=verify(folder)
    freeze=json.loads((folder/'freeze.json').read_text())
    payloads={case:json.loads((folder/(case+'.packet.json')).read_text()) for case in freeze['case_ids']}
    requests={case:json.loads((folder/(case+'.request.json')).read_text()) for case in freeze['case_ids']}
    normalized={case:{k:v for k,v in request.items() if k!='reasoning'} for case,request in requests.items()}
    if baseline is None:baseline=(payloads,normalized)
    if (payloads,normalized)!=baseline:raise ValueError('Inputs or non-reasoning request parameters differ')
    elapsed=sum(json.loads((folder/case/'attempt-01/timing.json').read_text())['elapsed_ms'] for case in freeze['case_ids'])
    reports[name]=dict(snapshot=snapshot,integrity_sha256=hashlib.sha256((folder/'integrity.json').read_bytes()).hexdigest(),
        outcomes=summary['cases'],oracle_matches=summary['matches'],case_count=summary['count'],
        usage=summary['usage'],transport_and_validation_ms=round(elapsed,3),human_minutes=None,
        reasoning={case:request.get('reasoning',{'effort':'provider_default'}) for case,request in requests.items()})
routed=reports['criterion_routing']
report=dict(status='RECORDED_PROFILE_COMPARISON',formal_E1=False,independent_oracle=False,
    primary_variable='reasoning configuration: default / none / fixed routing by criterion',
    controls='Identical packets, model alias, prompt, schema, output ceiling 1500, timeout 45s; request difference only reasoning',
    uncontrolled=['API load/network timing','model alias may update','one trial per criterion/profile','AI-authored expected labels'],
    decision='LIMITED_ADOPT' if routed['oracle_matches']==routed['case_count'] else 'NEEDS_MORE_EVIDENCE',
    profiles=reports,human_signoff='pending',course_gate='PENDING',
    note='Local engineering pilot, not approved E1 or evidence of universal superiority. No missing human time was backfilled.')
dest=root/'evidence/model-comparisons'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
dest.mkdir(parents=True,exist_ok=False)
for name,value in (('comparison.json',report),('summary.json',dict(status=report['status'],decision=report['decision']))):
    (dest/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
manifest=dict(evidence_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in dest.iterdir()},
    source_hashes={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in
                   ('scripts/Compare-ReviewProfiles.py','ipcsec/review_contract_v2.py')},human_signoff='pending',formal_E1=False)
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print(dest)
print(json.dumps({name:dict(matches=p['oracle_matches'],total=p['case_count'],tokens=p['usage']['total_tokens'],elapsed_ms=p['transport_and_validation_ms']) for name,p in reports.items()}))
