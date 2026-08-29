# Devpost Project Description Draft

## Project title

Adaptive Conversational Product Search

## One-line summary

A fully offline shopping agent that routes buying, browsing, and intent changes through stateful multi-route retrieval, structured reranking, and local semantic similarity.

## Inspiration and problem

Traditional keyword search treats every request as static. Real shoppers arrive with hard constraints, explore loosely, and revise intent during a conversation. The challenge is to preserve useful context without allowing stale preferences to distort later recommendations.

## What it does

The agent maintains structured state for up to ten turns. It detects buying, browsing, and overrides; retrieves through specialized FTS5 routes; merges a bounded candidate pool; and reranks using lexical relevance, constraints, category evidence, recent turns, profile preferences, browsing-gated local semantic similarity, and a capped review-volume tie-breaker. It also asks focused clarification questions.

## How it was built

- Python 3.10+ and SQLite FTS5.
- General, category, feature, constraint, strict-feature, and buying retrieval routes.
- Deterministic structured reranking.
- Model2Vec 0.9.0 with bundled Potion 8M static embeddings.
- Organizer-provided deterministic evaluator.
- No external API, API key, paid model, GPU, or runtime network dependency.

## Results

On the 200-session public development set:

- Hit Rate@10: 0.770000
- MRR: 0.405845
- MTTC: 4.445000
- Technical Score: 0.637853

The released starter achieved Hit Rate@10 0.125 and MRR 0.068034. V5.12d improved Hit Rate@10 by 6.16 times while remaining fully offline. The private holdout was never accessed.

## What is innovative

The agent does not apply one policy to every shopper. It changes retrieval and scoring based on conversational intent, separates retrieval from structured reranking, preserves constraints across turns, rewrites state on explicit overrides, and uses a small local semantic model only where ablation showed it helped. A deterministic fallback keeps the system operational if the semantic dependency is unavailable.

## Impact and feasibility

The design suits retailers that need predictable cost, privacy-friendly processing, and reliable behavior in constrained environments. Runtime API cost and token usage are zero.

## Challenges and lessons

The main challenge was balancing precision for high-intent buyers with discovery for browsers. Controlled ablations showed that global semantic retrieval and overly strong popularity weighting could reduce Top-10 coverage. Only full-evaluator improvements were retained.

## Limitations and future work

Lexical candidate generation can still miss rare paraphrases before semantic reranking. Future work would add structured subtype consistency and learn weights with a larger, properly separated training and validation set.

## Tools, APIs, libraries, and data

- Development: OpenAI Codex desktop with a GPT-5-family coding model; local Python and PowerShell workflow.
- Runtime APIs: none.
- Libraries: Python, SQLite FTS5, Model2Vec 0.9.0, Potion 8M static embeddings.
- Data: organizer-provided catalog and public sessions derived from Amazon Reviews 2023.
- Assets: text architecture diagram and locally generated evaluator reports.

## Team contributions

Solo project. System design, implementation, evaluation, documentation, and demo production were completed by shenyingxi with development-time assistance from OpenAI Codex.

## Links to complete before posting

- GitHub: TODO
- Public YouTube demo: TODO

