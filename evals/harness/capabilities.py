from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping

from .core import HarnessContractError


class CapabilityStatus(StrEnum):
    SUPPORTED = "supported"
    BEST_EFFORT = "best_effort"
    UNSUPPORTED = "unsupported"


BEST_EFFORT_DIAGNOSTIC_EVIDENCE = {
    "agent_tool_events",
    "agent_command_events",
    "agent_command_events.exit_status",
    "agent_command_events.exit_code",
    "transcript",
}


@dataclass(frozen=True)
class CapabilityMatrix:
    capabilities: Mapping[str, CapabilityStatus | str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized: dict[str, CapabilityStatus] = {}
        for name, status in self.capabilities.items():
            try:
                normalized[str(name)] = status if isinstance(status, CapabilityStatus) else CapabilityStatus(str(status))
            except ValueError as exc:
                raise HarnessContractError(f"invalid capability status for {name}: {status}") from exc
        object.__setattr__(self, "capabilities", normalized)

    def status(self, capability: str) -> CapabilityStatus:
        return self.capabilities.get(capability, CapabilityStatus.UNSUPPORTED)

    def unsupported_required(self, required: tuple[str, ...]) -> tuple[str, ...]:
        return tuple(name for name in required if self.status(name) != CapabilityStatus.SUPPORTED)

    def to_fingerprint_data(self) -> dict[str, str]:
        return {key: self.capabilities[key].value for key in sorted(self.capabilities)}
