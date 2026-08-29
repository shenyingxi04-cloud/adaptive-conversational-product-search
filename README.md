# Adaptive Conversational Product Search

A deterministic, fully offline shopping agent for the TechJam Conversational E-Commerce Search Challenge. It routes buying, browsing, and intent-override conversations through a stateful multi-route retrieval pipeline, then reranks products using accumulated conversational context.

## Results

Evaluated with the organizer-provided deterministic harness on the 200-session public development set and frozen 50,000-product catalog:

| Metric | Released starter | This project |
|---|---:|---:|
| Hit Rate@10 | 0.125000 | **0.770000** |
| MRR | 0.068034 | **0.414903** |
| MTTC (lower is better) | 9.810000 | **4.440000** |
| Technical Score | — | **0.640671** |

The final agent improves Hit Rate@10 by **6.16×** without an external API, paid model, network connection, or GPU. See the [full result breakdown](docs/results_summary.md).

## Problem and approach

A buyer saying “I need a leather wallet under $50” should not be treated like a browser saying “show me something fun for summer.” The first requires strict constraint retention; the second benefits from wider discovery. The same session may later contain an explicit correction that invalidates earlier preferences.

This agent handles those behaviors with:

- buying, browsing, and intent-override routing;
- multi-turn structured state and slot rewriting;
- general, category, feature, constraint, and buying-specific retrieval routes;
- context-aware, field-weighted reranking;
- browsing-gated local Model2Vec semantic reranking;
- a capped review-volume tie-breaker;
- proactive clarification within the 10-turn limit;
- a deterministic offline path suitable for network-restricted evaluation.

## Architecture

```text
User message + anonymized profile
                |
                v
      Intent router and state update
                |
                v
 General | Category | Feature | Constraint | Buying
                |
                v
      Merge and deduplicate up to 250 candidates
                |
                v
 Structured reranking + optional local semantics
                |
                v
 Clarification message + ranked Top 10 parent_asin values
```

At startup, the agent builds an in-memory SQLite FTS5 index over the read-only catalog. Retrieval uses surface-form terms, while reranking uses normalized terms and structured conversational evidence. Intent overrides clear incompatible state before the query is rebuilt.

The semantic model is bundled locally and never downloads at runtime. If it cannot load, the agent automatically uses the deterministic FTS/rule path. See the [technical report](docs/technical_report.md).

## Repository layout

```text
submission/agent.py       final standalone competition entry
starter/agent.py          final agent in participant-kit layout
evaluator/                organizer-provided local evaluation harness
data/public_set.jsonl     organizer-provided public development sessions
docs/                     contract, rules, results, and technical report
tests/                    interface and behavior tests
```

Local catalogs, debug traces, and exploratory result files are intentionally excluded from GitHub.

## Requirements

- Python 3.10 or newer
- SQLite with FTS5 support (included in standard CPython builds)
- Sufficient memory to index the 50,000-product catalog

`model2vec==0.9.0` enables the preferred local semantic reranker. API keys, external services, GPU access, and runtime network access are not required. A dependency-free deterministic fallback is built in.

## Setup

Clone this repository and download the frozen competition catalog from the [official participant-kit release](https://github.com/TechJam2026/techjam-conversational-search/releases/tag/participant-kit).

Decompress it and place it at:

```text
data/catalog.jsonl
```

Verify it using the organizer-provided SHA256 checksum. The catalog is not redistributed in this repository.

## Reproduce the public result

From the repository root:

```bash
python -m evaluator.local_evaluator \
  --catalog data/catalog.jsonl \
  --dataset data/public_set.jsonl \
  --output results.json
```

Expected aggregate output:

```text
Hit Rate@10     0.770000
MRR             0.414903
MTTC            4.440000
Efficiency      0.656000
Technical Score 0.640671
```

The evaluator is deterministic. Do not edit the evaluator or public labels when reproducing the result.

## Agent interface

```python
from starter.agent import Agent

agent = Agent("data/catalog.jsonl")
agent.reset("demo-session", user_profile={})
response = agent.respond(
    "demo-session",
    "I need comfortable running shoes in black.",
    turn=1,
    top_k=10,
)
```

Each response contains a clarification message, one optional requested attribute, ordered product recommendations, and non-negative usage counters matching the official contract.

## Three-turn demo

Run the prepared end-to-end demo against the local catalog:

```bash
python demo.py --catalog data/catalog.jsonl --top-k 5
```

The demo shows broad browsing, added rainy-day requirements, and an explicit intent change to black leather casual boots. See the [three-minute video script](docs/demo_script.md) and [recording checklist](docs/demo_recording_checklist.md).

## Cost, latency, and network disclosure

| Item | Disclosure |
|---|---|
| External API | None |
| Network required | No |
| Prompt/completion tokens | 0 / 0 |
| Estimated model cost | $0 |
| Main runtime dependency | SQLite FTS5 and local Model2Vec 0.9.0 |

## Development approach

The system was developed through controlled ablation rather than accumulating unverified patches. Regressing experiments were discarded. Full-catalog semantic retrieval and an excessive popularity prior both lost score and were rejected. `starter/agent.py` is the frozen V5.13 champion.

## Limitations and future improvements

- Lexical candidate retrieval can still miss rare paraphrases before semantic reranking.
- Gender and fine-grained product subtype are not fully structured.
- Manual public-set iteration can overfit and must be interpreted cautiously.
- Building the in-memory index adds startup time.
- A future version could learn a small reranker with properly separated training and validation sessions.

## Data attribution

The frozen competition artifacts are derived from [Amazon Reviews 2023](https://amazon-reviews-2023.github.io/) by McAuley Lab at UCSD. See [DATA_ATTRIBUTION.md](DATA_ATTRIBUTION.md). The private 800-session holdout was never accessed.

## Team contributions

This is a solo project. System design, implementation, evaluation, documentation, and demo production were completed by **shenyingxi**.

## License

This project is released under the [MIT License](LICENSE).

## Submission status

See the [release checklist](docs/release_checklist.md) for the remaining GitHub, Devpost, and demo-video steps.

## Recording UI

On Windows, double-click `start_demo_ui.bat`. The browser opens `http://127.0.0.1:8765` and uses the existing V5.13 agent locally. No external API or network connection is used by ranking. Use the three preset prompts for the recorded multi-turn demo.
