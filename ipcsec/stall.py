"""Independent evidence analysis for an owned-service pause/timeout/resume."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from .native import read_json,read_rows

EVENTS=['ready','before_complete','client_connected','pause_requested','paused',
        'timeout_observed','resume_requested','resumed','after_complete']


def prepare(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    if any(folder.iterdir()):raise ValueError('Never overwrite stall evidence')
    config=dict(backend='qnx-native',target_id='lab-resmgr-01',device='/dev/ipcsec-lab',
        fault_kind='controlled_SIGSTOP',before_count=10,after_count=10,blocked_count=1,checkpoint_count=1,pause_checkpoint='before_next_receive',
        ipc_timeout_ns=2000000000,monitor_deadline_seconds=15,host_deadline_seconds=45)
    (folder/'stall-config.json').write_text(json.dumps(config,indent=2),encoding='utf-8');return folder


def analyze(folder,write_summary=True):
    folder=Path(folder)
    required=('stall-config.json','stall-meta.json','stall-cleanup.json','stall-events.jsonl',
        'stall-monitor.jsonl','os-probe.jsonl','before.jsonl','after.jsonl','stall-ready.json',
        'stall-request.json','stall-client-trace.jsonl','target-audit.jsonl','host-execution.json')
    missing=[name for name in required if not (folder/name).is_file() or not (folder/name).stat().st_size]
    if missing:
        summary=dict(backend='qnx-native',status='FAIL',target_fault='UNKNOWN',isolation_verdict='INCONCLUSIVE',
            errors=['incomplete or empty evidence: '+name for name in missing])
        if write_summary:(folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
        return summary
    config=read_json(folder/'stall-config.json');meta=read_json(folder/'stall-meta.json')
    cleanup=read_json(folder/'stall-cleanup.json');events=read_rows(folder/'stall-events.jsonl')
    samples=read_rows(folder/'stall-monitor.jsonl');probes=read_rows(folder/'os-probe.jsonl')
    before=read_rows(folder/'before.jsonl');after=read_rows(folder/'after.jsonl')
    ready=read_json(folder/'stall-ready.json');blocked=read_json(folder/'stall-request.json')
    trace=read_rows(folder/'stall-client-trace.jsonl')
    audit=read_rows(folder/'target-audit.jsonl');errors=[]
    if config['fault_kind']!='controlled_SIGSTOP' or meta['fault_kind']!=config['fault_kind'] or meta['backend']!='qnx-native' or config['device']!='/dev/ipcsec-lab' or config['target_id']!='lab-resmgr-01':errors.append('unexpected target/backend/fault kind')
    if [e['event'] for e in events]!=EVENTS:raise ValueError('Incomplete or reordered stall events')
    e=dict(zip(EVENTS,events));roles=[cleanup[k] for k in ('monitor_pid','target_pid','probe_pid','before_client_pid','blocked_client_pid','after_client_pid')]
    if len(set(roles))!=6 or any(pid<=0 for pid in roles) or cleanup['monitor_pid']!=meta['monitor_pid']:errors.append('process roles not distinct')
    if not cleanup['complete'] or not cleanup['all_owned_children_reaped'] or cleanup['device_present'] or cleanup.get('pause_watchdog_triggered',False):errors.append('cleanup incomplete or pause watchdog triggered')
    if any(b['mono_ns']<a['mono_ns'] for a,b in zip(events,events[1:])):errors.append('event clock regressed')
    for event in events:
        paused=event['event'] in ('paused','timeout_observed','resume_requested')
        if event['monitor_pid']!=meta['monitor_pid'] or event['target_pid']!=cleanup['target_pid'] or event['target_signal']!=0:errors.append('target identity/liveness changed')
        if event['device_present']!=(None if paused else True):errors.append('paused device visibility must be unknown; responsive phases must observe device')
        if event['target_state']!=('stopped' if paused else 'running'):errors.append('pause/resume state not observed')
        if paused and event['target_stop_signal']!=meta['SIGSTOP']:errors.append('SIGSTOP not independently observed')
    for name,key in [('before_complete','before_client_pid'),('client_connected','blocked_client_pid'),('timeout_observed','blocked_client_pid'),('after_complete','after_client_pid')]:
        if e[name]['client_pid']!=cleanup[key]:errors.append('event client identity mismatch')
    if ready['client_pid']!=cleanup['blocked_client_pid'] or not e['before_complete']['mono_ns']<=ready['ready_ns']<=e['client_connected']['mono_ns']:errors.append('client was not connected before pause')
    duration=blocked['end_ns']-blocked['begin_ns']
    if blocked['client_pid']!=cleanup['blocked_client_pid'] or blocked['outcome']!='TIMEOUT' or blocked['return_code']!=meta['ETIMEDOUT'] or blocked['configured_timeout_ns']!=2000000000 or config['ipc_timeout_ns']!=2000000000:errors.append('real configured timeout not observed')
    if not e['paused']['mono_ns']<=blocked['begin_ns']<=blocked['end_ns']<=e['timeout_observed']['mono_ns'] or not 2000000000<=duration<15000000000:errors.append('timeout timing/paused interval inconsistent')
    if [t['stage'] for t in trace]!=['connected','checkpoint_request','before_devctl','devctl_returned']:raise ValueError('Incomplete client/checkpoint trace')
    warm=dict(trace[1],sequence=1)
    if config.get('pause_checkpoint')!='before_next_receive' or warm['client_pid']!=cleanup['blocked_client_pid'] or not e['pause_requested']['mono_ns']<=warm['begin_ns']<=warm['end_ns']<=blocked['begin_ns']:errors.append('checkpoint request timing/identity mismatch')
    if trace[3]['return_code']!=blocked['return_code'] or trace[3]['mono_ns']!=blocked['end_ns']:errors.append('timeout trace differs from result')
    if len(before)!=10 or len(after)!=10 or len(audit)!=21:errors.append('request/receiver count differs; possible missing or late delivery')
    wire=(struct.pack('<IIiI',1,4,0,0)+b'ping').hex()
    rows=before+[warm]+after
    for i,(row,a) in enumerate(zip(rows,audit)):
        stage='before' if i<10 else ('checkpoint' if i==10 else 'after')
        pid=cleanup['blocked_client_pid' if stage=='checkpoint' else stage+'_client_pid']
        sequence=i+1 if i<10 else (1 if i==10 else i-10)
        if row['sequence']!=sequence or row['client_pid']!=pid or row['return_code']!=0 or not row['reply_matches']:errors.append('normal reply/identity mismatch')
        if stage!='checkpoint' and not e['ready' if stage=='before' else 'resumed']['mono_ns']<=row['begin_ns']<=row['end_ns']<=e[stage+'_complete']['mono_ns']:errors.append('normal request outside phase')
        expected_wire=(struct.pack('<IIiI',1,4,0,0)+b'gate').hex() if stage=='checkpoint' else wire
        if a['sequence']!=i+1 or a['target_pid']!=cleanup['target_pid'] or a['wire_hex']!=expected_wire or a['dcmd_bytes']!=20 or not row['begin_ns']<=a['mono_ns']<=row['end_ns']:errors.append('receiver content/order/timing mismatch')
    if not samples or any(s['monitor_pid']!=meta['monitor_pid'] or s['target_pid']!=cleanup['target_pid'] or s['probe_pid']!=cleanup['probe_pid'] or s['probe_state']!='running' for s in samples):errors.append('independent monitor missing or identity mismatch')
    if any(b['mono_ns']<a['mono_ns'] for a,b in zip(samples,samples[1:])):errors.append('monitor clock regressed')
    if not probes or any(p['probe_pid']!=cleanup['probe_pid'] or p['uname_rc'] or p['uname_errno'] or p['proc_stat_rc'] or p['proc_stat_errno'] or not p['proc_is_directory'] or p['begin_ns']>p['end_ns'] for p in probes):errors.append('read-only OS probe failure')
    if any(b['begin_ns']<=a['end_ns'] for a,b in zip(probes,probes[1:])):errors.append('probe clock/order invalid')
    coverage={}
    for phase,left,right in [('before',e['ready']['mono_ns'],e['pause_requested']['mono_ns']),('paused',e['paused']['mono_ns'],e['resume_requested']['mono_ns']),('after',e['resumed']['mono_ns'],samples[-1]['mono_ns'] if samples else 0)]:
        coverage[phase]=sum(left<=p['begin_ns']<=p['end_ns']<=right for p in probes)
        if coverage[phase]<2:errors.append('insufficient probe coverage: '+phase)
    host=read_json(folder/'host-execution.json')
    if host['host_watchdog_timeout'] or host['remote_exit_code']!=0:errors.append('host deadline/remote execution failed')
    summary=dict(backend='qnx-native',fault_kind='controlled_SIGSTOP',before_replies=len(before),after_replies=len(after),
        checkpoint_replies=1,timeout_count=1 if blocked['return_code']==meta['ETIMEDOUT'] else 0,timeout_return_code=blocked['return_code'],
        timeout_duration_ns=duration,target_same_pid=all(event['target_pid']==cleanup['target_pid'] for event in events),target_received_count=len(audit),probe_samples=len(probes),probe_coverage=coverage,
        resume_to_first_reply_ns=(after[0]['end_ns'] if after else e['after_complete']['mono_ns'])-e['resume_requested']['mono_ns'],
        target_fault='CONTROLLED_PAUSE' if all(e[name]['target_state']=='stopped' for name in ('paused','timeout_observed','resume_requested')) else 'UNKNOWN',isolation_verdict='INCONCLUSIVE',system_service_probe=None,
        errors=errors,status='PASS' if not errors else 'FAIL')
    if write_summary:(folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary


def verify(folder):
    folder=Path(folder).resolve();manifest=read_json(folder/'manifest.json')
    for name,digest in manifest['evidence_hashes'].items():
        path=(folder/name).resolve()
        if path.parent!=folder or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Evidence hash mismatch: '+name)
    summary=analyze(folder,False)
    if summary!=read_json(folder/'summary.json') or summary['status']!='PASS':raise ValueError('Stall evidence failed')
    return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','analyze','verify'));p.add_argument('directory');args=p.parse_args()
    if args.action=='prepare':print(prepare(args.directory));return
    result=analyze(args.directory) if args.action=='analyze' else verify(args.directory)
    print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
