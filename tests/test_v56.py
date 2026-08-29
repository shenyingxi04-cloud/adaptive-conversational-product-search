import sys
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from starter.agent import Agent


# Organizer-provided catalog (not committed to the repository).
CATALOG = Path(
    "data/catalog.jsonl"
)


def make_agent():

    assert CATALOG.exists(), (
        f"Catalog does not exist: {CATALOG}"
    )

    return Agent(
        str(CATALOG)
    )


def profile():

    return {
        "preference_tags": [],
        "summary": "",
        "rating_style": "",
    }


# ============================================================
# 1. Agent creation
# ============================================================

def test_agent_creation():

    agent = make_agent()

    assert len(
        agent._products
    ) > 0

    print(
        "Products:",
        len(agent._products),
    )


# ============================================================
# 2. Basic browsing
# ============================================================

def test_browsing():

    agent = make_agent()

    session = "browsing"

    agent.reset(
        session,
        profile(),
    )

    result = agent.respond(
        session,
        "I want a shirt",
        1,
        10,
    )

    assert len(
        result["recommendations"]
    ) > 0

    assert (
            agent._session_state[
                session
            ]["mode"]
            == "browsing"
    )

    print(
        "Browsing recommendations:",
        len(
            result["recommendations"]
        ),
    )


# ============================================================
# 3. Multi-turn constraints
# ============================================================

def test_multi_turn():

    agent = make_agent()

    session = "multi"

    agent.reset(
        session,
        profile(),
    )

    agent.respond(
        session,
        "I want a shirt",
        1,
        10,
    )

    agent.respond(
        session,
        "I prefer black",
        2,
        10,
    )

    agent.respond(
        session,
        "It should be cotton",
        3,
        10,
    )

    state = (
        agent._session_state[
            session
        ]
    )

    assert (
            state["constraints"]
            ["color"]
            == ["black"]
    )

    assert (
            state["constraints"]
            ["material"]
            == ["cotton"]
    )

    print(
        "Constraints:",
        state["constraints"],
    )


# ============================================================
# 4. Buying mode
# ============================================================

def test_buying():

    agent = make_agent()

    session = "buying"

    agent.reset(
        session,
        profile(),
    )

    result = agent.respond(
        session,
        "I need to buy a black cotton shirt",
        1,
        10,
    )

    state = (
        agent._session_state[
            session
        ]
    )

    assert (
            state["mode"]
            == "buying"
    )

    assert (
            state["constraints"]
            ["color"]
            == ["black"]
    )

    assert (
            state["constraints"]
            ["material"]
            == ["cotton"]
    )

    assert len(
        result["recommendations"]
    ) > 0

    print(
        "Buying recommendations:",
        len(
            result["recommendations"]
        ),
    )


# ============================================================
# 5. Buying context preservation
# ============================================================

def test_buying_context():

    agent = make_agent()

    session = "buy-context"

    agent.reset(
        session,
        profile(),
    )

    agent.respond(
        session,
        "I want a shirt",
        1,
        10,
    )

    agent.respond(
        session,
        "It should be black",
        2,
        10,
    )

    agent.respond(
        session,
        "I prefer cotton",
        3,
        10,
    )

    result = agent.respond(
        session,
        "I want to buy it",
        4,
        10,
    )

    state = (
        agent._session_state[
            session
        ]
    )

    assert (
            state["mode"]
            == "buying"
    )

    assert (
            state["constraints"]
            ["color"]
            == ["black"]
    )

    assert (
            state["constraints"]
            ["material"]
            == ["cotton"]
    )

    assert len(
        result["recommendations"]
    ) > 0

    print(
        "Buying context preserved."
    )


# ============================================================
# 6. True override
# ============================================================

def test_override():

    agent = make_agent()

    session = "override"

    agent.reset(
        session,
        profile(),
    )

    agent.respond(
        session,
        "I want a black cotton shirt",
        1,
        10,
    )

    agent.respond(
        session,
        (
            "Forget what I said. "
            "I want a red shirt instead."
        ),
        2,
        10,
    )

    state = (
        agent._session_state[
            session
        ]
    )

    assert (
            state["mode"]
            == "intent_override"
    )

    assert (
            "material"
            not in state["constraints"]
    )

    assert (
            state["constraints"]
            ["color"]
            == ["red"]
    )

    print(
        "Override constraints:",
        state["constraints"],
    )


# ============================================================
# 7. Bare actually should not reset
# ============================================================

def test_actually():

    agent = make_agent()

    session = "actually"

    agent.reset(
        session,
        profile(),
    )

    agent.respond(
        session,
        "I want a black shirt",
        1,
        10,
    )

    agent.respond(
        session,
        "I actually prefer cotton",
        2,
        10,
    )

    state = (
        agent._session_state[
            session
        ]
    )

    assert (
            state["mode"]
            == "browsing"
    )

    assert (
            state["constraints"]
            ["color"]
            == ["black"]
    )

    assert (
            state["constraints"]
            ["material"]
            == ["cotton"]
    )

    print(
        "Bare actually preserved state."
    )


# ============================================================
# Runner
# ============================================================

TESTS = [
    (
        "Agent creation",
        test_agent_creation,
    ),
    (
        "Browsing",
        test_browsing,
    ),
    (
        "Multi-turn",
        test_multi_turn,
    ),
    (
        "Buying",
        test_buying,
    ),
    (
        "Buying context",
        test_buying_context,
    ),
    (
        "Override",
        test_override,
    ),
    (
        "Actually noise",
        test_actually,
    ),
]


passed = 0


print("=" * 60)
print("V5.6 LOCAL TEST SUITE")
print("=" * 60)


for name, test in TESTS:

    print()
    print("=" * 60)
    print(name)
    print("=" * 60)

    try:

        test()

        print("PASS")

        passed += 1

    except Exception as exc:

        print(
            "FAIL:",
            type(exc).__name__,
            exc,
        )


print()
print("=" * 60)
print("TEST SUMMARY")
print("=" * 60)

print(
    f"Passed: {passed}/{len(TESTS)}"
)

print(
    f"Failed: "
    f"{len(TESTS) - passed}/{len(TESTS)}"
)

if passed == len(TESTS):

    print(
        "ALL TESTS PASSED."
    )
