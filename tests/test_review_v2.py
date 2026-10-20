import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ipcsec.model_calibration import fixtures
from ipcsec.review_contract_v2 import fixture_from_v1,validate_packet,validate_review,sha_text
from ipcsec.registered_review import build_packet,bounded_file
from ipcsec.semantic_review import call,build_request

ROOT=Path(__file__).resolve().parents[1]


class ReviewV2Tests(unittest.TestCase):
    def setUp(self):
        cases,_=fixtures()
        self.packet=fixture_from_v1(cases['K1'],'K1')
        self.review=dict(schema_version=2,criterion_id='SEC-03',scope=self.packet['scope'],status='PASS',
            evidence_ids=['excerpt-1'],evidence_level='OBSERVED',evidence_sources=['fixture_demo'],
            backends=['fixture'],missing_evidence=[],suggested_check='Independent verification pending',
            score_suggestion=None,human_signoff='pending')

    def test_backend_source_and_strength_are_independent(self):
        validate_review(self.packet,self.review)
        for update in (dict(evidence_level='qnx_native'),dict(evidence_level='REPRODUCED'),
                       dict(evidence_sources=['teacher_runner']),dict(backends=['qnx_native']),
                       dict(evidence_ids=['invented']),dict(human_signoff='approved')):
            with self.assertRaises(ValueError):validate_review(self.packet,dict(self.review,**update))

    def test_mixed_strength_uses_weakest_cited_item(self):
        item=copy.deepcopy(self.packet['evidence'][0]);item.update(id='static',verification_level='STATIC')
        self.packet['evidence'].append(item)
        self.review['evidence_ids'].append('static')
        with self.assertRaises(ValueError):validate_review(self.packet,self.review)
        self.review['evidence_level']='STATIC'
        validate_review(self.packet,self.review)

    def test_claim_only_cannot_pass_and_stale_ids_are_quarantined(self):
        cases,_=fixtures()
        packet=fixture_from_v1(cases['K5'],'K5')
        review=dict(self.review,criterion_id=packet['criterion_id'],scope=packet['scope'],evidence_level='CLAIM_ONLY')
        with self.assertRaises(ValueError):validate_review(packet,review)
        packet=fixture_from_v1(cases['V1-stale'],'V1-stale')
        self.assertEqual(packet['evidence'],[])
        self.assertEqual(packet['excluded_evidence'][0]['reason'],'source_version_mismatch')
        with self.assertRaises(ValueError):validate_review(packet,dict(review,scope=packet['scope']))

    def test_false_approval_and_edited_excerpt_rejected(self):
        self.packet['evidence'][0]['excerpt']+=' modified'
        with self.assertRaises(ValueError):validate_packet(self.packet)
        self.packet['evidence'][0]['excerpt_sha256']=sha_text(self.packet['evidence'][0]['excerpt'])
        self.packet.update(input_kind='registered_archive',approved_na=True,na_approval_id='teacher-said-so')
        with self.assertRaises(ValueError):validate_packet(self.packet)
        self.packet.update(input_kind='fixture_demo',approved_na=False,na_approval_id=None,complete_system_probes=True)
        with self.assertRaises(ValueError):validate_packet(self.packet)


class RegisteredPreflightTests(unittest.TestCase):
    def setUp(self):
        scratch=ROOT/'build/test-tmp';scratch.mkdir(parents=True,exist_ok=True)
        self.tmp=tempfile.TemporaryDirectory(dir=scratch);self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        for name in ('configs/review-registry.json','docs/specification.md'):
            dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,dest)
        self.archive='evidence/native-fuzz-runs/20261017T122327Z-0b2f7718'
        shutil.copytree(ROOT/self.archive,self.root/self.archive)

    def test_real_local_reanalysis_never_claims_independent_reproduction(self):
        packet=build_packet('defense-20261017','OBS-01',self.root)
        self.assertEqual(packet['contract']['status'],'project_draft')
        self.assertFalse(packet['approved_na'])
        self.assertFalse(packet['complete_system_probes'])
        self.assertEqual({i['evidence_source'] for i in packet['evidence']},{'target_runner','static_inspection'})
        self.assertEqual({i['verification_level'] for i in packet['evidence']},{'OBSERVED'})
        request=build_request(packet,'deepseek-flash','deepseek')
        self.assertEqual(request['max_output_tokens'],1500)
        self.assertEqual(request['reasoning'],{'effort':'high'})
        boundary=build_packet('defense-20261017','SEC-03',self.root)
        self.assertEqual(build_request(boundary,'deepseek-flash','deepseek')['reasoning'],{'effort':'none'})

    def test_contract_manifest_or_raw_log_tamper_blocks_preflight(self):
        for name in ('docs/specification.md',self.archive+'/manifest.json',self.archive+'/fuzz-results.jsonl'):
            path=self.root/name;before=path.read_bytes()
            path.write_bytes(before+b' ')
            with self.assertRaises(ValueError):build_packet('defense-20261017','SEC-03',self.root)
            path.write_bytes(before)
        with self.assertRaises(ValueError):build_packet('unknown-release','SEC-03',self.root)
        for name in ('../secret','D:/secret','/secret','evidence/../../secret'):
            with self.assertRaises(ValueError):bounded_file(self.root,name)

    def test_edited_packet_cannot_reach_network_even_with_valid_excerpt_hash(self):
        packet=build_packet('defense-20261017','SEC-03',self.root)
        packet['evidence'][0]['excerpt']='A forged positive summary'
        packet['evidence'][0]['excerpt_sha256']=sha_text(packet['evidence'][0]['excerpt'])
        with patch('ipcsec.registered_review.TRUSTED_ROOT',self.root), \
                patch('ipcsec.semantic_review.urlopen') as network:
            with self.assertRaises(ValueError):call(packet,'deepseek-flash',self.root/'not-created','deepseek')
            network.assert_not_called()
            self.assertFalse((self.root/'not-created').exists())
