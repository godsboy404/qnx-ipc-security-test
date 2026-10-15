import unittest
import json
from dataclasses import replace
from ipcsec.model import Case
from ipcsec.defense import Defense
from ipcsec.monitor import isolation_verdict, unknown_probes
from ipcsec.harness import QnxTransport
from ipcsec.metrics import summarize
from ipcsec.evaluator import review
from ipcsec.runner import ROOT, oracle, run
from ipcsec.fuzzer import generate

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads((ROOT/'configs/lab.json').read_text(encoding='utf-8'))

    def test_boundaries_and_actual_length(self):
        d = Defense(self.cfg)
        for length in (0,1,63,64):
            c = Case(str(length),declared_length=length,payload_hex='61'*length)
            self.assertEqual(d.decide(c,length*1000)[0],'ALLOW')
        for c in (Case('bad',declared_length=65,payload_hex='61'*65),
                  Case('mismatch',declared_length=64),Case('negative',offset=-1)):
            self.assertEqual(d.decide(c,999999)[0],'BLOCK')

    def test_rate_window_and_session_independence(self):
        d = Defense(self.cfg)
        c = Case('rate')
        for i in range(10): self.assertEqual(d.decide(c,0)[0],'ALLOW')
        self.assertEqual(d.decide(c,0)[0],'RATE_LIMIT')
        self.assertEqual(d.decide(replace(c,session_id='other'),0)[0],'ALLOW')
        self.assertEqual(d.decide(c,1000)[0],'ALLOW')

    def test_unknown_does_not_prove_isolation(self):
        self.assertEqual(isolation_verdict(unknown_probes()),'INCONCLUSIVE')
        probes = dict.fromkeys(unknown_probes(),True)
        self.assertEqual(isolation_verdict(probes),'PASS')
        probes['peer_ok'] = False
        self.assertEqual(isolation_verdict(probes),'FAIL')

    def test_empty_denominators_are_not_zero_success(self):
        self.assertIsNone(summarize([])['false_positive_rate'])
        self.assertIsNone(summarize([])['isolation_success_rate'])

    def test_reproducible_corpus_and_three_mutations(self):
        self.assertEqual(generate(100),generate(100))
        self.assertEqual({c.mutation for c in generate(100)}, {'normal','boundary','field','combination'})

    def test_blocked_invalid_never_reaches_target(self):
        # Contract oracle is independent; all invalid generated inputs must be rejected.
        d = Defense(self.cfg)
        for i,c in enumerate(generate(100)):
            if oracle(c)=='invalid': self.assertEqual(d.decide(c,i*1000)[0],'BLOCK')

    def test_scope_gate_precedes_execution(self):
        cfg = dict(self.cfg,target_id='unregistered')
        with self.assertRaises(PermissionError): run([Case('x')],cfg,'denied')

    def test_native_cannot_silently_fallback(self):
        with self.assertRaises(NotImplementedError): QnxTransport().send(Case('x'))

    def test_calibration_and_wrong_version(self):
        for f in json.loads((ROOT/'eval/calibration/k1-k6.json').read_text(encoding='utf-8')):
            self.assertEqual(review(f)['status'],f['expected'])
        self.assertEqual(review(dict(criterion_id='x',evidence_exists=True,same_version=False,observed='supports'))['status'],
                         'INSUFFICIENT_EVIDENCE')

if __name__ == '__main__': unittest.main()
