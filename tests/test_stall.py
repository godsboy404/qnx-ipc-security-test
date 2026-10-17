"""Synthetic timeout evidence calibration, not QNX run evidence."""
import json
import struct
import tempfile
import unittest
from pathlib import Path
from ipcsec.stall import prepare,analyze,EVENTS
from ipcsec.native import read_rows,read_json


class StallTests(unittest.TestCase):
    def setUp(self):
        scratch=Path(__file__).resolve().parents[1]/'build/test-tmp';scratch.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.tmp.cleanup)
        self.folder=prepare(Path(self.tmp.name)/'synthetic-stall')
        self.write('stall-meta.json',dict(backend='qnx-native',fault_kind='controlled_SIGSTOP',monitor_pid=1,SIGSTOP=19,SIGCONT=18,ETIMEDOUT=260))
        self.write('stall-cleanup.json',dict(complete=True,all_owned_children_reaped=True,device_present=False,monitor_pid=1,target_pid=2,probe_pid=3,before_client_pid=4,blocked_client_pid=5,after_client_pid=6))
        events=[]
        for i,(name,t) in enumerate(zip(EVENTS,(100,400,450,500,550,2700,2750,2800,3200))):
            stopped=i in (4,5,6)
            events.append(dict(event=name,mono_ns=t*1000000,monitor_pid=1,target_pid=2,
                client_pid={1:4,2:5,5:5,8:6}.get(i,0),target_state='stopped' if stopped else 'running',
                target_signal=0,device_present=None if stopped else True,target_stop_signal=19 if stopped else 0))
        self.rows('stall-events.jsonl',events)
        self.rows('stall-monitor.jsonl',[dict(phase=phase,mono_ns=t*1000000,monitor_pid=1,target_pid=2,probe_pid=3,probe_state='running')
            for phase,t in [('before',300),('blocked',1000),('blocked',2000),('after',3300)]])
        self.rows('os-probe.jsonl',[dict(probe_pid=3,begin_ns=t*1000000,end_ns=t*1000000+1,
            uname_rc=0,uname_errno=0,proc_stat_rc=0,proc_stat_errno=0,proc_is_directory=True)
            for t in (120,180,250,700,1200,1800,2500,2850,3000,3250)])
        wire=(struct.pack('<IIiI',1,4,0,0)+b'ping').hex();audit=[]
        for stage,pid,start in [('before',4,200),('after',6,2900)]:
            rows=[]
            for i in range(10):
                begin=(start+i*10)*1000000
                rows.append(dict(sequence=i+1,client_pid=pid,begin_ns=begin,end_ns=begin+5000000,return_code=0,reply_matches=True))
                audit.append(dict(sequence=len(audit)+1,target_pid=2,mono_ns=begin+1,dcmd_bytes=20,wire_hex=wire))
            self.rows(stage+'.jsonl',rows)
        audit.insert(10,dict(sequence=11,target_pid=2,mono_ns=510000001,dcmd_bytes=20,wire_hex=(struct.pack('<IIiI',1,4,0,0)+b'gate').hex()))
        for i,a in enumerate(audit):a['sequence']=i+1
        self.rows('target-audit.jsonl',audit)
        self.rows('stall-client-trace.jsonl',[dict(stage='connected',client_pid=5,mono_ns=440000000),
            dict(stage='checkpoint_request',client_pid=5,begin_ns=510000000,end_ns=540000000,return_code=0,reply_matches=True),
            dict(stage='before_devctl',mono_ns=590000000),dict(stage='devctl_returned',return_code=260,mono_ns=2600000000)])
        self.write('stall-ready.json',dict(client_pid=5,ready_ns=445000000))
        self.write('stall-request.json',dict(client_pid=5,begin_ns=600000000,end_ns=2600000000,configured_timeout_ns=2000000000,return_code=260,outcome='TIMEOUT'))
        self.write('host-execution.json',dict(host_watchdog_timeout=False,remote_exit_code=0))

    def write(self,name,value):
        (self.folder/name).write_text(json.dumps(value),encoding='utf-8')

    def rows(self,name,rows):
        (self.folder/name).write_text(''.join(json.dumps(row)+'\n' for row in rows),encoding='utf-8')

    def test_timeout_pass_is_not_crash_or_global_isolation(self):
        result=analyze(self.folder,False)
        self.assertEqual(result['status'],'PASS');self.assertEqual(result['target_fault'],'CONTROLLED_PAUSE')
        self.assertEqual(result['isolation_verdict'],'INCONCLUSIVE')
        self.assertFalse((self.folder/'summary.json').exists())

    def test_short_or_wrong_errno_timeout_rejected(self):
        row=read_json(self.folder/'stall-request.json');row['return_code']=110;row['end_ns']=1000000000
        self.write('stall-request.json',row)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_target_exit_cannot_be_called_pause(self):
        events=read_rows(self.folder/'stall-events.jsonl');events[5]['target_state']='signaled';events[5]['target_signal']=15
        self.rows('stall-events.jsonl',events)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_late_delivery_receiver_record_is_rejected(self):
        audit=read_rows(self.folder/'target-audit.jsonl');audit.append(dict(audit[-1],sequence=21))
        self.rows('target-audit.jsonl',audit)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_probe_must_span_paused_window(self):
        self.rows('os-probe.jsonl',[p for p in read_rows(self.folder/'os-probe.jsonl') if p['begin_ns']<550000000 or p['begin_ns']>2750000000])
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_same_pid_and_cleanup_required(self):
        events=read_rows(self.folder/'stall-events.jsonl');events[-1]['target_pid']=20
        self.rows('stall-events.jsonl',events)
        clean=read_json(self.folder/'stall-cleanup.json');clean['all_owned_children_reaped']=False
        self.write('stall-cleanup.json',clean)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_pause_watchdog_is_failure_not_timeout_success(self):
        clean=read_json(self.folder/'stall-cleanup.json');clean['pause_watchdog_triggered']=True
        self.write('stall-cleanup.json',clean)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_only_explicit_gate_request_is_checkpoint(self):
        audit=read_rows(self.folder/'target-audit.jsonl');audit[10]['wire_hex']=audit[0]['wire_hex']
        self.rows('target-audit.jsonl',audit)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_partial_run_fails_without_crash_inference(self):
        (self.folder/'after.jsonl').unlink()
        result=analyze(self.folder,False)
        self.assertEqual(result['status'],'FAIL');self.assertEqual(result['target_fault'],'UNKNOWN')
