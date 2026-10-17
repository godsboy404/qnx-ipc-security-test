import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ipcsec.model_calibration import fixtures, prepare, check_freeze, execute, verify


class ModelCalibrationTests(unittest.TestCase):
    def setUp(self):
        scratch = Path(__file__).resolve().parents[1]/'build/test-tmp'
        scratch.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)/'snapshot'

    def test_frozen_oracles_never_enter_model_request(self):
        prepare(self.folder)
        for file in self.folder.glob('*.request.json'):
            packet = json.loads(json.loads(file.read_text(encoding='utf-8'))['input'][1]['content'])
            self.assertNotIn('expected', packet)
            self.assertNotIn('oracle_author', packet)
        file = self.folder/'K1.packet.json'
        file.write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError): check_freeze(self.folder)

    def test_budget_and_unsafe_ids_rejected_before_creation(self):
        cases, answers = fixtures()
        cases['../escape'] = cases['K1']; answers['../escape'] = answers['K1']
        with self.assertRaises(ValueError): prepare(self.folder, cases, answers)
        self.assertFalse(self.folder.exists())
        cases = {str(i): cases['K1'] for i in range(11)}
        answers = {str(i): answers['K1'] for i in range(11)}
        with self.assertRaises(ValueError): prepare(self.folder, cases, answers)

    def test_three_failures_stop_and_no_hidden_retry(self):
        prepare(self.folder)
        with patch('ipcsec.model_calibration.call', side_effect=RuntimeError('synthetic')) as transport:
            report = execute(self.folder)
            self.assertEqual(transport.call_count, 3)
            self.assertEqual(report['technical_calibration'], 'FAIL')
            with self.assertRaises(FileExistsError): execute(self.folder)
            self.assertEqual(transport.call_count, 3)
        self.assertEqual(verify(self.folder), report)
        file = self.folder/'answers.json'
        file.write_text('{}', encoding='utf-8')
        with self.assertRaises(ValueError): verify(self.folder)
