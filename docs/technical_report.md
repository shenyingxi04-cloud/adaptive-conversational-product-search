# Technical Report — V5.12d

## Executive summary

V5.12d is a stateful, fully offline conversational product-search agent. It combines SQLite FTS5 multi-route retrieval, structured multi-turn constraints, deterministic field-aware reranking, a small local semantic reranker, and a bounded review-volume prior. It never sends catalog or conversation data to an external service.

On the organizer-provided 200-session public development set and frozen 50,000-product catalog, it achieves Hit Rate@10 `0.770000`, MRR `0.405845`, MTTC `4.445000`, and recommended technical score `0.637853`.

## Runtime environment

- Development OS: Windows.
- Language: Python 3.12; code targets Python 3.10+.
- Retrieval: in-memory SQLite FTS5.
- Semantic library: Model2Vec 0.9.0.
- Local model: `minishlab/potion-base-8M`, bundled under `models/potion-base-8M`.
- Hardware: CPU inference; no GPU required.
- Runtime network/API: none.

## Architecture

```text
User message + anonymized profile
                 |
                 v
        Intent and override parser
                 |
                 v
 Multi-turn category, constraint, feature,
 recent-term, and profile state
                 |
                 v
 General | category | feature | constraint |
 strict-feature | high-intent FTS5 routes
                 |
                 v
 Merge and deduplicate bounded candidates
                 |
                 v
 Structured score + browsing-only Model2Vec
 similarity + bounded popularity prior
                 |
                 v
 Clarification + Top-10 parent_asin values
```

### Intent and session state

The agent distinguishes exploratory browsing, high-intent buying, and explicit preference overrides. State accumulates across turns. An override removes incompatible earlier constraints before retrieval, while conversational filler does not erase valid state.

### Multi-route retrieval

At startup, catalog title, categories, features, details, store, and description are indexed in an in-memory FTS5 table. Each turn combines bounded general, category, feature, constraint, strict category-plus-feature, and high-intent routes. IDs are merged and deduplicated before reranking.

### Deterministic reranking

The base score uses field-weighted overlap, query coverage, recent-turn evidence, current and historical constraints, category coverage, exact feature phrases, profile terms, and penalties for missing current buying constraints. All runtime weights are fixed.

### Local semantic reranking

When Model2Vec and the bundled Potion model are available, semantic similarity is applied only while internal state is exploratory. It reranks the bounded lexical pool instead of searching all 50,000 products. The semantic weight is 2.0. This gating preserved buying and override behavior better than global semantic reranking in ablations.

### Popularity prior

The agent uses `rating_number`, not average rating, as a small trust signal in exploratory states. Its logarithmic contribution saturates at 100,000 reviews and is capped at 0.5 point, so it acts only as a tie-breaker among similarly relevant products.

## Evaluation

All reported numbers use the unmodified organizer evaluator. The private holdout was never accessed.

| Metric | V5.10e | V5.12d | Change |
|---|---:|---:|---:|
| Hit Rate@10 | 0.720000 | 0.770000 | +0.050000 |
| MRR | 0.379129 | 0.405845 | +0.026716 |
| MTTC | 4.875000 | 4.445000 | -0.430000 |
| Technical Score | 0.596239 | 0.637853 | +0.041614 |

### Scenario breakdown

| Scenario | Samples | Hit Rate@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Boundary | 10 | 0.700000 | 0.313889 | 5.100000 |
| Browsing | 80 | 0.825000 | 0.520392 | 3.850000 |
| Buying | 80 | 0.737500 | 0.303581 | 4.225000 |
| Intent Override | 30 | 0.733333 | 0.403743 | 6.400000 |

The full evaluation was repeated with identical aggregate results. Unit and behavior checks passed 10/10.

## Controlled experiments

Development used one-change-at-a-time ablations. Retained changes included feature-field weighting, exact multi-word feature evidence, a strict category/feature route, browsing-gated local semantic similarity, and the bounded popularity prior. Full-catalog semantic retrieval and a 1.0-point popularity prior were rejected because they reduced the recommended score or Hit Rate@10.

No model was trained or fine-tuned on the 200 public sessions. Potion is a pretrained static embedding model. This avoids claiming a learned reranker from a dataset too small for reliable training and validation.

## Robustness and fallback

Semantic loading is guarded against missing packages, files, and invalid artifacts. With the model deliberately hidden, all 200 sessions completed and produced Hit Rate@10 `0.765000`, MRR `0.405534`, MTTC `4.485000`, and technical score `0.634460`.

## Performance and cost

- Startup: about 3.14 seconds on the development Windows CPU machine.
- Median turn: about 0.198 seconds.
- Maximum recorded turn: about 0.225 seconds.
- External API requests: 0.
- Evaluation prompt/completion tokens: 0/0.
- Estimated inference API cost: $0.

## Limitations

- The public set has only 200 sessions; fixed weights may not transfer perfectly to the private holdout.
- The candidate pool still begins with lexical retrieval, so rare paraphrases can be missed.
- Fine-grained gender and subtype consistency are not fully structured.
- Review volume can correlate with product age and popularity; the cap limits but does not eliminate this bias.
- The in-memory index is rebuilt at startup.

## Attribution

The challenge catalog is derived from Amazon Reviews 2023 by McAuley Lab at UCSD, as described by the participant kit. Potion and Model2Vec are provided by Minish Lab under the MIT license. See `models/potion-base-8M/README.md`.

