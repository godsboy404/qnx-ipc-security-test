"""Local handoff integrity and exclusion invariants, using synthetic files."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from ipcsec.handoff import safe_path,collect_files,write_bundle,verify_bundle,audit


class HandoffTests(unittest.TestCase):
    def setUp(self):
        scratch=Path(__file__).resolve().parents[1]/'build/test-tmp';scratch.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)

    def put(self,name,data='synthetic'):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(data,encoding='utf-8')

    def test_paths_cannot_escape_workspace(self):
        for name in ('../secret','D:/secret','/secret','native/../../secret','native\\secret'):
            with self.assertRaises(ValueError):safe_path(self.root,name)
        self.assertEqual(safe_path(self.root,'native/a.c'),self.root/'native/a.c')

    def test_keys_vm_build_and_private_runtime_are_excluded(self):
        for name in ('README.md','ipcsec/example.py','build/lab-keys/qnx-lab-ed25519',
            '.git/config','native/test.pem','native/build/private.txt','ipcsec/__pycache__/x.pyc',
            'release/.env','evidence/native-stall-runs/example/summary.json','evidence/native-runs/example/server.log'):
            self.put(name)
        files=collect_files(self.root)
        self.assertEqual(set(files),{'README.md','ipcsec/example.py','evidence/native-stall-runs/example/summary.json','evidence/native-runs/example/server.log'})

    def test_archive_retains_failure_and_detects_corruption(self):
        files={'README.md':b'synthetic source','evidence/native-stall-runs/failed/summary.json':b'{"status":"FAIL"}'}
        folder=write_bundle(self.root,dict(selected_evidence_status='PASS',course_gate='PENDING'),files)
        archive=folder/'qnx-ipc-security-test-handoff.zip'
        self.assertEqual(verify_bundle(archive),4)
        bad=self.root/'tampered.zip'
        with zipfile.ZipFile(archive) as source,zipfile.ZipFile(bad,'w') as dest:
            for name in source.namelist():
                content=source.read(name)
                if name.endswith('/README.md'):content=b'changed'
                dest.writestr(name,content)
        with self.assertRaises(ValueError):verify_bundle(bad)

    def test_unverifiable_selected_run_cannot_pass(self):
        self.put('configs/handoff-evidence.json',json.dumps(dict(selected=[dict(id='missing',kind='fuzz',path='evidence/missing')],comparison_paths=[],pending=['human_signoff'])))
        report=audit(self.root)
        self.assertEqual(report['selected_evidence_status'],'FAIL')
        self.assertEqual(report['course_gate'],'PENDING')
        with self.assertRaises(ValueError):write_bundle(self.root,report,{})

    def test_manifest_dependency_must_be_inside_archive(self):
        files={'evidence/native-runs/example/manifest.json':json.dumps(dict(hashes={'server.log':'0'*64})).encode()}
        with self.assertRaises(ValueError):write_bundle(self.root,dict(selected_evidence_status='PASS'),files)

    def test_model_artifact_dependency_cannot_be_omitted(self):
        files={'evidence/model-review-runs/example/integrity.json':
            json.dumps(dict(hashes={'K1/attempt-01/response.json':'0'*64})).encode()}
        with self.assertRaises(ValueError):write_bundle(self.root,dict(selected_evidence_status='PASS'),files)
