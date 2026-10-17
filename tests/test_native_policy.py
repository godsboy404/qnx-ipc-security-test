"""Synthetic calibration and evidence corruption tests; no QNX claims."""
import json
import struct
import tempfile
import unittest
from pathlib import Path
from ipcsec.model import Case
from ipcsec.native import (prepare_policy, prepare_replay, read_rows, read_json,
    encode_policy_case, policy_expectations, analyze, AUTH_CONTENT, authorization_allowed)


class NativePolicyTests(unittest.TestCase):
    def setUp(self):
        scratch=Path(__file__).resolve().parents[1]/'build/test-tmp'
        scratch.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.folder=Path(self.tmp.name)/'fixture'

    def write(self,name,value):
        (self.folder/name).write_text(json.dumps(value),encoding='utf-8')

    def jsonl(self,name,rows):
        (self.folder/name).write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')

    def fixture(self,authorization_control=False):
        prepare_policy(self.folder,count=16,suite='authorization' if authorization_control else 'mixed')
        cases=read_rows(self.folder/'cases.jsonl');meta=read_json(self.folder/'corpus-meta.json')
        rows=[dict(begin_ns=100+i*1000,end_ns=200+i*1000) for i in range(len(cases))]
        decisions=policy_expectations(cases,rows,meta);audit=[]
        for index,(c,r,d) in enumerate(zip(cases,rows,decisions)):
            sent=d=='ALLOW'
            r.update(case_id=c['case_id'],operation=1 if c['operation']=='ECHO' else 0xffffffff,
                declared_length=c['declared_length'],offset=c['offset'],flags=c['flags'],payload_hex=c['payload_hex'],
                backend='qnx-native',fuzzer_pid=3,actual_payload_bytes=len(bytes.fromhex(c['payload_hex'])),
                decision=d,forwarded=sent,authorized=authorization_allowed(meta,index),session_index=0,delay_before_ms=0,
                outcome='REPLY' if sent else 'NOT_SENT',return_code=0 if sent else -1,reply_matches=sent)
            if sent:
                wire=struct.pack('<IIiI',r['operation'],r['declared_length'],r['offset'],r['flags'])+bytes.fromhex(r['payload_hex'])
                audit.append(dict(sequence=len(audit)+1,target_pid=2,mono_ns=r['begin_ns']+1,dcmd_bytes=len(wire),wire_hex=wire.hex()))
        self.jsonl('fuzz-results.jsonl',rows);self.jsonl('target-audit.jsonl',audit)
        self.write('monitor-summary.json',dict(monitor_pid=1,target_pid=2,worker_pid=3,peer_pid=4,
            watchdog_expired=False,worker_state='exited',worker_exit_code=0,
            target_state_before_cleanup='running',peer_state_before_cleanup='running'))
        self.jsonl('monitor.jsonl',[dict(monitor_pid=1,target_pid=2,worker_pid=3,peer_pid=4,mono_ns=150)])
        self.jsonl('heartbeat.jsonl',[dict(pid=4,mono_ns=t) for t in (90,17000)])
        self.write('monitor-selftest.json',dict(exit7_observed=True,sigterm_observed=True))
        self.write('fuzzer-meta.json',dict(EINVAL=22,EMSGSIZE=240,schema_version=2,defense_enabled=True))
        self.write('cleanup.json',dict(target_reaped=True,worker_reaped=True,peer_reaped=True,device_present=False))
        self.write('policy-selftest.json',dict(passed=True))
        if authorization_control:
            self.jsonl('authorization-events.jsonl',[dict(sequence=i+1,monitor_pid=1,state=state,
                content_hex=AUTH_CONTENT[state].hex(),file_present=state!='missing',applied_ns=rows[i]['begin_ns']-1)
                for i,state in enumerate(meta['authorization_states'])])

    def test_exact_window_and_session_independence(self):
        cases=[dict(Case(str(i)).record(),oracle_label='valid') for i in range(14)]
        cases[11]['session_id']='session-02'
        rows=[dict(begin_ns=100) for _ in cases]
        rows[10]['begin_ns']=1000000099
        rows[12]['begin_ns']=1000000100
        rows[13]['begin_ns']=1000000101
        decisions=policy_expectations(cases,rows,dict(mode='defense',authorization='allow'))
        self.assertEqual(decisions,['ALLOW']*10+['RATE_LIMIT','ALLOW','ALLOW','ALLOW'])

    def test_deny_precedes_invalid_and_baseline(self):
        cases=[dict(Case('X',flags=8).record(),oracle_label='invalid')]
        self.assertEqual(policy_expectations(cases,[dict(begin_ns=1)],dict(mode='baseline',authorization='deny')),['SCOPE_DENY'])
        self.assertEqual(policy_expectations(cases,[dict(begin_ns=1)],dict(mode='defense',authorization='allow')),['BLOCK'])

    def test_receiver_count_and_content_are_required(self):
        self.fixture()
        self.assertEqual(analyze(self.folder,False)['status'],'PASS')
        audit=read_rows(self.folder/'target-audit.jsonl')
        audit[0]['wire_hex']='00';self.jsonl('target-audit.jsonl',audit)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')
        self.jsonl('target-audit.jsonl',[])
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_forged_policy_decision_is_rejected(self):
        self.fixture()
        rows=read_rows(self.folder/'fuzz-results.jsonl');rows[4]['forwarded']=True
        self.jsonl('fuzz-results.jsonl',rows)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_schedule_and_replay(self):
        prepare_policy(self.folder,suite='rate')
        meta=read_json(self.folder/'corpus-meta.json')
        self.assertEqual(meta['count'],24);self.assertEqual(sum(meta['delays_ms']),1100)
        cases=read_rows(self.folder/'cases.jsonl')
        rows=[dict(begin_ns=i*10000000+(1100000000 if i>=12 else 0)) for i in range(24)]
        self.assertEqual(policy_expectations(cases,rows,meta),['RATE_LIMIT' if i in (10,22) else 'ALLOW' for i in range(24)])
        dest=Path(self.tmp.name)/'replay'
        prepare_replay(self.folder,dest,'NR-0011')
        self.assertEqual(read_rows(dest/'cases.jsonl')[0]['session_id'],'session-02')
        self.assertEqual((dest/'defense-mode.txt').read_bytes(),b'defense\n')
        with self.assertRaises(ValueError):encode_policy_case(Case('X',session_id='arbitrary'))

    def test_dynamic_revocation_and_cached_permission_rejection(self):
        self.fixture(True)
        summary=analyze(self.folder,False)
        self.assertEqual(summary['status'],'PASS')
        self.assertEqual((summary['forwarded_count'],summary['scope_denied_count']),(8,16))
        rows=read_rows(self.folder/'fuzz-results.jsonl');rows[4]['authorized']=True
        self.jsonl('fuzz-results.jsonl',rows)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_external_event_causality_and_content_required(self):
        self.fixture(True)
        events=read_rows(self.folder/'authorization-events.jsonl')
        events[4]['applied_ns']=999999
        events[8]['file_present']=True
        self.jsonl('authorization-events.jsonl',events)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_revoked_case_replay_preserves_selected_state(self):
        prepare_policy(self.folder,suite='authorization')
        dest=Path(self.tmp.name)/'revoked-replay'
        prepare_replay(self.folder,dest,'NA-0008')
        self.assertEqual(read_json(dest/'corpus-meta.json')['authorization_states'],['missing'])
        self.assertEqual((dest/'authorization-plan.txt').read_bytes(),b'missing\n')
        self.assertEqual((dest/'defense-mode.txt').read_bytes(),b'defense-auth\n')
