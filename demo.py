from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from submission.agent import Agent


DEMO_MESSAGES = (
    "I'm looking for women's ankle boots.",
    "They should be waterproof and comfortable for rainy days.",
    "Actually, I changed my mind. Instead, I need black leather ankle boots for casual wear.",
)


def console_safe(value: object) -> str:
    text = str(value)
    encoding = sys.stdout.encoding or "utf-8"
    return text.encode(encoding, errors="replace").decode(encoding, errors="replace")


def compact_constraints(state: dict) -> str:
    constraints = state.get("constraints", {})
    parts = []
    for name, values in constraints.items():
        if values:
            parts.append(f"{name}={', '.join(map(str, values))}")
    return "; ".join(parts) if parts else "none"


def run_demo(catalog: Path, top_k: int) -> None:
    print("=" * 72)
    print("V5.13 - Offline Conversational Product Search")
    print("=" * 72)

    started = time.perf_counter()
    agent = Agent(catalog)
    startup = time.perf_counter() - started
    print(f"Catalog products : {len(agent._products):,}")
    print(f"Local semantics  : {'enabled' if agent.semantic_model is not None else 'fallback'}")
    print(f"Startup time     : {startup:.3f}s")

    session_id = "video-demo"
    agent.reset(session_id, user_profile={"rating_style": "usually positive"})

    for turn, user_message in enumerate(DEMO_MESSAGES, start=1):
        print("\n" + "-" * 72)
        print(f"USER {turn}: {user_message}")
        started = time.perf_counter()
        response = agent.respond(session_id, user_message, turn, top_k)
        elapsed = time.perf_counter() - started
        state = agent._session_state[session_id]

        print(f"AGENT : {response['message']}")
        print(f"STATE : mode={state.get('mode')} | {compact_constraints(state)}")
        print(f"TIME  : {elapsed:.3f}s | API tokens=0")
        print("TOP RESULTS:")

        for rank, recommendation in enumerate(response["recommendations"], start=1):
            parent_asin = recommendation["parent_asin"]
            title = agent._products[parent_asin]["title"]
            print(console_safe(f"  {rank:>2}. {parent_asin}  {title[:100]}"))

    print("\n" + "=" * 72)
    print("Demo complete: local retrieval, local embeddings, no network or LLM API.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the V5.13 three-turn demo.")
    parser.add_argument("--catalog", default="data/catalog.jsonl", type=Path)
    parser.add_argument("--top-k", default=5, type=int)
    args = parser.parse_args()
    run_demo(args.catalog, max(1, min(args.top_k, 10)))


if __name__ == "__main__":
    main()
