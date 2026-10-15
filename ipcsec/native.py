"""Bounded corpus bridge and evidence analysis for the owned QNX devctl lab."""
import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

from .model import Case
from .fuzzer import generate
from .runner import oracle

MAX_CASES = 200

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
    cases=corpus(count,seed)
    (dest/'corpus.tsv').write_text(''.join(encode_case(c) for c in cases),encoding='ascii')
    (dest/'cases.jsonl').write_text(''.join(json.dumps(dict(c.record(),oracle_label=oracle(c)))+'\n' for c in cases),encoding='utf-8')
    digest=hashlib.sha256((dest/'corpus.tsv').read_bytes()).hexdigest()
    (dest/'corpus-meta.json').write_text(json.dumps({'seed':seed,'count':count,'corpus_sha256':digest,
        'target_id':'lab-resmgr-01','device':'/dev/ipcsec-lab','max_actual_payload':65,
        'max_ipc_ms':2000,'monitor_deadline_s':15,'backend':'qnx-native'},indent=2),encoding='utf-8')
    return dest

def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]

def analyze(folder):
    folder=Path(folder)
    meta=read_json(folder/'corpus-meta.json')
    if hashlib.sha256((folder/'corpus.tsv').read_bytes()).hexdigest()!=meta['corpus_sha256']:
        raise ValueError('Corpus hash mismatch')
    cases=read_rows(folder/'cases.jsonl');rows=read_rows(folder/'fuzz-results.jsonl')
    monitor=read_json(folder/'monitor-summary.json')
    samples=read_rows(folder/'monitor.jsonl');heartbeats=read_rows(folder/'heartbeat.jsonl')
    calibration=read_json(folder/'monitor-selftest.json')
    errors=[]
    if len(cases)!=meta['count'] or len(rows)!=len(cases):errors.append('partial or extra case execution')
    if len({r['case_id'] for r in rows})!=len(rows):errors.append('duplicate result IDs')
    if [r['case_id'] for r in rows]!=[c['case_id'] for c in cases]:errors.append('execution order/identity mismatch')
    for c,r in zip(cases,rows):
        case=Case(**{k:v for k,v in c.items() if k!='oracle_label'})
        label=oracle(case)
        if c['oracle_label']!=label:errors.append(c['case_id']+': altered oracle')
        expected_op=1 if c['operation']=='ECHO' else 0xffffffff
        if any(r[k]!=v for k,v in dict(operation=expected_op,declared_length=c['declared_length'],
                offset=c['offset'],flags=c['flags'],payload_hex=c['payload_hex']).items()):
            errors.append(c['case_id']+': transported fields mismatch')
        if r['backend']!='qnx-native' or r['actual_payload_bytes']!=len(bytes.fromhex(c['payload_hex'])):
            errors.append(c['case_id']+': backend or length mismatch')
        if label=='valid':
            if r['outcome']!='REPLY' or not r['reply_matches'] or r['return_code']!=0:
                errors.append(c['case_id']+': legal request failed')
        elif r['outcome']!='ERROR_REPLY' or r['return_code'] not in (22,90):
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
    if len({monitor['monitor_pid'],monitor['worker_pid'],monitor['target_pid'],monitor['peer_pid']})!=4:
        errors.append('observer and observed roles not independent processes')
    for r in rows:
        if r['begin_ns']>r['end_ns']:errors.append('invalid monotonic timestamps')
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
    (folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
    a=sub.add_parser('prepare');a.add_argument('directory');a.add_argument('--count',type=int,default=128);a.add_argument('--seed',type=int,default=20261015)
    a=sub.add_parser('analyze');a.add_argument('directory')
    args=p.parse_args()
    if args.action=='prepare':print(prepare(args.directory,args.count,args.seed))
    else:
        summary=analyze(args.directory);print(json.dumps(summary,indent=2))
        if summary['errors']:raise SystemExit(1)

if __name__=='__main__':main()
