import copy
import unittest
from ipcsec.claim_audit import assess, build_report


class ClaimAuditTests(unittest.TestCase):
    def setUp(self):
        self.summary = dict(mode='defense', invalid_cases=1, blocked_count=1,
            forwarded_count=1, target_received_count=1)
        self.cases = [dict(case_id='bad', oracle_label='invalid'), dict(case_id='good', oracle_label='valid')]
        self.rows = [dict(case_id='bad', decision='BLOCK', forwarded=False, outcome='NOT_SENT'),
            dict(case_id='good', decision='ALLOW', forwarded=True, outcome='REPLY')]

    def test_forwarded_invalid_request_is_a_counterexample(self):
        self.assertTrue(all(assess(self.summary, self.cases, self.rows).values()))
        rows = copy.deepcopy(self.rows)
        rows[0].update(decision='ALLOW', forwarded=True, outcome='ERROR_REPLY')
        self.assertFalse(assess(self.summary, self.cases, rows)['all_invalid_blocked_without_send'])

    def test_duplicate_or_missing_rows_cannot_pass(self):
        for rows in (self.rows[:1], self.rows + self.rows[:1]):
            self.assertFalse(assess(self.summary, self.cases, rows)['case_ids_unique_and_aligned'])

    def test_empty_invalid_set_does_not_vacuously_pass(self):
        checks = assess(self.summary, self.cases[1:], self.rows[1:])
        self.assertFalse(checks['nonempty_invalid_sample'])

    def test_registered_report_preserves_authority_and_isolation_limits(self):
        report = build_report()
        self.assertEqual(report['criteria']['SEC-03']['local_result'], 'PASS')
        self.assertEqual(report['criteria']['OBS-01']['local_result'], 'PASS')
        self.assertEqual(report['criteria']['ISO-01']['local_result'], 'INSUFFICIENT_EVIDENCE')
        self.assertEqual(report['criteria']['SEC-03']['observed']['blocked'], 94)
        self.assertEqual(report['human_signoff'], 'pending')
        self.assertFalse(report['independent_reproduction'])
