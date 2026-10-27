"""Self-consistency tests for the draft contracts in packages/contracts (ASG-012, ASG-014).

These prove the definitions are internally coherent and match the invariants the
Blueprint fixes. They do NOT prove the proposals are the right business rules.
"""

import copy
import json
from collections import defaultdict, deque
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

CONTRACTS = Path(__file__).resolve().parents[2] / "packages" / "contracts"


def load(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text())


# ---------- App manifest schema ----------

VALID_MANIFEST = {
    "manifest_version": 0,
    "id": "com.example.stockcount",
    "name": "Stock Count",
    "version": "1.2.3",
    "publisher": {"id": "example-co", "name": "Example Co"},
    "compatibility": {"platform_min": "0.1.0", "platform_max": "1.0.0"},
    "dependencies": [{"id": "asg.inventory", "version_range": ">=1.0,<2.0"}],
    "permissions": [{"code": "stockcount.count_create", "description": "Create stock counts"}],
    "migrations": [{"id": "0001_initial", "reversible": False}],
}


@pytest.fixture(scope="module")
def manifest_validator() -> Draft202012Validator:
    schema = load("app-manifest.schema.json")
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_valid_manifest_passes(manifest_validator: Draft202012Validator) -> None:
    assert list(manifest_validator.iter_errors(VALID_MANIFEST)) == []


@pytest.mark.parametrize(
    "mutate",
    [
        lambda m: m.pop("id"),
        lambda m: m.pop("publisher"),
        lambda m: m.pop("compatibility"),
        lambda m: m.update(id="NotValid"),
        lambda m: m.update(id="single"),
        lambda m: m.update(version="1.2"),
        lambda m: m.update(version="01.2.3"),
        lambda m: m.update(manifest_version=1),
        lambda m: m.update(entry_point="evil.py"),  # no code entry point until D-015
        lambda m: m["compatibility"].update(platform_min="latest"),
        lambda m: m["permissions"][0].update(code="Bad Code"),
        lambda m: m["migrations"][0].pop("reversible"),
    ],
)
def test_invalid_manifests_are_rejected(manifest_validator: Draft202012Validator, mutate) -> None:
    manifest = copy.deepcopy(VALID_MANIFEST)
    mutate(manifest)
    assert list(manifest_validator.iter_errors(manifest)), "expected a schema violation"


# ---------- State machines ----------


def reachable(initial: str, edges: list[tuple[str, str]]) -> set[str]:
    graph: dict[str, list[str]] = defaultdict(list)
    for a, b in edges:
        graph[a].append(b)
    seen, queue = {initial}, deque([initial])
    while queue:
        for nxt in graph[queue.popleft()]:
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def check_machine(machine: dict, states_key: str) -> tuple[list[str], list[tuple[str, str]]]:
    states = machine[states_key]
    assert len(states) == len(set(states)), "duplicate states"
    assert machine["initial"] in states
    triggers = set()
    edges = []
    for t in machine["transitions"]:
        assert t["from"] in states and t["to"] in states, f"unknown state in {t}"
        assert (t["from"], t["on"]) not in triggers, f"non-deterministic edge {t}"
        triggers.add((t["from"], t["on"]))
        edges.append((t["from"], t["to"]))
    assert reachable(machine["initial"], edges) == set(states), "unreachable state(s)"
    return states, edges


def test_app_lifecycle_machine() -> None:
    machine = load("app-lifecycle.json")
    states, edges = check_machine(machine, "states")
    # Blueprint 3.1 fixes these states.
    assert set(states) == {
        "available",
        "installing",
        "installed",
        "upgrading",
        "disabled",
        "uninstalling",
        "failed",
    }
    # An app can never jump straight to installed or be removed mid-install.
    assert ("available", "installed") not in edges
    assert ("installing", "uninstalling") not in edges
    # Every in-progress state can fail, and failed offers a retry for each operation.
    for in_progress in ("installing", "upgrading", "uninstalling"):
        assert (in_progress, "failed") in edges
        assert ("failed", in_progress) in edges
    # Uninstall ends only in 'available' (data retained per policy) or 'failed'.
    assert {b for a, b in edges if a == "uninstalling"} == {"available", "failed"}


def test_sync_status_machine() -> None:
    machine = load("sync-operation-status.json")
    states, edges = check_machine(machine, "statuses")
    # Blueprint 7.2 minimum statuses.
    assert {"pending", "syncing", "synced", "conflict", "failed", "needs_attention"} <= set(states)
    terminal = set(machine["terminal"])
    assert terminal == {"synced", "failed"}
    # Terminal states have no way out.
    assert not [e for e in edges if e[0] in terminal]
    # Every non-terminal state can still reach a terminal state (nothing gets stuck).
    for state in set(states) - terminal:
        assert reachable(state, edges) & terminal, f"{state} cannot reach a terminal state"
    # Conflicts are never silently dropped: they can only be resolved or escalated.
    assert {b for a, b in edges if a == "conflict"} == {"pending", "needs_attention"}
    # Retries stay in the queue; an accepted result is the only way to 'synced'.
    assert [(a, b) for a, b in edges if b == "synced"] == [("syncing", "synced")]
