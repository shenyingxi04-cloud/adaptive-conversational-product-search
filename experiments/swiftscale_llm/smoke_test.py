from __future__ import annotations

import argparse
import json

from experiments.swiftscale_llm.agent import Agent


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one SwiftScale-enhanced buying turn.",
    )
    parser.add_argument("--catalog", required=True)
    args = parser.parse_args()

    agent = Agent(args.catalog)
    session_id = "swiftscale_smoke_test"
    agent.reset(
        session_id,
        {
            "preference_tags": ["material", "comfort", "fit"],
            "rating_style": "usually positive",
        },
    )
    response = agent.respond(
        session_id,
        "I am ready to buy men's running shoes. A key requirement is leather.",
        turn=1,
        top_k=10,
    )
    print(
        json.dumps(
            {
                "message": response.get("message"),
                "ask_attribute": response.get("ask_attribute"),
                "recommendations": [
                    item.get("parent_asin")
                    for item in response.get("recommendations", [])
                ],
                "usage": response.get("usage"),
                "llm_enabled": agent.reranker.enabled,
                "model": agent.reranker.model,
                "llm_error": agent.reranker.last_error,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
