import json
import math
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ipcsec.local_check import run, verify, sha, save, STEPS


class LocalCheckTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1] / 'build/test-tmp'
        scratch.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('AGENTS.md', 'pyproject.toml'):
            (self.root / name).write_text('synthetic', encoding='utf-8')

    def successful(self, command, **kwargs):
        self.assertFalse(kwargs['shell'])
        self.assertEqual(kwargs['timeout'], 60)
        kwargs['stdout'].write(b'Synthetic test output\n')
        if 'ipcsec.claim_audit' in command:
            Path(command[-1]).write_text('{}', encoding='utf-8')
        return subprocess.CompletedProcess(command, 0)

    def test_success_never_claims_peer_or_native_execution(self):
        with patch('ipcsec.local_check.subprocess.run', side_effect=self.successful):
            folder, report = run(self.root)
        self.assertEqual(len(report['steps']), len(STEPS))
        self.assertEqual(verify(folder)['status'], 'PASS')
        self.assertFalse(report['peer_reproduced'])
        self.assertFalse(report['qnx_live_execution'])

    def test_failure_stops_without_retry_and_is_verifiable(self):
        with patch('ipcsec.local_check.subprocess.run', return_value=subprocess.CompletedProcess([], 7)) as call:
            folder, report = run(self.root)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(report['steps'][0]['exit_code'], 7)
        self.assertEqual(verify(folder)['status'], 'FAIL')

    def test_timeout_is_not_success_or_crash(self):
        with patch('ipcsec.local_check.subprocess.run', side_effect=subprocess.TimeoutExpired([], 60)):
            folder, report = run(self.root)
        self.assertTrue(report['steps'][0]['timed_out'])
        self.assertIsNone(report['steps'][0]['exit_code'])
        self.assertEqual(verify(folder)['status'], 'FAIL')

    def test_rehashed_false_pass_is_rejected(self):
        with patch('ipcsec.local_check.subprocess.run', return_value=subprocess.CompletedProcess([], 1)):
            folder, report = run(self.root)
        report['status'] = 'PASS'
        save(folder / 'summary.json', report)
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        manifest['evidence_hashes']['summary.json'] = sha(folder / 'summary.json')
        save(folder / 'manifest.json', manifest)
        with self.assertRaises(ValueError):
            verify(folder)

    def test_elapsed_ms_accepts_zero_and_fraction(self):
        with patch('ipcsec.local_check.subprocess.run', side_effect=self.successful):
            folder, report = run(self.root)
        report['steps'][0]['elapsed_ms'] = 0
        report['steps'][1]['elapsed_ms'] = 1.25
        save(folder / 'summary.json', report)
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        manifest['evidence_hashes']['summary.json'] = sha(folder / 'summary.json')
        save(folder / 'manifest.json', manifest)
        self.assertEqual(verify(folder)['status'], 'PASS')

    def test_rehashed_invalid_elapsed_ms_is_rejected(self):
        with patch('ipcsec.local_check.subprocess.run', side_effect=self.successful):
            folder, report = run(self.root)
        report['steps'][0]['elapsed_ms'] = math.inf
        save(folder / 'summary.json', report)
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        manifest['evidence_hashes']['summary.json'] = sha(folder / 'summary.json')
        save(folder / 'manifest.json', manifest)
        with self.assertRaisesRegex(ValueError, 'Invalid elapsed_ms'):
            verify(folder)

    def test_rehashed_boolean_elapsed_ms_is_rejected(self):
        with patch('ipcsec.local_check.subprocess.run', side_effect=self.successful):
            folder, report = run(self.root)
        report['steps'][0]['elapsed_ms'] = True
        save(folder / 'summary.json', report)
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        manifest['evidence_hashes']['summary.json'] = sha(folder / 'summary.json')
        save(folder / 'manifest.json', manifest)
        with self.assertRaisesRegex(ValueError, 'Invalid elapsed_ms'):
            verify(folder)

    def test_rehashed_invalid_elapsed_ms_values_are_rejected(self):
        invalid_values = (-1, False, '1', None, math.nan, math.inf, -math.inf)
        with patch('ipcsec.local_check.subprocess.run', side_effect=self.successful):
            folder, report = run(self.root)
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        for value in invalid_values:
            report['steps'][0]['elapsed_ms'] = value
            save(folder / 'summary.json', report)
            manifest['evidence_hashes']['summary.json'] = sha(folder / 'summary.json')
            save(folder / 'manifest.json', manifest)
            with self.subTest(value=repr(value)):
                with self.assertRaisesRegex(ValueError, 'Invalid elapsed_ms'):
                    verify(folder)

    def test_rehashed_large_integer_elapsed_ms_is_accepted(self):
        with patch('ipcsec.local_check.subprocess.run', side_effect=self.successful):
            folder, report = run(self.root)
        report['steps'][0]['elapsed_ms'] = 10 ** 400
        save(folder / 'summary.json', report)
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        manifest['evidence_hashes']['summary.json'] = sha(folder / 'summary.json')
        save(folder / 'manifest.json', manifest)
        self.assertEqual(verify(folder)['status'], 'PASS')
