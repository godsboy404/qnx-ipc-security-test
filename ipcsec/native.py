"""Bounded corpus bridge and evidence analysis for the owned QNX devctl lab."""
import argparse
import hashlib
import json
import struct
from dataclasses import replace
from pathlib import Path

from .model import Case
from .fuzzer import generate
from .runner import oracle

MAX_CASES = 200
AUTH_CONTENT = {'allow':b'lab-resmgr-01 allow\n','deny':b'lab-resmgr-01 deny\n',
    'missing':b'','malformed':b'lab-resmgr-01 allow EXTRA\n','wrong-target':b'unregistered-target allow\n'}


def authorization_allowed(meta,index):
    return (meta['authorization_states'][index] if meta.get('authorization_control') else meta['authorization'])=='allow'

def corpus(count=128, seed=20261015):
    if not 16 <= count <= MAX_CASES:
        raise ValueError('Native corpus budget is 16..200 cases')
    anchors = [Case('anchor',declared_length=n,payload_hex='61'*n,mutation='boundary') for n in (0,1,63,64)]
    anchors += [Case('anchor',declared_length=65,payload_hex='61'*65,mutation='boundary'),
                Case('anchor',declared_length=0xffffffff,mutation='boundary'),
                Case('anchor',declared_length=0,mutation='boundary'),
                Case('anchor',offset=-1,mutation='field'),
                Case('anchor',offset=5,mutation='field'),
                Case('anchor',offset=4,mutation='field'),
                Case('anchor',operation='INVALID',mutation='field'),
                Case('anchor',flags=8,mutation='field'),
                Case('anchor',operation='INVALID',declared_length=65,flags=8,mutation='combination'),
                Case('anchor',offset=-1,flags=8,mutation='combination')]
    cases = anchors + generate(count-len(anchors),seed)
    return [replace(c,case_id=f'NF-{i:04d}') for i,c in enumerate(cases)]

def encode_case(c):
    if c.operation not in ('ECHO','INVALID'):
        raise ValueError('Unknown operation mapping')
    if c.mutation not in ('normal','boundary','field','combination'):
        raise ValueError('Unknown mutation')
    payload = bytes.fromhex(c.payload_hex)
    if len(payload)>65 or not 0 <= c.declared_length <= 0xffffffff or not -(2**31)<=c.offset<2**31 or not 0<=c.flags<=0xffffffff:
        raise ValueError('Case exceeds bounded native encoding')
    if not c.case_id or len(c.case_id)>31 or any(ch not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for ch in c.case_id):
        raise ValueError('Unsafe case ID')
    return '\t'.join(map(str,(c.case_id,c.mutation,1 if c.operation=='ECHO' else 0xffffffff,
                              c.declared_length,c.offset,c.flags,c.payload_hex or '-')))+'\n'

def prepare(dest,count=128,seed=20261015):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
    if any(dest.iterdir()):raise ValueError('Corpus directory must be empty; never overwrite a run')
    cases=corpus(count,seed)
    (dest/'corpus.tsv').write_text(''.join(encode_case(c) for c in cases),encoding='ascii')
    (dest/'cases.jsonl').write_text(''.join(json.dumps(dict(c.record(),oracle_label=oracle(c)))+'\n' for c in cases),encoding='utf-8')
    digest=hashlib.sha256((dest/'corpus.tsv').read_bytes()).hexdigest()
    (dest/'corpus-meta.json').write_text(json.dumps({'seed':seed,'count':count,'corpus_sha256':digest,
        'target_id':'lab-resmgr-01','device':'/dev/ipcsec-lab','max_actual_payload':65,
        'max_ipc_ms':2000,'monitor_deadline_s':15,'backend':'qnx-native'},indent=2),encoding='utf-8')
    return dest


def encode_policy_case(c, delay_ms=0):
    if c.session_id not in [f'session-{i:02d}' for i in range(1,9)] or not 0<=delay_ms<=1100:
        raise ValueError('Invalid bounded session or delay')
    return encode_case(c).rstrip('\n')+f'\t{int(c.session_id[-2:])-1}\t{delay_ms}\n'


def prepare_policy(dest,count=128,seed=20261015,mode='defense',suite='mixed',authorization='allow'):
    if mode not in ('baseline','defense') or suite not in ('mixed','rate','authorization') or authorization not in ('allow','deny'):
        raise ValueError('Unknown native policy configuration')
    if suite=='rate':
        cases=[Case(f'NR-{i:04d}',session_id='session-02' if i in (11,23) else 'session-01') for i in range(24)]
    elif suite=='authorization':
        if authorization!='allow':raise ValueError('Authorization sequence requires initial allow')
        cases=[Case(f'NA-{i:04d}') for i in range(24)]
    else:cases=corpus(count,seed)
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
    if any(dest.iterdir()):raise ValueError('Never overwrite a run')
    delays=[1100 if suite=='rate' and i==12 else 0 for i in range(len(cases))]
    (dest/'corpus.tsv').write_text(''.join(encode_policy_case(c,d) for c,d in zip(cases,delays)),encoding='ascii')
    (dest/'cases.jsonl').write_text(''.join(json.dumps(dict(c.record(),oracle_label=oracle(c)))+'\n' for c in cases),encoding='utf-8')
    controlled=suite=='authorization'
    (dest/'defense-mode.txt').write_bytes((mode+('-auth' if controlled else '')+'\n').encode('ascii'))
    (dest/'authorization.txt').write_bytes(('lab-resmgr-01 '+authorization+'\n').encode('ascii'))
    meta=dict(schema_version=2,mode=mode,suite=suite,authorization=authorization,seed=seed,count=len(cases),
        delays_ms=delays,corpus_sha256=hashlib.sha256((dest/'corpus.tsv').read_bytes()).hexdigest(),
        target_id='lab-resmgr-01',device='/dev/ipcsec-lab',max_actual_payload=65,max_ipc_ms=2000,
        monitor_deadline_s=15,backend='qnx-native')
    if controlled:
        states=[state for state in ('allow','deny','missing','malformed','wrong-target','allow') for _ in range(4)]
        meta.update(authorization_control=True,authorization_states=states)
        (dest/'authorization-plan.txt').write_bytes(('\n'.join(states)+'\n').encode('ascii'))
    (dest/'corpus-meta.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return dest

def prepare_replay(source,dest,case_id):
    source=Path(source);dest=Path(dest)
    meta=read_json(source/'corpus-meta.json')
    if hashlib.sha256((source/'corpus.tsv').read_bytes()).hexdigest()!=meta['corpus_sha256']:
        raise ValueError('Replay source corpus is modified')
    source_cases=read_rows(source/'cases.jsonl')
    canonical=canonical_corpus(source_cases,meta)
    if (source/'corpus.tsv').read_text(encoding='ascii')!=canonical:
        raise ValueError('Replay source JSON differs from transported corpus')
    matches=[row for row in source_cases if row['case_id']==case_id]
    if len(matches)!=1:raise ValueError('Replay case must uniquely exist in source corpus')
    c=Case(**{k:v for k,v in matches[0].items() if k!='oracle_label'})
    dest.mkdir(parents=True,exist_ok=True)
    if any(dest.iterdir()):raise ValueError('Replay directory must be empty')
    version=meta.get('schema_version',1)
    (dest/'corpus.tsv').write_text(encode_policy_case(c) if version==2 else encode_case(c),encoding='ascii')
    (dest/'cases.jsonl').write_text(json.dumps(dict(c.record(),oracle_label=oracle(c)))+'\n',encoding='utf-8')
    meta=dict(meta,count=1,corpus_sha256=hashlib.sha256((dest/'corpus.tsv').read_bytes()).hexdigest(),
              replay_source=source.name,replay_source_corpus_sha256=meta['corpus_sha256'],replay_case_id=case_id)
    if version==2:
        meta['delays_ms']=[0]
        for name in ('defense-mode.txt','authorization.txt'):
            (dest/name).write_bytes((source/name).read_bytes())
        if meta.get('authorization_control'):
            index=next(i for i,row in enumerate(source_cases) if row['case_id']==case_id)
            state=meta['authorization_states'][index]
            meta['authorization_states']=[state]
            (dest/'authorization-plan.txt').write_bytes((state+'\n').encode('ascii'))
    (dest/'corpus-meta.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
    return dest

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def canonical_corpus(cases,meta):
    objects=[Case(**{k:v for k,v in c.items() if k!='oracle_label'}) for c in cases]
    if meta.get('schema_version',1)==2:
        if len(meta['delays_ms'])!=len(objects):raise ValueError('Schedule length mismatch')
        return ''.join(encode_policy_case(c,d) for c,d in zip(objects,meta['delays_ms']))
    return ''.join(encode_case(c) for c in objects)


def policy_expectations(cases,rows,meta):
    """Independent host oracle; live monotonic timestamps, not fuzzer decisions."""
    histories={};decisions=[]
    for index,(c,r) in enumerate(zip(cases,rows)):
        if not authorization_allowed(meta,index):decision='SCOPE_DENY'
        elif meta['mode']=='baseline':decision='ALLOW'
        elif oracle(Case(**{k:v for k,v in c.items() if k!='oracle_label'}))!='valid':decision='BLOCK'
        else:
            now=r['begin_ns'];key=c['session_id']
            recent=[t for t in histories.get(key,[]) if now-1000000000<t<=now]
            decision='RATE_LIMIT' if len(recent)>=10 else 'ALLOW'
            if decision=='ALLOW':recent.append(now)
            histories[key]=recent
        decisions.append(decision)
    return decisions

def analyze(folder, write_summary=True):
    folder=Path(folder)
    meta=read_json(folder/'corpus-meta.json')
    if hashlib.sha256((folder/'corpus.tsv').read_bytes()).hexdigest()!=meta['corpus_sha256']:
        raise ValueError('Corpus hash mismatch')
    cases=read_rows(folder/'cases.jsonl');rows=read_rows(folder/'fuzz-results.jsonl')
    monitor=read_json(folder/'monitor-summary.json')
    samples=read_rows(folder/'monitor.jsonl');heartbeats=read_rows(folder/'heartbeat.jsonl')
    calibration=read_json(folder/'monitor-selftest.json')
    codes=read_json(folder/'fuzzer-meta.json');cleanup=read_json(folder/'cleanup.json')
    errors=[]
    version=meta.get('schema_version',1)
    canonical=canonical_corpus(cases,meta)
    if (folder/'corpus.tsv').read_text(encoding='ascii')!=canonical:errors.append('TSV and JSON corpus differ')
    if len(cases)!=meta['count'] or len(rows)!=len(cases):errors.append('partial or extra case execution')
    if len({r['case_id'] for r in rows})!=len(rows):errors.append('duplicate result IDs')
    if [r['case_id'] for r in rows]!=[c['case_id'] for c in cases]:errors.append('execution order/identity mismatch')
    decisions=policy_expectations(cases,rows,meta) if version==2 else ['ALLOW']*len(rows)
    for i,(c,r,decision) in enumerate(zip(cases,rows,decisions)):
        case=Case(**{k:v for k,v in c.items() if k!='oracle_label'})
        label=oracle(case)
        if c['oracle_label']!=label:errors.append(c['case_id']+': altered oracle')
        expected_op=1 if c['operation']=='ECHO' else 0xffffffff
        if any(r[k]!=v for k,v in dict(operation=expected_op,declared_length=c['declared_length'],
                offset=c['offset'],flags=c['flags'],payload_hex=c['payload_hex']).items()):
            errors.append(c['case_id']+': transported fields mismatch')
        if r['backend']!='qnx-native' or r['actual_payload_bytes']!=len(bytes.fromhex(c['payload_hex'])):
            errors.append(c['case_id']+': backend or length mismatch')
        if version==2:
            expected_session=int(c['session_id'][-2:])-1
            if r['session_index']!=expected_session or r['delay_before_ms']!=meta['delays_ms'][i]:
                errors.append(c['case_id']+': session/schedule mismatch')
            if r['decision']!=decision or r['forwarded']!=(decision=='ALLOW') or r['authorized']!=authorization_allowed(meta,i):
                errors.append(c['case_id']+': policy decision mismatch')
        if decision!='ALLOW':
            if r['outcome']!='NOT_SENT' or r['return_code']!=-1 or r['reply_matches']:
                errors.append(c['case_id']+': blocked request claims target response')
        elif label=='valid':
            if r['outcome']!='REPLY' or not r['reply_matches'] or r['return_code']!=0:
                errors.append(c['case_id']+': legal request failed')
        elif r['outcome']!='ERROR_REPLY' or r['return_code'] not in (codes['EINVAL'],codes['EMSGSIZE']):
            errors.append(c['case_id']+': invalid request did not receive bounded rejection')
        if r['fuzzer_pid']!=monitor['worker_pid']:errors.append(c['case_id']+': worker identity mismatch')
    if monitor['watchdog_expired'] or monitor['worker_state']!='exited' or monitor['worker_exit_code']!=0:
        errors.append('worker incomplete or monitor deadline')
    if monitor['target_state_before_cleanup']!='running' or monitor['peer_state_before_cleanup']!='running':
        errors.append('target or peer not running before expected cleanup')
    if not calibration.get('exit7_observed') or not calibration.get('sigterm_observed'):
        errors.append('observer selftest failed')
    if len(heartbeats)<2 or any(h['pid']!=monitor['peer_pid'] for h in heartbeats):
        errors.append('insufficient independent heartbeat evidence')
    if any(b['mono_ns']<=a['mono_ns'] for a,b in zip(heartbeats,heartbeats[1:])):
        errors.append('heartbeat clock did not progress')
    if not samples or any(s['monitor_pid']!=monitor['monitor_pid'] for s in samples):
        errors.append('monitor sampling missing or mismatched')
    if any(s['target_pid']!=monitor['target_pid'] or s['worker_pid']!=monitor['worker_pid'] or
           s['peer_pid']!=monitor['peer_pid'] for s in samples):errors.append('sample process identity mismatch')
    if rows and samples and (samples[-1]['mono_ns']<rows[0]['begin_ns'] or samples[0]['mono_ns']>rows[-1]['end_ns']):
        errors.append('monitor did not overlap execution')
    if not all(cleanup.get(k) for k in ('target_reaped','worker_reaped','peer_reaped')) or cleanup.get('device_present') is not False:
        errors.append('owned process cleanup incomplete')
    if len({monitor['monitor_pid'],monitor['worker_pid'],monitor['target_pid'],monitor['peer_pid']})!=4:
        errors.append('observer and observed roles not independent processes')
    for r in rows:
        if r['begin_ns']>r['end_ns']:errors.append('invalid monotonic timestamps')
    policy_summary={}
    if version==2:
        if codes.get('schema_version')!=2 or codes.get('defense_enabled')!=(meta['mode']=='defense'):
            errors.append('native policy mode mismatch')
        mode_text=meta['mode']+('-auth' if meta.get('authorization_control') else '')+'\n'
        if (folder/'defense-mode.txt').read_bytes()!=mode_text.encode('ascii') or (folder/'authorization.txt').read_bytes()!=('lab-resmgr-01 '+meta['authorization']+'\n').encode('ascii'):
            errors.append('policy configuration mismatch')
        if not read_json(folder/'policy-selftest.json').get('passed'):errors.append('policy calibration failed')
        for previous,current in zip(rows,rows[1:]):
            if current['begin_ns']<previous['end_ns']:errors.append('request clock/order regressed')
        if meta['suite']=='rate' and not meta.get('replay_source') and meta['authorization']=='allow' and len(rows)==24:
            expected=['RATE_LIMIT' if i in (10,22) else 'ALLOW' for i in range(24)] if meta['mode']=='defense' else ['ALLOW']*24
            if decisions!=expected:errors.append('live rate/session/recovery scenario did not exercise expected behavior')
            if rows[12]['begin_ns']-rows[11]['end_ns']<1100000000:
                errors.append('live window recovery wait was too short')
        audit=read_rows(folder/'target-audit.jsonl')
        sent=[r for r in rows if r['forwarded']]
        if len(audit)!=len(sent):errors.append('receiver count differs from forwarded count')
        for index,(a,r) in enumerate(zip(audit,sent)):
            wire=struct.pack('<IIiI',r['operation'],r['declared_length'],r['offset'],r['flags'])+bytes.fromhex(r['payload_hex'])
            if a['sequence']!=index+1 or a['target_pid']!=monitor['target_pid'] or a['wire_hex']!=wire.hex() or a['dcmd_bytes']!=len(wire) or not r['begin_ns']<=a['mono_ns']<=r['end_ns']:
                errors.append('receiver content/order/time differs from forwarded request')
        policy_summary=dict(mode=meta['mode'],suite=meta['suite'],forwarded_count=len(sent),
            target_received_count=len(audit),blocked_count=decisions.count('BLOCK'),
            rate_limited_count=decisions.count('RATE_LIMIT'),scope_denied_count=decisions.count('SCOPE_DENY'))
        if meta.get('authorization_control'):
            events=read_rows(folder/'authorization-events.jsonl');states=meta['authorization_states']
            if len(states)!=len(cases) or len(events)!=len(cases):errors.append('authorization event count mismatch')
            if (folder/'authorization-plan.txt').read_bytes()!=('\n'.join(states)+'\n').encode('ascii'):
                errors.append('authorization plan mismatch')
            for i,(event,row,state) in enumerate(zip(events,rows,states)):
                if event['sequence']!=i+1 or event['monitor_pid']!=monitor['monitor_pid'] or event['state']!=state or event['content_hex']!=AUTH_CONTENT[state].hex() or event['file_present']!=(state!='missing'):
                    errors.append('authorization controller identity/content mismatch')
                if event['applied_ns']>row['begin_ns'] or (i and event['applied_ns']<rows[i-1]['end_ns']):
                    errors.append('authorization change did not precede next request')
            policy_summary.update(authorization_event_count=len(events),authorization_control=True)
    summary={'backend':'qnx-native','cases':len(rows),'valid_cases':sum(c['oracle_label']=='valid' for c in cases),
        'invalid_cases':sum(c['oracle_label']=='invalid' for c in cases),
        'reply_count':sum(r['outcome']=='REPLY' for r in rows),
        'error_reply_count':sum(r['outcome']=='ERROR_REPLY' for r in rows),
        'timeout_count':sum(r['outcome']=='TIMEOUT' for r in rows),
        'monitor_samples':len(samples),'peer_heartbeats':len(heartbeats),
        'target_state_before_cleanup':monitor['target_state_before_cleanup'],
        'observer_calibrated':not not calibration.get('exit7_observed') and not not calibration.get('sigterm_observed'),
        'system_service_probe':None,'isolation_verdict':'INCONCLUSIVE','isolation_success_rate':None,
        'errors':errors,'status':'PASS' if not errors else 'FAIL',
        'scope':'bounded inputs to owned devctl service; process/peer liveness, not global health or crash isolation'}
    summary.update(policy_summary)
    if write_summary:
        (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary


def verify_archived(folder):
    """Read-only consistency check; hashes are not signatures or peer signoff."""
    folder=Path(folder).resolve()
    manifest=read_json(folder/'manifest.json')
    for name,digest in manifest['evidence_hashes'].items():
        path=(folder/name).resolve()
        if path.parent!=folder or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError(f'Evidence hash mismatch: {name}')
    summary=analyze(folder,write_summary=False)
    if summary!=read_json(folder/'summary.json') or summary['status']!='PASS':
        raise ValueError(f'Evidence analysis failed: {folder.name}')
    return summary,manifest


def compare_policy(baseline,defense):
    baseline=Path(baseline);defense=Path(defense)
    a,am=verify_archived(baseline);b,bm=verify_archived(defense)
    ac=read_json(baseline/'corpus-meta.json');bc=read_json(defense/'corpus-meta.json')
    if a.get('mode')!='baseline' or b.get('mode')!='defense':raise ValueError('Expected baseline and defense runs')
    if ac['authorization']!='allow' or bc['authorization']!='allow':raise ValueError('Paired runs require authorization')
    for key in ('corpus_sha256','count','suite','seed','delays_ms'):
        if ac[key]!=bc[key]:raise ValueError('Paired corpus/configuration differs: '+key)
    for key in ('authorization_control','authorization_states'):
        if ac.get(key)!=bc.get(key):raise ValueError('Paired authorization plan differs')
    if am['binary_hashes']!=bm['binary_hashes'] or am['source_hashes']!=bm['source_hashes']:
        raise ValueError('Paired source or binary versions differ')
    return dict(status='PASS',baseline_run=baseline.name,defense_run=defense.name,
        baseline_manifest_sha256=hashlib.sha256((baseline/'manifest.json').read_bytes()).hexdigest(),
        defense_manifest_sha256=hashlib.sha256((defense/'manifest.json').read_bytes()).hexdigest(),
        corpus_sha256=ac['corpus_sha256'],suite=ac['suite'],cases=ac['count'],
        baseline_forwarded=a['forwarded_count'],defense_forwarded=b['forwarded_count'],
        invalid_blocked=b['blocked_count'],valid_rate_limited=b['rate_limited_count'],
        isolation_verdict='INCONCLUSIVE',peer_reproduced=False)

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('prepare');a.add_argument('directory');a.add_argument('--count',type=int,default=128);a.add_argument('--seed',type=int,default=20261015)
    a=sub.add_parser('prepare-policy');a.add_argument('directory');a.add_argument('--count',type=int,default=128);a.add_argument('--seed',type=int,default=20261015)
    a.add_argument('--mode',choices=('baseline','defense'),default='defense');a.add_argument('--suite',choices=('mixed','rate','authorization'),default='mixed');a.add_argument('--authorization',choices=('allow','deny'),default='allow')
    a=sub.add_parser('analyze');a.add_argument('directory')
    a=sub.add_parser('replay');a.add_argument('source');a.add_argument('directory');a.add_argument('--case-id',required=True)
    args=p.parse_args()
    if args.action=='prepare':print(prepare(args.directory,args.count,args.seed))
    elif args.action=='prepare-policy':print(prepare_policy(args.directory,args.count,args.seed,args.mode,args.suite,args.authorization))
    elif args.action=='replay':print(prepare_replay(args.source,args.directory,args.case_id))
    else:
        summary=analyze(args.directory);print(json.dumps(summary,indent=2))
        if summary['errors']:raise SystemExit(1)

if __name__=='__main__':main()
