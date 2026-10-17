"""Evidence checks for a controlled stop/restart of our own QNX service."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from .native import read_json,read_rows

EVENTS=['ready','before_complete','stop_requested','stopped','unavailable_observed',
        'restart_requested','restarted','after_complete']


def prepare(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    if any(folder.iterdir()):raise ValueError('Never overwrite recovery evidence')
    config=dict(backend='qnx-native',target_id='lab-resmgr-01',device='/dev/ipcsec-lab',
        fault_kind='controlled_SIGTERM',before_count=10,after_count=10,down_open_count=1,
        ipc_deadline_seconds=2,monitor_deadline_seconds=15,host_deadline_seconds=45,
        probe_scope='independent uname and read-only /proc stat, not global system health')
    (folder/'recovery-config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    return folder


def analyze(folder,write_summary=True):
    folder=Path(folder);config=read_json(folder/'recovery-config.json')
    meta=read_json(folder/'recovery-meta.json');cleanup=read_json(folder/'recovery-cleanup.json')
    events=read_rows(folder/'recovery-events.jsonl');samples=read_rows(folder/'recovery-monitor.jsonl')
    probes=read_rows(folder/'os-probe.jsonl');before=read_rows(folder/'before.jsonl')
    after=read_rows(folder/'after.jsonl');down=read_rows(folder/'down.jsonl')
    errors=[]
    if config['fault_kind']!='controlled_SIGTERM' or meta['fault_kind']!=config['fault_kind'] or meta['backend']!='qnx-native' or config['target_id']!='lab-resmgr-01' or config['device']!='/dev/ipcsec-lab':
        errors.append('unexpected backend or fault kind')
    if [e['event'] for e in events]!=EVENTS:raise ValueError('Incomplete or reordered recovery events')
    e=dict(zip(EVENTS,events))
    if any(b['mono_ns']<a['mono_ns'] for a,b in zip(events,events[1:])):errors.append('event clock regressed')
    if any(row['monitor_pid']!=meta['monitor_pid'] for row in events+samples):errors.append('monitor identity mismatch')
    if not cleanup['complete'] or not cleanup['all_owned_children_reaped'] or cleanup['device_present']:
        errors.append('recovery or cleanup incomplete')
    roles=[cleanup[k] for k in ('monitor_pid','first_target_pid','second_target_pid','probe_pid','before_client_pid','down_client_pid','after_client_pid')]
    if len(set(roles))!=7 or any(pid<=0 for pid in roles) or cleanup['monitor_pid']!=meta['monitor_pid']:
        errors.append('process identities missing or not distinct')
    if e['stopped']['target_state']!='signaled' or e['stopped']['target_signal']!=meta['SIGTERM'] or e['stopped']['device_present']:
        errors.append('controlled SIGTERM exit not independently observed')
    for name in ('ready','before_complete','stop_requested'):
        if e[name]['target_pid']!=cleanup['first_target_pid'] or e[name]['target_state']!='running':errors.append('initial target identity/state mismatch')
    for name in ('restarted','after_complete'):
        if e[name]['target_pid']!=cleanup['second_target_pid'] or e[name]['target_state']!='running' or not e[name]['device_present']:
            errors.append('restarted target identity/state mismatch')
    if e['stopped']['target_pid']!=cleanup['first_target_pid'] or e['unavailable_observed']['device_present']:
        errors.append('unavailable target observation mismatch')
    for name,key in [('before_complete','before_client_pid'),('unavailable_observed','down_client_pid'),('after_complete','after_client_pid')]:
        if e[name]['client_pid']!=cleanup[key]:errors.append('event client identity mismatch')
    wire=struct.pack('<IIiI',1,4,0,0)+b'ping'
    for stage,rows,target_pid,client_pid in (
        ('before',before,cleanup['first_target_pid'],cleanup['before_client_pid']),
        ('after',after,cleanup['second_target_pid'],cleanup['after_client_pid'])):
        audit=read_rows(folder/f'target-{stage}.jsonl')
        if len(rows)!=10 or len(audit)!=10:errors.append(stage+': incomplete request/receiver records')
        for i,(r,a) in enumerate(zip(rows,audit)):
            if r['sequence']!=i+1 or r['client_pid']!=client_pid or r['return_code']!=0 or not r['reply_matches'] or r['begin_ns']>r['end_ns']:
                errors.append(stage+': request identity/reply mismatch')
            if a['sequence']!=i+1 or a['target_pid']!=target_pid or a['wire_hex']!=wire.hex() or a['dcmd_bytes']!=len(wire) or not r['begin_ns']<=a['mono_ns']<=r['end_ns']:
                errors.append(stage+': receiver identity/content/time mismatch')
        if rows and (rows[0]['begin_ns']<e['ready' if stage=='before' else 'restarted']['mono_ns'] or rows[-1]['end_ns']>e[stage+'_complete']['mono_ns']):
            errors.append(stage+': requests outside observed phase')
    if len(down)!=1 or any(r['client_pid']!=cleanup['down_client_pid'] or r['open_succeeded'] or r['ipc_sent'] or r['open_errno']!=meta['ENOENT'] or not e['stopped']['mono_ns']<=r['begin_ns']<=r['end_ns']<=e['unavailable_observed']['mono_ns'] for r in down):
        errors.append('device absence not independently confirmed by client')
    if not samples or any(s['probe_pid']!=cleanup['probe_pid'] or s['probe_state']!='running' for s in samples):
        errors.append('independent probe lifecycle incomplete')
    if any(b['mono_ns']<a['mono_ns'] for a,b in zip(samples,samples[1:])) or any(s['target_pid'] not in (cleanup['first_target_pid'],cleanup['second_target_pid']) for s in samples):
        errors.append('monitor clock or target identity mismatch')
    if not probes or any(p['probe_pid']!=cleanup['probe_pid'] or p['uname_rc']!=0 or p['uname_errno']!=0 or p['proc_stat_rc']!=0 or p['proc_stat_errno']!=0 or not p['proc_is_directory'] or p['begin_ns']>p['end_ns'] for p in probes):
        errors.append('read-only OS probe failed or identity mismatched')
    if any(b['begin_ns']<=a['end_ns'] for a,b in zip(probes,probes[1:])):errors.append('probe clock/order invalid')
    coverage={}
    for phase,left,right in [('before',e['ready']['mono_ns'],e['stop_requested']['mono_ns']),
        ('down',e['stopped']['mono_ns'],e['restart_requested']['mono_ns']),
        ('after',e['restarted']['mono_ns'],samples[-1]['mono_ns'] if samples else 0)]:
        coverage[phase]=sum(left<=p['begin_ns'] and p['end_ns']<=right for p in probes)
        if coverage[phase]<2:errors.append('insufficient OS probe coverage: '+phase)
    host=read_json(folder/'host-execution.json')
    if host['host_watchdog_timeout'] or host['remote_exit_code']!=0:errors.append('host deadline or remote execution failure')
    first_reply=after[0]['end_ns'] if after else e['after_complete']['mono_ns']
    summary=dict(backend='qnx-native',fault_kind='controlled_SIGTERM',before_replies=len(before),after_replies=len(after),
        down_open_errno=down[0]['open_errno'] if down else None,probe_samples=len(probes),probe_coverage=coverage,
        stop_to_first_reply_ns=first_reply-e['stop_requested']['mono_ns'],
        restart_to_first_reply_ns=first_reply-e['restart_requested']['mono_ns'],
        observed_down_hold_ns=e['restart_requested']['mono_ns']-e['stopped']['mono_ns'],
        recovery_verdict='PASS' if not errors else 'FAIL',isolation_verdict='INCONCLUSIVE',
        system_service_probe=None,probe_scope=config['probe_scope'],errors=errors,status='PASS' if not errors else 'FAIL')
    if write_summary:(folder/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    return summary


def verify(folder):
    folder=Path(folder).resolve();manifest=read_json(folder/'manifest.json')
    for name,digest in manifest['evidence_hashes'].items():
        path=(folder/name).resolve()
        if path.parent!=folder or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('Evidence hash mismatch: '+name)
    summary=analyze(folder,False)
    if summary!=read_json(folder/'summary.json') or summary['status']!='PASS':raise ValueError('Recovery evidence failed')
    return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','analyze','verify'));p.add_argument('directory')
    args=p.parse_args()
    if args.action=='prepare':print(prepare(args.directory));return
    result=analyze(args.directory) if args.action=='analyze' else verify(args.directory)
    print(json.dumps(result,indent=2))
    if result['status']!='PASS':raise SystemExit(1)

if __name__=='__main__':main()
