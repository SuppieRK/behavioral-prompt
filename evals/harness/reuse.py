from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .case_validation import case_fingerprint
from .fingerprints import fingerprint_json, fixture_tree_fingerprint, source_fingerprint
from .models import CodingAgent, EvalCase, PromptArtifact
from .selftest import SELFTEST_CONTRACT_VERSION


@dataclass(frozen=True)
class CacheKeyManifest:
    prompt_hash: str
    case_hash: str
    fixture_hash: str | None
    scorer_hash: str | None
    agent_hash: str
    runtime_hash: str
    model_hash: str
    adapter_hash: str
    normalizer_hash: str
    prompt_injection_hash: str
    isolation_hash: str
    capability_hash: str
    auth_config_hash: str
    judge_hash: str | None
    selftest_contract_version: str
    harness_version: str
    report_schema_version: str = "result-json-v1"

    def digest(self) -> str:
        return fingerprint_json(self.__dict__)


@dataclass(frozen=True)
class ReuseDecision:
    case_id: str
    target_id: str
    cache_key: CacheKeyManifest
    reusable: bool
    source: Mapping[str, Any] | None = None


def build_cache_key(
    case: EvalCase,
    agent: CodingAgent,
    prompt: PromptArtifact,
    *,
    fixtures_dir: Path | None = None,
    fixture_hash: str | None = None,
    scorer_hash: str | None = None,
    judge_config: Mapping[str, object] | None = None,
    harness_version: str = "harness-v1",
) -> CacheKeyManifest:
    if fixture_hash is None and fixtures_dir is not None and case.fixture:
        fixture_hash = fixture_tree_fingerprint(fixtures_dir / case.fixture)
    if scorer_hash is None and case.scorer_fingerprint_sources:
        scorer_hash = source_fingerprint(Path(path) for path in case.scorer_fingerprint_sources)
    return CacheKeyManifest(
        prompt_hash=prompt.sha256,
        case_hash=case_fingerprint(case),
        fixture_hash=fixture_hash,
        scorer_hash=scorer_hash,
        agent_hash=agent.fingerprint,
        runtime_hash=fingerprint_json(agent.runtime.to_fingerprint_data()),
        model_hash=agent.model.fingerprint,
        adapter_hash=agent.adapter_fingerprint,
        normalizer_hash=agent.normalizer_fingerprint,
        prompt_injection_hash=fingerprint_json(agent.prompt_injection.to_fingerprint_data()),
        isolation_hash=fingerprint_json(agent.isolation.to_fingerprint_data()),
        capability_hash=fingerprint_json(agent.capabilities.to_fingerprint_data()),
        auth_config_hash=fingerprint_json({"auth_mode": agent.auth_mode, "auth_identity": dict(sorted(agent.auth_identity.items()))}),
        judge_hash=fingerprint_json({"judge": case.judge, "config": dict(judge_config or {})}) if case.judge else None,
        selftest_contract_version=SELFTEST_CONTRACT_VERSION,
        harness_version=harness_version,
    )


def exact_match_reusable(current: CacheKeyManifest, prior: Mapping[str, Any] | None) -> bool:
    if not prior or prior.get("digest") != current.digest():
        return False
    cell = prior.get("cell")
    if not isinstance(cell, Mapping):
        return True
    return cell.get("status") in {"pass", "fail"}


def build_reuse_plan(
    cases: tuple[EvalCase, ...],
    agents: tuple[CodingAgent, ...],
    prompt: PromptArtifact,
    *,
    fixtures_dir: Path | None = None,
    prior_cells: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
    judge_config: Mapping[str, object] | None = None,
) -> tuple[ReuseDecision, ...]:
    prior_cells = prior_cells or {}
    decisions: list[ReuseDecision] = []
    for case in cases:
        for agent in agents:
            cache_key = build_cache_key(case, agent, prompt, fixtures_dir=fixtures_dir, judge_config=judge_config)
            prior = prior_cells.get((case.id, agent.id))
            decisions.append(ReuseDecision(case.id, agent.id, cache_key, exact_match_reusable(cache_key, prior), prior))
    return tuple(decisions)


def target_ids_requiring_smoke(plan: tuple[ReuseDecision, ...]) -> tuple[str, ...]:
    required = sorted({decision.target_id for decision in plan if not decision.reusable})
    return tuple(required)


def load_prior_cells(report_path: Path) -> dict[tuple[str, str], Mapping[str, Any]]:
    if not report_path.exists():
        return {}
    try:
        data = json.loads(report_path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    cells = data.get("cells", [])
    if not isinstance(cells, list):
        return {}
    loaded: dict[tuple[str, str], Mapping[str, Any]] = {}
    for cell in cells:
        if not isinstance(cell, dict):
            continue
        case_id = cell.get("case_id")
        target_id = cell.get("target_id")
        cache_key = cell.get("cache_key")
        digest = cache_key.get("digest") if isinstance(cache_key, dict) else None
        if isinstance(case_id, str) and isinstance(target_id, str) and isinstance(digest, str):
            loaded[(case_id, target_id)] = {"digest": digest, "cell": cell}
    return loaded


def reused_cell(decision: ReuseDecision, *, source_report: Path) -> dict[str, Any]:
    source = decision.source or {}
    cell = dict(source.get("cell", {})) if isinstance(source.get("cell"), dict) else {}
    cell["reused_exact_match"] = True
    cell["reuse_source"] = str(source_report)
    cell["cache_key"] = {"digest": decision.cache_key.digest(), **decision.cache_key.__dict__}
    raw_run = dict(cell.get("raw_run") or {})
    raw_run["actual_tokens_spent"] = 0
    cell["raw_run"] = raw_run
    usage = dict(cell.get("target_usage") or {})
    previous = usage.get("actual_tokens_spent") or usage.get("total_tokens_reported") or usage.get("uncached_total_tokens")
    usage["actual_tokens_spent"] = 0
    if previous is not None:
        usage["avoided_tokens_by_reuse"] = previous
    cell["target_usage"] = usage
    return cell
