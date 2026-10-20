import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ipcsec.model import Case
from ipcsec.runner import run,ROOT
from ipcsec.simulation_evidence import verify


class SimulationEvidenceTests(unittest.TestCase):
    def setUp(self):
        scratch=ROOT/'build/test-tmp';scratch.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        for name in ('README.md','AGENTS.md','pyproject.toml'):shutil.copyfile(ROOT/name,self.root/name)
        cfg=json.loads((ROOT/'configs/lab.json').read_text(encoding='utf-8'))
        with patch('ipcsec.runner.ROOT',self.root):
            self.folder=run([Case('good'),Case('invalid',declared_length=65)],cfg,'EXP-03-defense',True)

    def test_raw_run_reanalysis_and_summary(self):
        summary,manifest=verify(self.folder)
        self.assertEqual(summary['total'],2)
        self.assertIsNone(summary['isolation_success_rate'])
        self.assertEqual(manifest['backend'],'simulation')

    def test_forged_summary_rejected_even_after_rehash(self):
        path=self.folder/'summary.json'
        data=json.loads(path.read_text());data['total']=999
        path.write_text(json.dumps(data),encoding='utf-8')
        manifest_path=self.folder/'manifest.json';manifest=json.loads(manifest_path.read_text())
        manifest['evidence_hashes']['summary.json']=hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest),encoding='utf-8')
        with self.assertRaises(ValueError):verify(self.folder)
