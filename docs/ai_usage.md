# AI/LLM Usage Disclosure

## Development-time use

OpenAI Codex desktop was used as a coding assistant. The active environment used an OpenAI GPT-5-family coding model. Codex helped read the participant kit and evaluator, inspect code and schema, propose controlled experiments, edit Python, run evaluation/tests, compare regressions, and draft submission documentation.

The human participant selected the direction, approved experiments, decided when to freeze the code, and requested the final package. Reported results came from local evaluator execution, not LLM estimates.

## Runtime use

The submitted agent does **not** call Codex, GPT, ChatGPT, or another online LLM. It needs no API key and makes no network request. Runtime token usage and API cost are zero.

The only learned runtime component is the bundled `minishlab/potion-base-8M` static embedding model loaded through Model2Vec. It is a local embedding model, not a generative chat LLM. It reranks a bounded candidate pool and has a deterministic fallback.

## Data handling

No private holdout was available or used. Development used organizer-provided public sessions, the catalog, evaluator outputs, and locally generated diagnostics. The runtime agent does not send catalog or conversation data to an external service.

## Transcript availability

This document distinguishes the AI tool used to create code from runtime software. The full raw Codex task history can be exported from the Codex application if the organizer requires the original transcript in addition to this structured record.

