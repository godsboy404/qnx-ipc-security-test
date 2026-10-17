"""Synthetic fixtures exercise evidence rejection; these are not QNX observations."""
import json
import tempfile
import unittest
from pathlib import Path
from ipcsec.native import prepare, prepare_replay, read_rows, read_json, analyze, corpus, encode_case


class NativeEvidenceTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1]/'build/test-tmp'
        scratch.mkdir(parents=True,exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.folder = prepare(Path(self.temp.name)/'synthetic',16)

    def write(self,name,value):
        (self.folder/name).write_text(json.dumps(value),encoding='utf-8')

    def fixture(self):
        rows=[]
        for c in read_rows(self.folder/'cases.jsonl'):
            valid=c['oracle_label']=='valid'
            rows.append(dict(case_id=c['case_id'],operation=1 if c['operation']=='ECHO' else 0xffffffff,
                declared_length=c['declared_length'],offset=c['offset'],flags=c['flags'],payload_hex=c['payload_hex'],
                backend='qnx-native',actual_payload_bytes=len(bytes.fromhex(c['payload_hex'])),
                outcome='REPLY' if valid else 'ERROR_REPLY',reply_matches=valid,
                return_code=0 if valid else 240,fuzzer_pid=3,begin_ns=100,end_ns=200))
        (self.folder/'fuzz-results.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
        self.write('monitor-summary.json',dict(monitor_pid=1,target_pid=2,worker_pid=3,peer_pid=4,
            watchdog_expired=False,worker_state='exited',worker_exit_code=0,
            target_state_before_cleanup='running',peer_state_before_cleanup='running'))
        (self.folder/'monitor.jsonl').write_text(json.dumps(dict(monitor_pid=1,target_pid=2,worker_pid=3,peer_pid=4,mono_ns=150))+'\n')
        (self.folder/'heartbeat.jsonl').write_text('\n'.join(json.dumps(dict(pid=4,mono_ns=t)) for t in (90,210)))
        self.write('monitor-selftest.json',dict(exit7_observed=True,sigterm_observed=True))
        self.write('fuzzer-meta.json',dict(EINVAL=22,EMSGSIZE=240))
        self.write('cleanup.json',dict(target_reaped=True,worker_reaped=True,peer_reaped=True,device_present=False))

    def test_bounds_and_determinism(self):
        self.assertEqual(corpus(128),corpus(128))
        self.assertLess(len(encode_case(corpus(16)[5])),200)
        for n in (0,201):
            with self.assertRaises(ValueError):corpus(n)
        with self.assertRaises(ValueError):prepare(self.folder,16)

    def test_qnx_errno_and_read_only_analysis(self):
        self.fixture()
        self.assertEqual(analyze(self.folder,False)['status'],'PASS')
        self.assertFalse((self.folder/'summary.json').exists())
        self.write('fuzzer-meta.json',dict(EINVAL=22,EMSGSIZE=90))
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_partial_results_rejected(self):
        self.fixture()
        p=self.folder/'fuzz-results.jsonl'
        p.write_text('\n'.join(p.read_text().splitlines()[:-1]))
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_observer_identity_and_cleanup_rejected(self):
        self.fixture()
        self.write('cleanup.json',dict(target_reaped=False,worker_reaped=True,peer_reaped=True,device_present=True))
        monitor=read_json(self.folder/'monitor-summary.json');monitor['peer_pid']=2
        self.write('monitor-summary.json',monitor)
        self.assertEqual(analyze(self.folder,False)['status'],'FAIL')

    def test_replay_preserves_fields_and_rejects_tampering(self):
        dest=Path(self.temp.name)/'replay'
        prepare_replay(self.folder,dest,'NF-0004')
        original=read_rows(self.folder/'cases.jsonl')[4]
        self.assertEqual(read_rows(dest/'cases.jsonl'),[original])
        cases=read_rows(self.folder/'cases.jsonl');cases[4]['flags']=7
        (self.folder/'cases.jsonl').write_text(''.join(json.dumps(c)+'\n' for c in cases))
        with self.assertRaises(ValueError):prepare_replay(self.folder,Path(self.temp.name)/'bad','NF-0004')
