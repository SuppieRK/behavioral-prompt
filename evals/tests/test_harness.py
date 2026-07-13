from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from evals.harness.adapters.jsonish import normalize_jsonish_output
from evals.harness.cases import CaseSelection, load_cases, select_cases
from evals.harness.case_validation import validate_case_set
from evals.harness.cli import _execute_non_reused_cell, _mark_run_unavailable, _run_target_preflights, parse_args
from evals.harness.config import build_selected_agents, load_harness_config
from evals.harness.core import HarnessContractError
from evals.harness.deterministic import score_cached_attempts, score_case
from evals.harness.evidence import HarnessValidationResult, NormalizedAgentEvidence, NormalizedTargetEvidence
from evals.harness.models import PromptArtifact
from evals.harness.outcomes import OutcomeStatus
from evals.harness.reporting.json_report import build_result_report
from evals.harness.report_store import load_prior_cells_from_reports, write_prompt_history
from evals.harness.reuse import build_cache_key, build_score_key


ROOT = Path(__file__).resolve().parents[2]


class DeclarativeCaseTest(unittest.TestCase):
    def test_repository_has_exact_deterministic_inventory(self):
        cases = load_cases(ROOT / "evals/cases.yaml").cases
        self.assertEqual(len(cases), 16)
        self.assertEqual(len({case.id for case in cases}), 16)
        self.assertTrue(all(case.contract for case in cases))
        self.assertTrue(all(case.fixture for case in cases))
        validate_case_set(cases, fixtures_dir=ROOT / "evals/fixtures")
        expected_fixtures = {str(case.fixture) for case in cases}
        fixture_root = ROOT / "evals/fixtures"
        actual_fixtures = {
            path.relative_to(fixture_root).parts[0]
            for path in fixture_root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(actual_fixtures, expected_fixtures)
        for case in cases:
            self.assertTrue((ROOT / "evals/fixtures" / str(case.fixture)).is_dir(), case.id)

    def test_loader_rejects_missing_contract_removed_fields_and_duplicates(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cases.yaml"
            path.write_text("cases:\n  - id: one\n    name: One\n    user_input: Do it\n    rubric: [Pass]\n")
            with self.assertRaises(HarnessContractError):
                load_cases(path)
            path.write_text("cases:\n  - id: one\n    name: One\n    user_input: Do it\n    rubric: [Pass]\n    scorer: old\n    contract: {changes: {max_files: 0}}\n")
            with self.assertRaises(HarnessContractError):
                load_cases(path)
            path.write_text("cases:\n  - &c {id: same, name: One, user_input: Do, rubric: [Pass], contract: {changes: {max_files: 0}}}\n  - *c\n")
            with self.assertRaises(HarnessContractError):
                load_cases(path)

    def test_selection_is_id_only(self):
        cases = load_cases(ROOT / "evals/cases.yaml").cases
        self.assertEqual([case.id for case in select_cases(cases, CaseSelection(("tf-bug-fix",)))], ["tf-bug-fix"])


class CliAndConfigTest(unittest.TestCase):
    def test_cli_supports_rescore_without_target_selection(self):
        args = parse_args(["--rescore", "--case", "tf-bug-fix"])
        self.assertTrue(args.rescore)
        for flag in ("--target", "--rejudge", "--category", "--tag", "--critical"):
            with self.subTest(flag=flag), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                parse_args([flag, "value"])

    def test_refresh_requires_focused_cases(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parse_args(["--refresh"])

    def test_config_selects_all_three_required_targets(self):
        config = load_harness_config(ROOT / "evals/eval.yaml")
        self.assertEqual([agent.id for agent in config.selected_targets], ["local-pi", "local-opencode-gpt55", "local-codex-gpt55"])
        self.assertFalse(hasattr(config, "judge"))

    def test_config_api_does_not_accept_target_override(self):
        with self.assertRaises(TypeError):
            build_selected_agents({}, target_names=("one",))

    def test_target_preflights_return_in_runner_order(self):
        import evals.harness.cli as cli
        original = cli._target_smoke_preflight
        cli._target_smoke_preflight = lambda runner, _: SimpleNamespace(outcome=SimpleNamespace(status=SimpleNamespace(value="pass")), name=runner.id)
        try:
            runners = [SimpleNamespace(id="pi"), SimpleNamespace(id="opencode"), SimpleNamespace(id="codex")]
            results = _run_target_preflights(runners, {"pi", "opencode", "codex"})
        finally:
            cli._target_smoke_preflight = original
        self.assertEqual([item.name for item in results], ["pi", "opencode", "codex"])


class ActionNormalizationTest(unittest.TestCase):
    def test_jsonish_normalizes_read_write_validation_plan_and_vcs(self):
        lines = [
            {"type": "item.completed", "item": {"type": "command_execution", "command": "sed -n '1,80p' src/app.py", "exit_code": 0}},
            {"type": "tool_use", "tool_use": {"name": "update_plan", "input": {"plan": [{"step": "inspect", "status": "in_progress"}]}}},
            {"type": "item.completed", "item": {"type": "file_change", "changes": [{"path": "src/app.py"}]}},
            {"type": "item.completed", "item": {"type": "command_execution", "command": "python3 -m unittest tests/test_app.py", "exit_code": 0}},
            {"type": "item.completed", "item": {"type": "command_execution", "command": "git commit -m bad", "exit_code": 0}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "Done."}},
        ]
        evidence = normalize_jsonish_output("\n".join(json.dumps(item) for item in lines))
        kinds = [item["kind"] for item in evidence.agent_actions]
        self.assertEqual(kinds, ["read", "plan", "write", "validation", "vcs_write"])
        self.assertEqual(evidence.final_response, "Done.")
        self.assertIn("src/app.py", evidence.agent_actions[2]["paths"])


class DeterministicScorerTest(unittest.TestCase):
    def setUp(self):
        self.case = load_cases(ROOT / "evals/cases.yaml").by_id()["tp-no-contrarianism"]
        self.validation = (HarnessValidationResult("0", "test", ".", "success", 0, "", "", 0),)

    def evidence(self, *, changed=("src/greeting.py",), actions=None, response="Done.", validation=None):
        actions = actions if actions is not None else (
            {"index": 1, "kind": "read", "paths": ("src/greeting.py",), "path": "src/greeting.py"},
            {"index": 2, "kind": "read", "paths": ("tests/test_greeting.py",), "path": "tests/test_greeting.py"},
            {"index": 3, "kind": "write", "paths": ("src/greeting.py",), "path": "src/greeting.py"},
        )
        return NormalizedAgentEvidence(
            target=NormalizedTargetEvidence(final_response=response, agent_actions=tuple(actions)),
            diff="diff", changed_files=tuple(changed),
            harness_validation=self.validation if validation is None else validation,
            workspace_files={"src/greeting.py": "def greeting(name): return f'Hello, {name}.'"},
        )

    def test_positive_contract_passes(self):
        outcome, checks = score_case(self.case, self.evidence())
        self.assertEqual(outcome.status, OutcomeStatus.PASS)
        self.assertTrue(all(item["pass"] for item in checks))

    def test_generated_mutations_fail(self):
        mutations = (
            self.evidence(changed=("src/greeting.py", "extra.py")),
            self.evidence(actions=({"index": 1, "kind": "write", "paths": ("src/greeting.py",)},)),
            self.evidence(validation=()),
            self.evidence(response="x" * 3001),
        )
        for evidence in mutations:
            with self.subTest(evidence=evidence):
                outcome, _ = score_case(self.case, evidence)
                self.assertNotEqual(outcome.status, OutcomeStatus.PASS)

    def test_missing_action_evidence_is_harness_error(self):
        outcome, _ = score_case(self.case, self.evidence(actions=()))
        self.assertEqual(outcome.status, OutcomeStatus.HARNESS_ERROR)

    def test_any_passing_attempt_is_success(self):
        failed = _cell_from_evidence(self.evidence(actions=({"index": 1, "kind": "write", "paths": ("src/greeting.py",)},)))
        passed = _cell_from_evidence(self.evidence())
        cell = dict(passed)
        cell["attempt_cells"] = [failed, passed]
        outcome, _, attempt = score_cached_attempts(self.case, cell)
        self.assertEqual(outcome.status, OutcomeStatus.PASS)
        self.assertEqual(attempt, 2)


class CacheTest(unittest.TestCase):
    def test_per_cell_checkpoint_merges_without_losing_prior_cells(self):
        with tempfile.TemporaryDirectory() as temp:
            reports = Path(temp)
            prompt = {"path": "PROMPT.md", "sha256": "prompt-hash"}
            write_prompt_history(reports, {"prompt": prompt, "cells": [{"case_id": "one", "target_id": "pi", "cache_key": {"digest": "a"}}]})
            write_prompt_history(reports, {"prompt": prompt, "cells": [{"case_id": "two", "target_id": "pi", "cache_key": {"digest": "b"}}]})
            loaded = load_prior_cells_from_reports(reports, "prompt-hash")
            self.assertEqual(set(loaded), {("one", "pi"), ("two", "pi")})

    def test_contract_change_invalidates_score_not_evidence(self):
        case = load_cases(ROOT / "evals/cases.yaml").by_id()["tp-no-contrarianism"]
        agent = load_harness_config(ROOT / "evals/eval.yaml").selected_targets[0]
        prompt = PromptArtifact.from_path(ROOT / "PROMPT.md")
        key = build_cache_key(case, agent, prompt, fixtures_dir=ROOT / "evals/fixtures")
        changed = replace(case, contract={**case.contract, "output": {"max_chars": 800}})
        changed_key = build_cache_key(changed, agent, prompt, fixtures_dir=ROOT / "evals/fixtures")
        self.assertEqual(key.digest(), changed_key.digest())
        self.assertNotEqual(build_score_key(case, key.digest())["digest"], build_score_key(changed, key.digest())["digest"])

    def test_rescore_contract_keeps_evidence_identity(self):
        case = load_cases(ROOT / "evals/cases.yaml").by_id()["tp-no-contrarianism"]
        original = {"digest": "old-evidence", "normalizer_hash": "old-normalizer"}
        score = build_score_key(case, original["digest"])
        self.assertEqual(original, {"digest": "old-evidence", "normalizer_hash": "old-normalizer"})
        self.assertEqual(score["evidence_digest"], "old-evidence")


class RetryAndPromotionTest(unittest.TestCase):
    def test_unavailable_target_trips_run_circuit_breaker(self):
        unavailable = {}
        _mark_run_unavailable({"status": "not_evaluated", "reason": "timeout", "message": "stalled"}, "opencode", unavailable)
        self.assertEqual(unavailable, {"opencode": "stalled"})
        _mark_run_unavailable({"status": "fail", "reason": ""}, "pi", unavailable)
        self.assertNotIn("pi", unavailable)

    def test_retry_pass_is_successful_flaky_pass(self):
        import evals.harness.cli as cli
        results = iter([
            {"status": "fail", "reason": "", "message": "", "normalized_evidence": {}},
            {"status": "pass", "reason": "", "message": "", "normalized_evidence": {}},
        ])
        original = cli.execute_case_target
        cli.execute_case_target = lambda **_: next(results)
        try:
            cell = _execute_non_reused_cell(
                case=object(), runner=SimpleNamespace(agent=SimpleNamespace(timeout_seconds=1)),
                prompt=object(), fixtures_dir=Path("."), confirm_failures=1,
            )
        finally:
            cli.execute_case_target = original
        self.assertEqual(cell["status"], "pass")
        self.assertTrue(cell["confirmation"]["flaky_pass_after_retry"])
        self.assertEqual(len(cell["attempt_cells"]), 2)

    def test_publication_requires_all_48_cells(self):
        cases = load_cases(ROOT / "evals/cases.yaml").cases
        targets = load_harness_config(ROOT / "evals/eval.yaml").selected_targets
        cells = [{"case_id": case.id, "target_id": target.id, "status": "pass", "reason": "", "target_usage": {}, "raw_run": {}} for case in cases for target in targets]
        prompt = SimpleNamespace(path=ROOT / "PROMPT.md", sha256="hash")
        selftests = SimpleNamespace(passed=True)
        report = build_result_report(prompt=prompt, selftests=selftests, preflights={}, cases=cases, targets=targets, cells=cells, required_cases=cases)
        missing = build_result_report(prompt=prompt, selftests=selftests, preflights={}, cases=cases, targets=targets, cells=cells[:-1], required_cases=cases)
        self.assertEqual(report["cell_count"], 48)
        self.assertTrue(report["promotion"]["allowed"])
        self.assertFalse(missing["promotion"]["allowed"])

def _cell_from_evidence(evidence: NormalizedAgentEvidence) -> dict[str, object]:
    return {
        "changed_files": list(evidence.changed_files),
        "diff": evidence.diff,
        "final_response": evidence.target.final_response,
        "harness_validation": [item.__dict__ for item in evidence.harness_validation],
        "normalized_evidence": {"actions": list(evidence.target.agent_actions), "workspace_files": dict(evidence.workspace_files)},
    }


if __name__ == "__main__":
    unittest.main()
