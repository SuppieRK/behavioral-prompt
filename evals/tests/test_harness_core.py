import tempfile
import textwrap
import unittest
from pathlib import Path

from evals.harness.adapters.base import CodingAgentRunner
from evals.harness.capabilities import CapabilityMatrix, CapabilityStatus
from evals.harness.case_validation import case_fingerprint, validate_case
from evals.harness.cases import load_python_cases
from evals.harness.core import HarnessContractError
from evals.harness.fingerprints import deterministic_module_name
from evals.harness.models import (
    AgentInvocation,
    AgentInvocationContext,
    CodingAgent,
    CodingAgentRuntime,
    EvalCase,
    HarnessValidationSpec,
    IsolationStrategy,
    LLMModel,
    PromptArtifact,
    PromptInjectionStrategy,
)


def score_declared(context):
    return []


score_declared.stable_id = "tests.score_declared"
score_declared.evidence_dependencies = ("diff", "final_response")
score_declared.fingerprint_sources = ("evals/tests/test_harness_core.py",)


class HarnessCoreTest(unittest.TestCase):
    def test_module_layout_keeps_core_small(self):
        harness_dir = Path("evals/harness")
        expected = {
            "__init__.py",
            "core.py",
            "models.py",
            "outcomes.py",
            "capabilities.py",
            "cases.py",
            "case_validation.py",
            "fingerprints.py",
            "evidence.py",
            "adapters/base.py",
        }

        present = {path.relative_to(harness_dir).as_posix() for path in harness_dir.glob("**/*.py")}

        self.assertTrue(expected.issubset(present))
        self.assertLess(Path("evals/harness/core.py").read_text().count("\n"), 40)

    def test_llm_model_and_agent_fingerprints_are_stable_and_distinct(self):
        medium = LLMModel("openai", "gpt-5.5", "medium")
        high = LLMModel("openai", "gpt-5.5", "high")

        self.assertEqual(medium.fingerprint, LLMModel("openai", "gpt-5.5", "medium").fingerprint)
        self.assertNotEqual(medium.fingerprint, high.fingerprint)

        agent_a = make_agent("codex", medium)
        agent_b = make_agent("opencode", medium)

        self.assertNotEqual(agent_a.fingerprint, agent_b.fingerprint)

    def test_case_fingerprint_includes_harness_validation(self):
        base = EvalCase(
            id="sample",
            name="Sample",
            description="Sample case.",
            user_input="Do it.",
            ground_truth=("It is done.",),
            scorer=score_declared,
            required_evidence=("diff", "final_response"),
        )
        with_validation = EvalCase(
            id="sample",
            name="Sample",
            description="Sample case.",
            user_input="Do it.",
            ground_truth=("It is done.",),
            scorer=score_declared,
            required_evidence=("diff", "final_response"),
            harness_validation=HarnessValidationSpec(commands=("pytest",)),
        )

        self.assertNotEqual(case_fingerprint(base), case_fingerprint(with_validation))

    def test_scorer_dependencies_must_be_declared_by_case(self):
        case = EvalCase(
            id="bad",
            name="Bad",
            description="Bad scorer case.",
            user_input="Do it.",
            ground_truth=("It is done.",),
            scorer=score_declared,
            required_evidence=("diff",),
        )

        with self.assertRaisesRegex(HarnessContractError, "undeclared evidence"):
            validate_case(case)

    def test_case_loader_uses_cases_tuple_and_deterministic_module_name(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cases_dir = root / "cases"
            cases_dir.mkdir()
            module = cases_dir / "sample_cases.py"
            module.write_text(textwrap.dedent("""
                from evals.harness.models import EvalCase

                CASES = (
                    EvalCase(
                        id="sample",
                        name="Sample",
                        description="Sample case.",
                        user_input="Do it.",
                        ground_truth=("It is done.",),
                    ),
                )
            """))

            name_a = deterministic_module_name(module, root=cases_dir)
            name_b = deterministic_module_name(module, root=cases_dir)
            registry = load_python_cases(cases_dir)

        self.assertEqual(name_a, name_b)
        self.assertEqual(tuple(registry.by_id()), ("sample",))

    def test_case_loader_rejects_markdown_after_cutover(self):
        with tempfile.TemporaryDirectory() as temp:
            cases_dir = Path(temp) / "cases"
            cases_dir.mkdir()
            (cases_dir / "old.md").write_text("# Old\n")

            with self.assertRaisesRegex(HarnessContractError, "Markdown eval case sources remain"):
                load_python_cases(cases_dir)

    def test_case_loader_rejects_target_launch_and_filesystem_mutation_patterns(self):
        with tempfile.TemporaryDirectory() as temp:
            cases_dir = Path(temp) / "cases"
            cases_dir.mkdir()
            (cases_dir / "bad.py").write_text("import subprocess\nCASES = ()\n")

            with self.assertRaisesRegex(HarnessContractError, "unsupported runtime/fs API"):
                load_python_cases(cases_dir)

        with tempfile.TemporaryDirectory() as temp:
            cases_dir = Path(temp) / "cases"
            cases_dir.mkdir()
            (cases_dir / "bad.py").write_text("from pathlib import Path\nPath('x').write_text('bad')\nCASES = ()\n")

            with self.assertRaisesRegex(HarnessContractError, "mutates filesystem"):
                load_python_cases(cases_dir)

    def test_capability_matrix_reports_unsupported_required(self):
        matrix = CapabilityMatrix({
            "final_response": CapabilityStatus.SUPPORTED,
            "agent_command_events": CapabilityStatus.BEST_EFFORT,
        })

        self.assertEqual(matrix.unsupported_required(("final_response",)), ())
        self.assertEqual(matrix.unsupported_required(("agent_command_events",)), ("agent_command_events",))

    def test_invocation_contract_and_runner_protocol_shape(self):
        agent = make_agent("pi", LLMModel("openai-codex", "gpt-5.5", "medium"))
        prompt = PromptArtifact(Path("PROMPT.md"), "abc")
        context = AgentInvocationContext(
            invocation_id="inv-1",
            case_id="sample",
            case_name="Sample",
            user_input="Do it.",
            prompt=prompt,
            prompt_injection_method="append-system-prompt",
            prompt_injection_fingerprint="prompt-v1",
            fixture_fingerprint="fixture",
            workspace_path=Path("/tmp/workspace"),
            agent=agent,
            timeout_seconds=360,
            output_mode="json",
        )
        invocation = AgentInvocation(
            invocation_id=context.invocation_id,
            case_id=context.case_id,
            target_id=agent.id,
            argv=("pi", "--mode", "json"),
            cwd=context.workspace_path,
            env={},
            env_summary_redacted={},
            prompt_injection={"method": context.prompt_injection_method},
            isolation={"method": agent.isolation.method},
            timeout_seconds=context.timeout_seconds,
        )

        self.assertTrue(hasattr(CodingAgentRunner, "build_invocation"))
        self.assertTrue(hasattr(CodingAgentRunner, "fingerprint"))
        self.assertEqual(invocation.cwd, Path("/tmp/workspace"))


def make_agent(runtime_name: str, model: LLMModel) -> CodingAgent:
    return CodingAgent(
        id=f"{runtime_name}-gpt55",
        runtime=CodingAgentRuntime(runtime_name, runtime_name, "json"),
        model=model,
        prompt_injection=PromptInjectionStrategy("AGENTS.md", "prompt-v1"),
        isolation=IsolationStrategy("temp-home", "isolation-v1"),
        adapter_fingerprint="adapter-v1",
        normalizer_fingerprint="normalizer-v1",
        capabilities=CapabilityMatrix({"final_response": CapabilityStatus.SUPPORTED}),
        auth_mode="configured",
    )


if __name__ == "__main__":
    unittest.main()
