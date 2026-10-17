"""CH-01 / SEC-04: simulation-only candidate, baseline and rollback evidence."""
import argparse
import hashlib
import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from .defense import Defense
from .harness import SimulationTarget
from .model import Case
from .runner import ROOT, source_identity


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def write(path, data): Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def corpus():
    events = [dict(time_ms=0, case=Case(f'A-{i:02d}',session_id='A').record()) for i in range(1,12)]
    events += [dict(time_ms=0, case=Case('B-independent',session_id='B').record()),
               dict(time_ms=500, case=Case('A-invalid',session_id='A',declared_length=65).record()),
               dict(time_ms=999, case=Case('A-before-expiry',session_id='A').record()),
               dict(time_ms=1000, case=Case('A-at-expiry',session_id='A').record())]
    events += [dict(time_ms=1100, case=Case(f'C-{i}',session_id='C').record()) for i in range(1,5)]
    events += [dict(time_ms=1100, case=Case('C-invalid',session_id='C',offset=-1).record()),
               dict(time_ms=1100, case=Case('C-5',session_id='C').record()),
               dict(time_ms=1100, case=Case('C-6',session_id='C').record())]
    return events


def expected(events, limit):
    # Independent list-based contract oracle: only allowed valid requests consume slots.
    history = []
    decisions = []
    for event in events:
        c, now = event['case'], event['time_ms']
        size = len(bytes.fromhex(c['payload_hex']))
        valid = (c['operation']=='ECHO' and c['flags']==0 and
                 0 <= c['offset'] <= size and c['declared_length']==size <= 64)
        if not valid:
            decisions.append('BLOCK'); continue
        count = sum(session==c['session_id'] and now-1000 < time <= now for session,time in history)
        allowed = count < limit
        decisions.append('ALLOW' if allowed else 'RATE_LIMIT')
        if allowed: history.append((c['session_id'],now))
    return decisions


def evaluate(events, cfg):
    defense, target = Defense(cfg), SimulationTarget()
    rows = []
    truth = expected(events, cfg['max_requests_per_window'])
    for event, wanted in zip(events, truth):
        case = Case(**event['case'])
        decision, reason = defense.decide(case, event['time_ms'])
        result = target.send(case) if decision=='ALLOW' else dict(target_outcome='NOT_SENT')
        rows.append(dict(case_id=case.case_id,time_ms=event['time_ms'],decision=decision,
                         expected=wanted,reason=reason,target_outcome=result['target_outcome']))
    return rows


def analyze(events, configs, profiles):
    if configs['baseline']['max_requests_per_window']!=10 or configs['candidate']['max_requests_per_window']!=5:
        raise ValueError('CH-01 requires baseline 10 and candidate 5')
    if configs['baseline']!=configs['rollback'] or configs['candidate']!=dict(configs['baseline'],max_requests_per_window=5):
        raise ValueError('Unexpected configuration delta or rollback')
    errors = []
    for name,cfg in configs.items():
        if cfg['backend']!='simulation' or cfg['native_enabled'] or len(events)>cfg['max_cases']:
            raise ValueError('Only bounded simulation rehearsal is permitted')
        rows = profiles[name]
        truth = expected(events,cfg['max_requests_per_window'])
        if len(rows)!=len(events): raise ValueError('Incomplete profile')
        for event,row,wanted in zip(events,rows,truth):
            if (row['case_id']!=event['case']['case_id'] or row['time_ms']!=event['time_ms'] or
                row['decision']!=wanted or row['expected']!=wanted or
                row['target_outcome']!=('REPLY' if wanted=='ALLOW' else 'NOT_SENT')):
                errors.append(name+': '+event['case']['case_id'])
    if profiles['baseline']!=profiles['rollback']:errors.append('rollback differs from baseline')
    return dict(status='PASS' if not errors else 'FAIL', errors=errors, change_id='CH-01',
                backend='simulation', cases_per_profile=len(events),
                counts={name:dict(Counter(r['decision'] for r in rows)) for name,rows in profiles.items()},
                approval='pending', formal_E2=False, qnx_verified=False, isolation_verdict='INCONCLUSIVE')


def run(root=ROOT):
    root=Path(root)
    baseline=read(root/'configs/lab.json'); change=read(root/'configs/ch01-candidate.json')
    if change['overrides']!={'max_requests_per_window':5}:raise ValueError('Unexpected candidate delta')
    configs=dict(baseline=baseline,candidate=dict(baseline,**change['overrides']),rollback=dict(baseline))
    events=corpus()
    profiles={name:evaluate(events,cfg) for name,cfg in configs.items()}
    summary=analyze(events,configs,profiles)
    version,files=source_identity()
    dest=root/'evidence/change-runs'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    dest.mkdir(parents=True,exist_ok=False)
    for name,value in [('events.json',events),('configs.json',configs),('summary.json',summary),
                       ('profiles.json',profiles),('source-files.json',files)]:write(dest/name,value)
    write(dest/'manifest.json',dict(change_id='CH-01',source_version=version,
        source_identity_scope='current local files; historical source is not reconstructed',
        evidence_source='local_simulation_rehearsal', formal_E2=False,human_signoff='pending',
        evidence_hashes={p.name:digest(p) for p in sorted(dest.iterdir())}))
    return dest


def verify(folder):
    folder=Path(folder)
    manifest=read(folder/'manifest.json')
    for name,value in manifest['evidence_hashes'].items():
        if Path(name).name!=name or digest(folder/name)!=value:raise ValueError('Evidence changed')
    summary=analyze(read(folder/'events.json'),read(folder/'configs.json'),read(folder/'profiles.json'))
    if summary!=read(folder/'summary.json') or summary['status']!='PASS':raise ValueError('Reanalysis failed')
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('run','verify'))
    parser.add_argument('--folder')
    args=parser.parse_args()
    if args.action=='run':print(run())
    else:print(json.dumps(verify(args.folder),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
