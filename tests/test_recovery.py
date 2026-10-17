"""Synthetic controlled-recovery evidence; never treated as QNX observations."""
import json
import struct
import tempfile
import unittest
from pathlib import Path
from ipcsec.recovery import prepare,analyze,EVENTS
from ipcsec.native import read_rows,read_json


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        scratch=Path(__file__).resolve().parents[1]/'build/test-tmp';scratch.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.tmp.cleanup)
        self.folder=prepare(Path(self.tmp.name)/'synthetic-recovery')
        self.write('recovery-meta.json',dict(backend='qnx-native',fault_kind='controlled_SIGTERM',monitor_pid=1,SIGTERM=15,ENOENT=2))
        self.write('recovery-cleanup.json',dict(complete=True,all_owned_children_reaped=True,device_present=False,
            monitor_pid=1,first_target_pid=2,second_target_pid=3,probe_pid=4,before_client_pid=5,down_client_pid=6,after_client_pid=7))
        times=[100,400,500,600,700,1000,1100,1500];events=[]
        for i,(name,t) in enumerate(zip(EVENTS,times)):
            events.append(dict(event=name,mono_ns=t,monitor_pid=1,target_pid=2 if i<5 else (0 if i==5 else 3),
                client_pid={1:5,4:6,7:7}.get(i,0),target_state='signaled' if i in (3,4) else ('unknown' if i==5 else 'running'),
                target_signal=15 if i in (3,4) else 0,device_present=i not in (3,4,5)))
        self.rows('recovery-events.jsonl',events)
        self.rows('recovery-monitor.jsonl',[dict(phase=phase,mono_ns=t,monitor_pid=1,target_pid=pid,probe_pid=4,probe_state='running')
            for phase,t,pid in [('before',300,2),('down',800,2),('after',1600,3)]])
        self.rows('os-probe.jsonl',[dict(probe_pid=4,begin_ns=t,end_ns=t+1,uname_rc=0,uname_errno=0,proc_stat_rc=0,proc_stat_errno=0,proc_is_directory=True)
            for t in (120,150,250,650,750,800,1150,1250,1550)])
        wire=(struct.pack('<IIiI',1,4,0,0)+b'ping').hex()
        for stage,pid,target,start in [('before',5,2,200),('after',7,3,1200)]:
            self.rows(stage+'.jsonl',[dict(sequence=i+1,client_pid=pid,begin_ns=start+i*10,end_ns=start+i*10+5,return_code=0,reply_matches=True) for i in range(10)])
            self.rows('target-'+stage+'.jsonl',[dict(sequence=i+1,target_pid=target,mono_ns=start+i*10+1,dcmd_bytes=20,wire_hex=wire) for i in range(10)])
        self.rows('down.jsonl',[dict(client_pid=6,begin_ns=650,end_ns=660,open_succeeded=False,open_errno=2,ipc_sent=False)])
        self.write('host-execution.json',dict(host_watchdog_timeout=False,remote_exit_code=0))

    def write(self,name,value):
        (self.folder/name).write_text(json.dumps(value),encoding='utf-8')

    def rows(self,name,rows):
        (self.folder/name).write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')

    def test_recovery_pass_keeps_isolation_unknown(self):
        result=analyze(self.folder,False)
        self.assertEqual(result['status'],'PASS');self.assertEqual(result['isolation_verdict'],'INCONCLUSIVE')
        self.assertEqual(result['restart_to_first_reply_ns'],205)
        self.assertFalse((self.folder/'summary.json').exists())

    def test_timeout_cannot_replace_signal_observation(self):
        events=read_rows(self.folder/'recovery-events.jsonl');events[3]['target_state']='unknown';events[3]['target_signal']=0
        self.rows('recovery-events.jsonl',events)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_receiver_content_and_new_process_required(self):
        audit=read_rows(self.folder/'target-after.jsonl');audit[0]['wire_hex']='00'
        self.rows('target-after.jsonl',audit)
        cleanup=read_json(self.folder/'recovery-cleanup.json');cleanup['second_target_pid']=2
        self.write('recovery-cleanup.json',cleanup)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_probe_must_cover_actual_down_window(self):
        self.rows('os-probe.jsonl',[p for p in read_rows(self.folder/'os-probe.jsonl') if not 600<p['begin_ns']<1000])
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_absence_and_cleanup_are_required(self):
        down=read_rows(self.folder/'down.jsonl');down[0]['open_succeeded']=True
        self.rows('down.jsonl',down)
        cleanup=read_json(self.folder/'recovery-cleanup.json');cleanup['all_owned_children_reaped']=False
        self.write('recovery-cleanup.json',cleanup)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_partial_execution_and_host_deadline_fail(self):
        self.rows('after.jsonl',read_rows(self.folder/'after.jsonl')[:-1])
        self.write('host-execution.json',dict(host_watchdog_timeout=True,remote_exit_code=255))
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')
