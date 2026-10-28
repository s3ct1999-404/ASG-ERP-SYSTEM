"""Provider contract v1 (internal; NOT URA's wire format) + simulator + real-provider boundary."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Protocol

CONTRACT_VERSION = "asg-fiscal/1"


@dataclass
class ProviderResult:
    outcome: str  # accepted | rejected | retryable | malformed
    fdn: str = ""
    verification_code: str = ""
    error_code: str = ""
    raw: dict[str, Any] = field(default_factory=dict)  # already redacted by the provider


class FiscalProvider(Protocol):
    name: str
    authoritative: bool  # True only for a real URA/accredited channel

    def submit(
        self, payload: dict[str, Any], submission_ref: str, correlation_id: str
    ) -> ProviderResult: ...
    def query(self, submission_ref: str, correlation_id: str) -> ProviderResult | None: ...


class ProviderUnavailable(Exception):
    """Network/timeout/5xx: outcome unknown or not delivered. Always retryable."""


class SimulatorProvider:
    """LOCAL SIMULATOR. Its output is never a URA acceptance. Behaviour is scripted for tests via
    ``SimulatorProvider.script`` (accept | reject | timeout | malformed | timeout_after_commit)."""

    name = "simulator"
    authoritative = False
    script: str = "accept"
    _committed: dict[str, ProviderResult] = {}

    @classmethod
    def reset(cls, script: str = "accept") -> None:
        cls.script = script
        cls._committed = {}

    def _accept(self, ref: str) -> ProviderResult:
        if ref in self._committed:  # provider-side dedupe on the stable submission_ref
            return self._committed[ref]
        digest = hashlib.sha256(ref.encode()).hexdigest()
        res = ProviderResult(
            "accepted",
            fdn=f"SIM-{digest[:12].upper()}",
            verification_code=digest[12:24].upper(),
            raw={"simulated": True},
        )
        self._committed[ref] = res
        return res

    def submit(
        self, payload: dict[str, Any], submission_ref: str, correlation_id: str
    ) -> ProviderResult:
        s = self.script
        if s == "timeout":
            raise ProviderUnavailable("simulated timeout before delivery")
        if s == "timeout_after_commit":
            self._accept(submission_ref)
            raise ProviderUnavailable("simulated timeout after provider commit")
        if s == "reject":
            return ProviderResult(
                "rejected", error_code="SIM_REJECT", raw={"simulated": True, "reason": "scripted"}
            )
        if s == "malformed":
            return ProviderResult("malformed", error_code="SIM_MALFORMED", raw={})
        return self._accept(submission_ref)

    def query(self, submission_ref: str, correlation_id: str) -> ProviderResult | None:
        return self._committed.get(submission_ref)


class UraS2SProvider:
    """Boundary for URA system-to-system integration (NOT IMPLEMENTED: ARCHITECTURE_READY only).

    Needs, from a human: URA test-portal registration, device/TIN credentials, the signing key pair
    and URA's current interface specification (incl. accreditation status). Until then it refuses to
    run rather than pretending."""

    name = "ura_s2s"
    authoritative = True

    def submit(
        self, payload: dict[str, Any], submission_ref: str, correlation_id: str
    ) -> ProviderResult:
        raise NotImplementedError(
            "URA S2S is not configured: credentials and interface spec are required."
        )

    def query(self, submission_ref: str, correlation_id: str) -> ProviderResult | None:
        raise NotImplementedError("URA S2S is not configured.")


def get_provider(name: str) -> FiscalProvider:
    if name == "simulator":
        return SimulatorProvider()
    if name == "ura_s2s":
        return UraS2SProvider()
    raise ValueError(f"Unknown fiscal provider {name!r}")
