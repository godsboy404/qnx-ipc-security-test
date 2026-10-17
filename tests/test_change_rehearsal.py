import json
import unittest
from ipcsec.runner import ROOT
from ipcsec.change_rehearsal import corpus,evaluate,analyze
from ipcsec.defense import Defense
from ipcsec.model import Case
from ipcsec.native import policy_expectations


class ChangeRehearsalTests(unittest.TestCase):
    def setUp(self):
        baseline=json.loads((ROOT/'configs/lab.json').read_text(encoding='utf-8'))
        self.configs=dict(baseline=baseline,candidate=dict(baseline,max_requests_per_window=5),rollback=dict(baseline))
        self.events=corpus()
        self.profiles={name:evaluate(self.events,cfg) for name,cfg in self.configs.items()}

    def test_fifth_sixth_expiry_sessions_invalid_and_rollback(self):
        rows={r['case_id']:r for r in self.profiles['candidate']}
        for name in ('A-05','B-independent','A-at-expiry','C-5'):
            self.assertEqual(rows[name]['decision'],'ALLOW')
        for name in ('A-06','A-before-expiry','C-6'):
            self.assertEqual(rows[name]['decision'],'RATE_LIMIT')
        for name in ('A-invalid','C-invalid'):
            self.assertEqual(rows[name]['decision'],'BLOCK')
            self.assertEqual(rows[name]['target_outcome'],'NOT_SENT')
        self.assertEqual(self.profiles['baseline'],self.profiles['rollback'])
        self.assertEqual(analyze(self.events,self.configs,self.profiles)['status'],'PASS')

    def test_forged_outcome_or_extra_config_delta_rejected(self):
        self.profiles['candidate'][0]['target_outcome']='NOT_SENT'
        self.assertEqual(analyze(self.events,self.configs,self.profiles)['status'],'FAIL')
        self.configs['candidate']['window_ms']=500
        with self.assertRaises(ValueError):analyze(self.events,self.configs,self.profiles)

    def test_rejected_arrival_does_not_prolong_window_for_5_or_10(self):
        for limit in (5,10):
            cfg=dict(self.configs['baseline'],max_requests_per_window=limit)
            defense=Defense(cfg)
            case=Case('rate')
            decisions=[defense.decide(case,t)[0] for t in [0]*limit+[900]+[1000]*limit]
            self.assertEqual(decisions,['ALLOW']*limit+['RATE_LIMIT']+['ALLOW']*limit)

    def test_original_21_case_counterexample_matches_native_oracle(self):
        times=[0]*10+[900]+[1000]*10
        cases=[Case(str(i)).record() for i in range(len(times))]
        native=policy_expectations(cases,[dict(begin_ns=t*1000000) for t in times],
                                   dict(mode='defense',authorization='allow'))
        defense=Defense(self.configs['baseline'])
        actual=[defense.decide(Case(**case),time)[0] for case,time in zip(cases,times)]
        self.assertEqual(actual,['ALLOW']*10+['RATE_LIMIT']+['ALLOW']*10)
        self.assertEqual(actual,native)
