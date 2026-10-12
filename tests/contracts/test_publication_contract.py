"""Publication decisions retain one owner, caller compatibility and real effects."""
from __future__ import annotations
import ast
import contextlib
import copy
from dataclasses import asdict, replace
from datetime import datetime, timezone
import importlib
import io
import json
import os
from pathlib import Path
import pickle
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts.pipeline import profile_pipeline as pipeline

def _publication_declaration_roster(tree):
    return sorted((type(node).__name__,node.name) for node in tree.body
        if isinstance(node,(ast.FunctionDef,ast.ClassDef)))

ROOT = Path(__file__).resolve().parents[2]

class _FixedTime(datetime):
    @classmethod
    def now(cls, tz=None):
        value=cls(2026,10,12,tzinfo=timezone.utc)
        return value.astimezone(tz) if tz else value.replace(tzinfo=None)

@contextlib.contextmanager
def _output(root):
    from scripts.pipeline import compute_metrics, profile_helpers
    from scripts.quality import diagnostics
    previous=Path.cwd()
    (root/'templates').mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/'templates/README.md.tpl',root/'templates/README.md.tpl')
    os.chdir(root)
    try:
        with patch.object(compute_metrics,'datetime',_FixedTime),patch.object(profile_helpers,'datetime',_FixedTime),patch.object(diagnostics,'datetime',_FixedTime):
            yield
    finally: os.chdir(previous)

def _collected():
    from tests.pipeline import test_compute_metrics_accuracy as fixtures
    with patch.object(fixtures,'datetime',_FixedTime):return fixtures.AccuracyTests()._collected()

def _generate(collected):
    # This isolates post-guard synthetic live facts. Real identity, writers and
    # validation remain active; it is not a clean/live provider assertion.
    with patch.object(pipeline,'refuse_dirty_generator_source',return_value=None):
        result=pipeline.run_profile_pipeline_with_collected(collected,logger=lambda *a:None,
             allow_network_calls=False,source_kind='github-api')
        return pipeline._seal_artifact_set(result,logger=lambda *a:None)

def _files(root):
    from scripts.contracts import PROFILE_ARTIFACT_PATHS
    return {name:(root/name).read_bytes() for name in PROFILE_ARTIFACT_PATHS if (root/name).exists()}

class PublicationContractTests(unittest.TestCase):
    def _subject(self,**overrides):
        values=dict(subject='candidate_generation',source_kind='github-api',private_inventory_status='exact',contribution_currentness='current')
        return pipeline.PublicationSubject(**(values|overrides))

    def test_decision_permissions_and_retained_hold_reasons(self):
        ready=pipeline.evaluate_profile_publication(self._subject())
        self.assertEqual(('READY',True,True),(ready.state,bool(ready),ready.writes_local_artifacts))
        held=pipeline.evaluate_profile_publication(self._subject(source_kind='fixture',private_inventory_status='partial',contribution_currentness='noncurrent'))
        self.assertEqual('HOLD_NONLIVE_SOURCE',held.state)
        self.assertEqual(('NONLIVE_SOURCE','INCOMPLETE_PRIVATE_EVIDENCE','NONCURRENT_CONTRIBUTIONS'),held.reasons)
        self.assertFalse(held.allows_canonical_publication)
        self.assertTrue(held.writes_local_artifacts)

    def test_error_precedence_and_sorted_completeness_contradictions(self):
        result=pipeline.evaluate_profile_publication(self._subject(artifact_errors=('second','first'),metric_family_statuses=(('z','unavailable'),('a','unavailable')),unqualified_partial_consumers=('p',)))
        self.assertEqual(('INVALID_ARTIFACT_SET',),result.reasons)
        self.assertEqual(('second','first'),result.errors)
        result=pipeline.evaluate_profile_publication(self._subject(metric_family_statuses=(('z','unavailable'),('a','unavailable'))))
        self.assertEqual(('CONTRADICTORY_METRIC_COMPLETENESS',),result.reasons)
        self.assertEqual(('a is unavailable while the repository inventory is exact','z is unavailable while the repository inventory is exact'),result.errors)

    def test_constructors_preserve_subject_identity_and_partial_qualification(self):
        model={'data_quality':{'private_aggregate_status':'exact','metric_statuses':{'m':'partial'}},'data_scope':{'metric_scopes':{'m':'PARTIAL known minimum'}}}
        original=copy.deepcopy(model)
        candidate=pipeline.candidate_publication_subject(model,source_kind='github-api')
        stored=pipeline.stored_publication_subject({'source_kind':'github-api'},model)
        self.assertEqual(('candidate_generation','stored_artifact_set'),(candidate.subject,stored.subject))
        self.assertEqual((),candidate.unqualified_partial_consumers)
        self.assertEqual('READY',pipeline.evaluate_profile_publication(candidate).state)
        self.assertEqual(original,model)
        model['data_scope']['metric_scopes']['m']='exact values'
        result=pipeline.evaluate_profile_publication(pipeline.candidate_publication_subject(model,source_kind='github-api'))
        self.assertEqual(('UNQUALIFIED_PARTIAL_METRIC',),result.reasons)

    def test_legacy_class_aliases_and_serialization_identity(self):
        owner=importlib.import_module('scripts.contracts.publication')
        for name,value in [('PublicationSubject',self._subject()),('PublicationDecision',pipeline.PublicationDecision('READY'))]:
            self.assertIs(getattr(pipeline,name),getattr(owner,name))
            self.assertEqual('scripts.pipeline.profile_pipeline',type(value).__module__)
            self.assertEqual(name,type(value).__qualname__)
            for protocol in range(pickle.HIGHEST_PROTOCOL+1):
                with self.subTest(name=name,protocol=protocol):self.assertEqual(value,pickle.loads(pickle.dumps(value,protocol=protocol)))

    def test_legacy_candidate_selects_evaluator_before_constructor_callback(self):
        first=pipeline.PublicationDecision('HOLD_NONCURRENT_CONTRIBUTIONS',('NONCURRENT_CONTRIBUTIONS',))
        second=pipeline.PublicationDecision('READY')
        original=pipeline.candidate_publication_subject
        def callback(*args,**kwargs):
            pipeline.evaluate_profile_publication=lambda subject:second
            return original(*args,**kwargs)
        with tempfile.TemporaryDirectory() as directory,_output(Path(directory)):
            with patch.object(pipeline,'evaluate_profile_publication',return_value=first),patch.object(pipeline,'candidate_publication_subject',callback):
                result=pipeline.run_profile_pipeline_with_collected(_collected(),logger=lambda *a:None,allow_network_calls=False,source_kind='fixture')
                self.assertIs(first,result['publication_decision'])
                self.assertEqual({},_files(Path(directory)))

    def test_legacy_stored_import_selects_evaluator_before_validation_callback(self):
        from scripts.cli import profile_cli as cli
        from scripts.quality import validate_generated_profile as validator
        first=pipeline.PublicationDecision('HOLD_NONCURRENT_CONTRIBUTIONS',('NONCURRENT_CONTRIBUTIONS',),subject='stored_artifact_set')
        second=pipeline.PublicationDecision('READY',subject='stored_artifact_set')
        with tempfile.TemporaryDirectory() as directory,_output(Path(directory)):
            _generate(_collected())
            original=validator.validate_profile
            def callback():
                pipeline.evaluate_profile_publication=lambda subject:second
                return original()
            with patch.object(pipeline,'evaluate_profile_publication',return_value=first),patch.object(validator,'validate_profile',callback),contextlib.redirect_stdout(io.StringIO()):
                result=cli._cmd_publication_status(SimpleNamespace(require_ready=True,github_output=None))
            self.assertEqual(('HOLD_NONCURRENT_CONTRIBUTIONS',1),(result.extra['state'],result.exit_code))

    def test_default_candidate_calls_current_publication_owner(self):
        owner=importlib.import_module('scripts.contracts.publication')
        replacement=owner.PublicationDecision('HOLD_NONCURRENT_CONTRIBUTIONS',('NONCURRENT_CONTRIBUTIONS',))
        with tempfile.TemporaryDirectory() as directory,_output(Path(directory)):
            with patch.object(owner,'evaluate_profile_publication',return_value=replacement) as evaluate:
                result=pipeline.run_profile_pipeline_with_collected(_collected(),logger=lambda *a:None,allow_network_calls=False,source_kind='fixture')
            self.assertIs(replacement,result['publication_decision'])
            self.assertEqual(1,evaluate.call_count)
            self.assertEqual({},_files(Path(directory)))

    def test_default_stored_calls_current_publication_owner(self):
        owner=importlib.import_module('scripts.contracts.publication')
        from scripts.cli import profile_cli as cli
        replacement=owner.PublicationDecision('HOLD_NONCURRENT_CONTRIBUTIONS',('NONCURRENT_CONTRIBUTIONS',),subject='stored_artifact_set')
        with tempfile.TemporaryDirectory() as directory,_output(Path(directory)):
            _generate(_collected())
            with patch.object(owner,'evaluate_profile_publication',return_value=replacement) as evaluate,contextlib.redirect_stdout(io.StringIO()):
                result=cli._cmd_publication_status(SimpleNamespace(require_ready=True,github_output='github-output.txt'))
            self.assertEqual(('HOLD_NONCURRENT_CONTRIBUTIONS',1),(result.extra['state'],result.exit_code))
            self.assertEqual(1,evaluate.call_count)
            self.assertEqual('publish=false\nstate=HOLD_NONCURRENT_CONTRIBUTIONS\nreasons=NONCURRENT_CONTRIBUTIONS\n',Path('github-output.txt').read_text())

    def test_one_algorithm_owner_and_transparent_legacy_forwards(self):
        owner=ROOT/'scripts/contracts/publication.py'
        expected={'PublicationSubject','PublicationDecision','evaluate_profile_publication','candidate_publication_subject','stored_publication_subject','_unqualified_partial_metrics'}
        new=ast.parse(owner.read_bytes())
        definitions=[n for n in new.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))]
        self.assertEqual(expected,{n.name for n in definitions})
        self.assertEqual(6,len(definitions))
        old=ast.parse((ROOT/'scripts/pipeline/profile_pipeline.py').read_bytes())
        expected_legacy=[
            ('FunctionDef','_decision_allows_canonical_writes'),
            ('FunctionDef','_decision_writes_local_artifacts'),
            ('FunctionDef','_seal_artifact_set'),
            ('FunctionDef','_unqualified_partial_metrics'),
            ('FunctionDef','candidate_publication_subject'),
            ('FunctionDef','evaluate_profile_publication'),
            ('FunctionDef','refuse_dirty_generator_source'),
            ('FunctionDef','run_profile_pipeline'),
            ('FunctionDef','run_profile_pipeline_from_fixture'),
            ('FunctionDef','run_profile_pipeline_with_collected'),
            ('FunctionDef','stored_publication_subject'),
        ]
        self.assertEqual(expected_legacy, _publication_declaration_roster(old), 'PUBLICATION_SINGLE_PHYSICAL_OWNER: legacy declaration roster')
        self.assertFalse(any(isinstance(n,ast.ClassDef) and n.name in expected for n in old.body))
        for node in old.body:
            if isinstance(node,ast.FunctionDef) and node.name in expected:
                body=[n for n in node.body if not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))]
                self.assertEqual(1,len(body),node.name)
                self.assertIsInstance(body[0],ast.Return,node.name)
                call=body[0].value
                self.assertIsInstance(call,ast.Call,node.name)
                self.assertIsInstance(call.func,ast.Attribute,node.name)
                self.assertEqual(node.name,call.func.attr)

    def test_decision_owner_cold_import_excludes_provider_and_writer_modules(self):
        code="import json,sys;import scripts.contracts.publication;print(json.dumps(sorted(n for n in sys.modules if n=='scripts' or n.startswith('scripts.'))))"
        result=subprocess.run([sys.executable,'-B','-c',code],cwd=ROOT,capture_output=True,text=True,check=True)
        modules=json.loads(result.stdout)
        prohibited=[n for n in modules if n.startswith(('scripts.github.','scripts.pipeline.','scripts.rendering.generate_')) or n in ('scripts.github','scripts.pipeline')]
        self.assertEqual([],prohibited)
        self.assertLess(len(modules),37)

    def test_fixture_writes_local_valid_artifacts_without_canonical_permission(self):
        from scripts.quality.validate_generated_profile import validate_profile
        with tempfile.TemporaryDirectory() as directory,_output(Path(directory)):
            result=pipeline.run_profile_pipeline_from_fixture(str(ROOT/'tests/fixtures/sample_collected_data.json'),logger=lambda *a:None)
            self.assertEqual('HOLD_NONLIVE_SOURCE',result['publication_decision'].state)
            self.assertTrue(result['publication_decision'].writes_local_artifacts)
            self.assertFalse(result['publication_decision'].allows_canonical_publication)
            self.assertTrue(validate_profile().ok)
            self.assertTrue(_files(Path(directory)))

    def test_held_live_candidate_keeps_actual_files_and_stored_ready(self):
        from scripts.cli import profile_cli as cli
        with tempfile.TemporaryDirectory() as directory,_output(Path(directory)):
            value=_collected();_generate(value);before=_files(Path(directory))
            counts=dict(value.repo_counts);counts['private_owned']=counts['private_owned_nonfork']=2
            result=_generate(replace(value,repo_counts=counts))
            self.assertEqual('HOLD_INCOMPLETE_PRIVATE_EVIDENCE',result['publication_decision'].state)
            self.assertEqual(before,_files(Path(directory)))
            with contextlib.redirect_stdout(io.StringIO()):status=cli._cmd_publication_status(SimpleNamespace(require_ready=True,github_output=None))
            self.assertEqual(('READY',0),(status.extra['state'],status.exit_code))

    def test_snapshot_writer_fault_keeps_later_bytes_and_stored_refuses(self):
        from scripts.quality.validate_generated_profile import validate_profile
        with tempfile.TemporaryDirectory() as directory,_output(Path(directory)):
            value=_collected();_generate(value);before=_files(Path(directory))
            original=pipeline.write_dashboard_json
            def fail_after_write(*args,**kwargs):
                original(*args,**kwargs)
                raise OSError('snapshot writer fault')
            zero=replace(value,repo_counts={key:0 for key in value.repo_counts},repos=[],all_repos=[],private_repos=[],events=[],language_bytes={},latest_push_message_by_repo={})
            with patch.object(pipeline,'write_dashboard_json',fail_after_write),self.assertRaisesRegex(OSError,'snapshot writer fault'):
                _generate(zero)
            after=_files(Path(directory))
            self.assertEqual(before['README.md'],after['README.md'])
            self.assertEqual(before['site/data/profile_artifact_manifest.json'],after['site/data/profile_artifact_manifest.json'])
            self.assertNotEqual(before['site/data/profile_snapshot.json'],after['site/data/profile_snapshot.json'])
            self.assertFalse(validate_profile().ok)
