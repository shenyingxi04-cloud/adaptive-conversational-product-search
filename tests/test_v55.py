from __future__ import annotations

import sys
from pathlib import Path


# Make the project root importable.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from starter.agent import Agent

CATALOG = Path(
    "data/catalog.jsonl"
)


def make_agent() -> Agent:
    assert CATALOG.exists(), f"Catalog does not exist: {CATALOG}"
    return Agent(catalog_path=CATALOG)


def test_agent_creation() -> None:
    agent = make_agent()
    assert len(agent._products) > 0
    print(f"Catalog products loaded: {len(agent._products)}")


def test_reset() -> None:
    agent = make_agent()
    agent.reset(
        "test-session",
        {
            "preference_tags": ["casual"],
            "summary": "likes practical products",
            "rating_style": "critical",
        },
    )

    state = agent._session_state["test-session"]

    assert state["history"] == []
    assert state["constraints"] == {}
    assert state["mode"] == "browsing"

    print("Session state initialized correctly.")


def test_single_response() -> None:
    agent = make_agent()
    agent.reset("single", {})

    result = agent.respond(
        "single",
        "I want a shirt",
        1,
        10,
    )

    assert isinstance(result, dict)
    assert "recommendations" in result
    assert len(result["recommendations"]) <= 10

    print(f"Recommendations: {len(result['recommendations'])}")

    if result["recommendations"]:
        print("\nTop 3:")
        for item in result["recommendations"][:3]:
            print(item)


def test_conversation() -> None:
    agent = make_agent()
    session = "conversation"

    agent.reset(session, {})

    turns = [
        "I want a shirt",
        "I prefer black",
        "It should be cotton",
        "I want to buy it",
    ]

    for i, message in enumerate(turns, start=1):
        result = agent.respond(
            session,
            message,
            i,
            10,
        )

        state = agent._session_state[session]

        print(f"Turn {i}: {message}")
        print(f"  recommendations: {len(result['recommendations'])}")
        print(f"  mode: {state['mode']}")
        print(f"  constraints: {state['constraints']}")

    state = agent._session_state[session]

    assert state["constraints"]["color"] == ["black"]
    assert state["constraints"]["material"] == ["cotton"]
    assert state["mode"] == "buying"

    print("\nMulti-turn state preserved correctly.")


def test_intent_override() -> None:
    agent = make_agent()
    session = "override"

    agent.reset(session, {})

    agent.respond(
        session,
        "I want a black cotton shirt",
        1,
        10,
    )

    before = dict(agent._session_state[session]["constraints"])
    print("Before override:", before)

    agent.respond(
        session,
        "Forget what I said. I want a red shirt instead.",
        2,
        10,
    )

    after = agent._session_state[session]["constraints"]
    mode = agent._session_state[session]["mode"]

    print("After override:", after)
    print("Mode:", mode)

    assert "material" not in after
    assert after.get("color") == ["red"]
    assert mode == "intent_override"

    print("Old constraints cleared correctly.")


def test_buying_mode() -> None:
    agent = make_agent()
    session = "buying"

    agent.reset(session, {})

    agent.respond(
        session,
        "I want a black cotton shirt",
        1,
        10,
    )

    result = agent.respond(
        session,
        "I need to buy it",
        2,
        10,
    )

    state = agent._session_state[session]

    print("Mode:", state["mode"])
    print("Constraints:", state["constraints"])
    print("Recommendations:", len(result["recommendations"]))

    assert state["mode"] == "buying"
    assert state["constraints"]["material"] == ["cotton"]
    assert state["constraints"]["color"] == ["black"]

    print("Buying mode detected correctly.")


def test_v55_buying_hard_route() -> None:
    agent = make_agent()
    session = "buying-hard"

    agent.reset(session, {})

    result = agent.respond(
        session,
        "I need to buy a black cotton shirt",
        1,
        10,
    )

    state = agent._session_state[session]

    assert state["mode"] == "buying"
    assert state["constraints"]["color"] == ["black"]
    assert state["constraints"]["material"] == ["cotton"]
    assert len(result["recommendations"]) <= 10

    print("V5.5 buying hard-constraint route executed.")


def test_v55_override_noise() -> None:
    agent = make_agent()
    session = "override-noise"

    agent.reset(session, {})

    agent.respond(
        session,
        "I want a black shirt",
        1,
        10,
    )

    # "actually" alone must NOT reset the state in V5.5.
    agent.respond(
        session,
        "I actually prefer cotton.",
        2,
        10,
    )

    state = agent._session_state[session]

    assert state["mode"] == "browsing"
    assert state["constraints"]["color"] == ["black"]
    assert state["constraints"]["material"] == ["cotton"]

    print("Bare 'actually' no longer triggers an override.")


def run_all() -> None:
    tests = [
        ("TEST 1: Agent creation", test_agent_creation),
        ("TEST 2: Session reset", test_reset),
        ("TEST 3: Single response", test_single_response),
        ("TEST 4: Multi-turn conversation", test_conversation),
        ("TEST 5: Intent override", test_intent_override),
        ("TEST 6: Buying mode", test_buying_mode),
        ("TEST 7: V5.5 buying hard route", test_v55_buying_hard_route),
        ("TEST 8: V5.5 override noise", test_v55_override_noise),
    ]

    passed = 0

    print("=" * 60)
    print("V5.5 LOCAL TEST SUITE")
    print("=" * 60)
    print("Project root :", PROJECT_ROOT)
    print("Catalog path :", CATALOG)

    for name, test in tests:
        print("\n" + "=" * 60)
        print(name)
        print("=" * 60)

        try:
            test()
            print("PASS")
            passed += 1
        except Exception as exc:
            print(f"FAIL: {type(exc).__name__}: {exc}")

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {len(tests) - passed}/{len(tests)}")
    print("=" * 60)

    if passed == len(tests):
        print("ALL TESTS PASSED.")
    else:
        raise SystemExit(1)


if __name__ == "__main__":
    run_all()

