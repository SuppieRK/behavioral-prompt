from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .deterministic import score_cached_attempts
from .fingerprints import fingerprint_json, fixture_tree_fingerprint
from .models import CodingAgent, EvalCase, PromptArtifact


@dataclass(frozen=True)
class CacheKeyManifest:
    prompt_hash: str
    execution_hash: str
    fixture_hash: str | None
    agent_hash: str
    runtime_hash: str
    model_hash: str
    adapter_hash: str
    normalizer_hash: str
    prompt_injection_hash: str
    isolation_hash: str
    auth_config_hash: str
    evidence_contract_version: str = "deterministic-evidence-v1"
    report_schema_version: str = "result-json-v2"

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
) -> CacheKeyManifest:
    if fixture_hash is None and fixtures_dir is not None and case.fixture:
        fixture_hash = fixture_tree_fingerprint(fixtures_dir / case.fixture)
    return CacheKeyManifest(
        prompt_hash=prompt.sha256,
        execution_hash=fingerprint_json({"id": case.id, "user_input": case.user_input, "fixture": case.fixture}),
        fixture_hash=fixture_hash,
        agent_hash=agent.fingerprint,
        runtime_hash=fingerprint_json(agent.runtime.to_fingerprint_data()),
        model_hash=agent.model.fingerprint,
        adapter_hash=agent.adapter_fingerprint,
        normalizer_hash=agent.normalizer_fingerprint,
        prompt_injection_hash=fingerprint_json(agent.prompt_injection.to_fingerprint_data()),
        isolation_hash=fingerprint_json(agent.isolation.to_fingerprint_data()),
        auth_config_hash=fingerprint_json({"auth_mode": agent.auth_mode, "auth_identity": dict(sorted(agent.auth_identity.items()))}),
    )


def build_score_key(case: EvalCase, evidence_digest: str) -> dict[str, str]:
    manifest = {
        "evidence_digest": evidence_digest,
        "contract_hash": fingerprint_json(dict(case.contract)),
        "scorer_version": "deterministic-scorer-v1",
    }
    return {"digest": fingerprint_json(manifest), **manifest}


def exact_match_reusable(current: CacheKeyManifest, prior: Mapping[str, Any] | None) -> bool:
    if not prior or prior.get("digest") != current.digest():
        return False
    cell = prior.get("cell")
    if not isinstance(cell, Mapping):
        return True
    return cell.get("status") in {"pass", "fail"} and isinstance(cell.get("normalized_evidence"), Mapping)


def build_reuse_plan(
    cases: tuple[EvalCase, ...],
    agents: tuple[CodingAgent, ...],
    prompt: PromptArtifact,
    *,
    fixtures_dir: Path | None = None,
    prior_cells: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
) -> tuple[ReuseDecision, ...]:
    prior_cells = prior_cells or {}
    decisions: list[ReuseDecision] = []
    for case in cases:
        for agent in agents:
            cache_key = build_cache_key(case, agent, prompt, fixtures_dir=fixtures_dir)
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


def reused_cell(decision: ReuseDecision, *, case: EvalCase, source_report: Path) -> dict[str, Any]:
    source = decision.source or {}
    cell = dict(source.get("cell", {})) if isinstance(source.get("cell"), dict) else {}
    cell["reused_exact_match"] = True
    cell["reuse_source"] = str(source_report)
    cell["cache_key"] = {"digest": decision.cache_key.digest(), **decision.cache_key.__dict__}
    outcome, checks, passing_attempt = score_cached_attempts(case, cell)
    cell["status"] = outcome.status.value
    cell["reason"] = outcome.reason.value
    cell["message"] = outcome.message
    cell["deterministic_checks"] = list(checks)
    cell["scored_attempt"] = passing_attempt
    cell["score_key"] = build_score_key(case, decision.cache_key.digest())
    cell["rescored_from_cache"] = True
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
