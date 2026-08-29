import sys
from pathlib import Path


# ============================================================
# Project path
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from starter.agent import Agent


# ============================================================
# Find catalog
# ============================================================

def find_catalog():
    candidates = [
        # Your actual evaluator catalog
        PROJECT_ROOT.parent / "catalog.jsonl" / "catalog.jsonl",

        # Common project locations
        PROJECT_ROOT / "catalog.jsonl",
        PROJECT_ROOT / "data" / "catalog.jsonl",

        # Another possible layout
        PROJECT_ROOT.parent / "catalog.jsonl",
        ]

    for path in candidates:
        if path.is_file():
            return path

    raise FileNotFoundError(
        "\nCould not find catalog.jsonl.\n"
        "Checked:\n"
        + "\n".join(str(p) for p in candidates)
    )


CATALOG_PATH = find_catalog()


# ============================================================
# Helper
# ============================================================

def make_agent():
    return Agent(str(CATALOG_PATH))


def make_profile():
    return {
        "preference_tags": [],
        "summary": "",
        "rating_style": "",
    }


# ============================================================
# TEST 1
# ============================================================

def test_agent_creation():

    print("=" * 60)
    print("TEST 1: Agent creation")
    print("=" * 60)

    print("Project root:")
    print(PROJECT_ROOT)

    print("\nCatalog:")
    print(CATALOG_PATH)

    assert CATALOG_PATH.exists()
    assert CATALOG_PATH.is_file()

    agent = make_agent()

    assert agent is not None
    assert len(agent._products) > 0

    print(
        f"\nLoaded products: {len(agent._products)}"
    )

    print("PASS")
    print()


# ============================================================
# TEST 2
# ============================================================

def test_reset():

    print("=" * 60)
    print("TEST 2: Session reset")
    print("=" * 60)

    agent = make_agent()

    agent.reset(
        "test_reset",
        make_profile(),
    )

    assert "test_reset" in agent._sessions

    state = agent._session_state[
        "test_reset"
    ]

    assert state["history"] == []
    assert state["constraints"] == {}
    assert state["current_constraints"] == {}
    assert state["explicit_constraints"] == {}
    assert state["mode"] == "browsing"

    print("Session initialized correctly.")
    print("PASS")
    print()


# ============================================================
# TEST 3
# ============================================================

def test_single_response():

    print("=" * 60)
    print("TEST 3: Single response")
    print("=" * 60)

    agent = make_agent()

    agent.reset(
        "test_single",
        make_profile(),
    )

    result = agent.respond(
        session_id="test_single",
        user_message="I am looking for a black cotton shirt",
        turn=1,
        top_k=10,
    )

    assert isinstance(result, dict)

    assert "message" in result
    assert "recommendations" in result
    assert "ask_attribute" in result
    assert "usage" in result

    assert isinstance(
        result["recommendations"],
        list,
    )

    assert len(
        result["recommendations"]
    ) > 0

    print(
        "Recommendations:",
        len(result["recommendations"]),
    )

    print("\nTop 3:")

    for item in result["recommendations"][:3]:
        print(item)

    print("\nPASS")
    print()


# ============================================================
# TEST 4
# ============================================================

def test_conversation():

    print("=" * 60)
    print("TEST 4: Multi-turn conversation")
    print("=" * 60)

    agent = make_agent()

    session = "test_conversation"

    agent.reset(
        session,
        make_profile(),
    )

    turns = [
        "I want a shirt",
        "I prefer black",
        "It should be cotton",
        "I want to buy it",
    ]

    for turn_number, message in enumerate(
            turns,
            start=1,
    ):

        result = agent.respond(
            session_id=session,
            user_message=message,
            turn=turn_number,
            top_k=10,
        )

        assert isinstance(result, dict)

        assert "recommendations" in result

        print(
            f"Turn {turn_number}: {message}"
        )

        print(
            "  recommendations:",
            len(result["recommendations"]),
        )

        state = agent._session_state[session]

        print(
            "  mode:",
            state["mode"],
        )

        print(
            "  constraints:",
            state["constraints"],
        )

    print("\nPASS")
    print()


# ============================================================
# TEST 5
# ============================================================

def test_intent_override():

    print("=" * 60)
    print("TEST 5: Intent override")
    print("=" * 60)

    agent = make_agent()

    session = "test_override"

    agent.reset(
        session,
        make_profile(),
    )

    # Original request
    agent.respond(
        session_id=session,
        user_message="I want a black cotton shirt",
        turn=1,
        top_k=10,
    )

    state = agent._session_state[session]

    print(
        "Before override:",
        state["constraints"],
    )

    # Override request
    result = agent.respond(
        session_id=session,
        user_message=(
            "Actually, forget that. "
            "I want a red jacket instead"
        ),
        turn=2,
        top_k=10,
    )

    assert isinstance(result, dict)

    state = agent._session_state[session]

    print(
        "After override:",
        state["constraints"],
    )

    print(
        "Mode:",
        state["mode"],
    )

    # V5.4 should detect override
    assert state["mode"] == "intent_override"

    # Old constraints should be removed
    constraint_text = str(
        state["constraints"]
    ).lower()

    assert "black" not in constraint_text
    assert "cotton" not in constraint_text

    print("Old constraints cleared correctly.")
    print("PASS")
    print()


# ============================================================
# TEST 6
# ============================================================

def test_buying_mode():

    print("=" * 60)
    print("TEST 6: Buying mode")
    print("=" * 60)

    agent = make_agent()

    session = "test_buying"

    agent.reset(
        session,
        make_profile(),
    )

    result = agent.respond(
        session_id=session,
        user_message=(
            "I need to buy a black cotton shirt"
        ),
        turn=1,
        top_k=10,
    )

    assert isinstance(result, dict)

    state = agent._session_state[session]

    print(
        "Mode:",
        state["mode"],
    )

    print(
        "Constraints:",
        state["constraints"],
    )

    assert state["mode"] == "buying"

    assert len(
        result["recommendations"]
    ) > 0

    print("Buying mode detected correctly.")
    print("PASS")
    print()


# ============================================================
# Main
# ============================================================

def main():

    print()
    print("=" * 60)
    print("V5.4 LOCAL TEST SUITE")
    print("=" * 60)
    print()

    print("Using catalog:")
    print(CATALOG_PATH)
    print()

    tests = [
        test_agent_creation,
        test_reset,
        test_single_response,
        test_conversation,
        test_intent_override,
        test_buying_mode,
    ]

    passed = 0
    failed = 0

    for test in tests:

        try:
            test()
            passed += 1

        except Exception as exc:

            failed += 1

            print(
                f"FAIL: {test.__name__}"
            )

            print(
                f"Error: "
                f"{type(exc).__name__}: {exc}"
            )

            print()

    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    print(
        f"Passed: {passed}/{len(tests)}"
    )

    print(
        f"Failed: {failed}/{len(tests)}"
    )

    print("=" * 60)

    if failed:
        sys.exit(1)

    print()
    print("ALL TESTS PASSED.")
    print()


if __name__ == "__main__":
    main()