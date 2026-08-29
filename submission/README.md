# V5.12d Final Submission

This directory is the self-contained runtime package for the TechJam Conversational E-Commerce Search Challenge.

## Contents

- `agent.py`: required `Agent` entry point.
- `models/potion-base-8M/`: bundled Model2Vec static embedding model (MIT license).
- `requirements.txt`: optional semantic runtime dependency.
- `TECHNICAL_REPORT.md`: architecture, evaluation, runtime, limitations, and reproducibility.
- `AI_USAGE.md`: AI/LLM development disclosure and runtime separation.
- `AI_INTERACTION_HISTORY.md`: chronological interaction and experiment summary.
- `SKILLS_USED.md`: Codex skills and native tool disclosure.

The organizer-provided catalog and evaluator are not redistributed here.

## Requirements

- Python 3.10 or newer (validated with Python 3.12).
- SQLite with FTS5 support.
- Recommended: at least 512 MB available RAM.
- No GPU, API key, paid service, or network connection is required.

Install the local semantic dependency:

```bash
python -m pip install -r submission/requirements.txt
```

`model2vec` loads only the bundled local model with `force_download=False`. If the package or model is unavailable, the agent continues with its deterministic FTS5/rule reranker.

## Agent interface

```python
from submission.agent import Agent

agent = Agent("data/catalog.jsonl")
agent.reset("demo", user_profile={})
response = agent.respond(
    "demo",
    "I need comfortable black running shoes.",
    turn=1,
    top_k=10,
)
```

## Reproduce the public result

Place the frozen 50,000-product catalog at `data/catalog.jsonl`. From the repository root, install dependencies and copy the submission entry point into the participant-kit layout:

```bash
python -m pip install -r submission/requirements.txt
cp submission/agent.py starter/agent.py
python -m evaluator.local_evaluator --catalog data/catalog.jsonl --dataset data/public_set.jsonl --output results.json
```

On Windows PowerShell, replace `cp` with `Copy-Item`.

Expected V5.12d result with the bundled semantic model:

| Metric | Result |
|---|---:|
| Hit Rate@10 | 0.770000 |
| MRR | 0.405845 |
| MTTC | 4.445000 |
| Efficiency | 0.655500 |
| Technical Score | 0.637853 |

Validated fallback without Model2Vec/model files: Technical Score `0.634460`. The fallback is functional but is not the preferred configuration.

## Runtime profile

Measured on the development Windows CPU machine with the 50,000-product catalog:

- Startup: approximately 3.14 seconds.
- Median response: approximately 0.198 seconds.
- Maximum response in the recorded 10-turn benchmark: approximately 0.225 seconds.
- Runtime LLM/API calls: none.
- Prompt/completion tokens: 0/0.

