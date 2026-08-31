# Technical Report — V5.13

## Executive summary

V5.13 is a stateful, fully offline conversational product-search agent. It combines SQLite FTS5 multi-route retrieval, structured multi-turn constraints, deterministic field-aware reranking, a small local semantic reranker, a bounded review-volume prior, and a retrieval-order tie-breaker for high-intent queries. It never sends catalog or conversation data to an external service.

On the organizer-provided 200-session public development set and frozen 50,000-product catalog, it achieves Hit Rate@10 `0.770000`, MRR `0.414903`, MTTC `4.440000`, and recommended technical score `0.640671`.

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
 similarity + bounded trust and retrieval-order priors
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

### Bounded catalog priors

The agent uses `rating_number`, not average rating, as a small catalog trust signal. Its logarithmic contribution saturates at 100,000 reviews and is capped at 0.5 point for browsing and 1.0 point for buying. In buying mode, a second bounded term preserves some evidence from the merged six-route retrieval order: `4 / sqrt(candidate_rank)`. Both terms rerank only already-retrieved products and cannot introduce a product that failed lexical recall.

## Development evolution

Development began with the released starter and proceeded through many separately saved and evaluated checkpoints. The version labels below are internal engineering milestones, not trained model generations. Regressions were retained in the experiment record because they informed later design choices, but they were not promoted into the final agent.

- **Released starter:** established the interface and deterministic evaluation baseline.
- **V2:** introduced structured constraint extraction, BM25 candidate retrieval, and deterministic field-aware reranking.
- **V3–V4:** explored alternative state and scoring behavior. Their regression relative to V2 showed that additional complexity did not automatically improve retrieval.
- **V5:** strengthened intent-override handling, explicit current-turn constraints, and candidate retrieval.
- **V5.6:** added buying hard-constraint retrieval, constraint-specific supplementary retrieval, coverage bonuses, and missing-constraint penalties.
- **V5.7:** added category anchors, non-informative-reply handling, and persistent conversational feature phrases.
- **V5.8:** expanded multi-route retrieval and explicit category coverage in reranking.
- **V5.9:** separated surface-form FTS retrieval terms from normalized reranking terms, producing the largest single late-stage recall improvement.
- **V5.10e:** increased bounded candidate retention across the established retrieval routes.
- **V5.11b:** added strict category-plus-feature retrieval and bounded exact-feature evidence.
- **V5.12b:** introduced browsing-gated local Model2Vec semantic reranking after global semantic variants were rejected.
- **V5.12d:** added a capped review-volume prior while preserving the lexical candidate boundary.
- **V5.13:** added bounded buying-mode trust and retrieval-order priors, preserving Hit Rate@10 while improving MRR.

## Evaluation

All reported numbers use the unmodified organizer evaluator, the same 200-session public development set, and the frozen 50,000-product catalog. The private holdout was never accessed.

| Checkpoint | Hit Rate@10 | MRR | MTTC | Technical Score |
|---|---:|---:|---:|---:|
| Released starter | 0.125000 | 0.068034 | 9.810000 | 0.106710 |
| V2 | 0.540000 | 0.279673 | 6.895000 | 0.436002 |
| V3 | 0.360000 | 0.200429 | 8.520000 | 0.289729 |
| V4 | 0.395000 | 0.219446 | 8.180000 | 0.319734 |
| V5 | 0.465000 | 0.256855 | 7.810000 | 0.373357 |
| V5.6 | 0.520000 | 0.245220 | 7.190000 | 0.409766 |
| V5.7 | 0.585000 | 0.272524 | 6.160000 | 0.471057 |
| V5.8 | 0.595000 | 0.277117 | 6.030000 | 0.480035 |
| V5.9 | 0.705000 | 0.376837 | 5.000000 | 0.585551 |
| V5.10e | 0.720000 | 0.379129 | 4.875000 | 0.596239 |
| V5.11b | 0.755000 | 0.403865 | 4.585000 | 0.626960 |
| V5.12b | 0.760000 | 0.402998 | 4.545000 | 0.629999 |
| V5.12d | 0.770000 | 0.405845 | 4.445000 | 0.637853 |
| **Final V5.13** | **0.770000** | **0.414903** | **4.440000** | **0.640671** |

Compared with the released starter, V5.13 increased Hit Rate@10 from 0.125000 to 0.770000, a 6.16x improvement, while reducing MTTC from 9.810000 to 4.440000. The non-monotonic early results also document that experimental variants were measured rather than selectively described as improvements.
### Scenario breakdown

| Scenario | Samples | Hit Rate@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Boundary | 10 | 0.700000 | 0.313889 | 5.100000 |
| Browsing | 80 | 0.825000 | 0.520392 | 3.850000 |
| Buying | 80 | 0.737500 | 0.326225 | 4.212500 |
| Intent Override | 30 | 0.733333 | 0.403743 | 6.400000 |

The full evaluation was repeated with identical aggregate results. Direct evaluation of the packaged `submission/agent.py`, the no-model fallback evaluation, and the three-turn recording demo also completed successfully.

## Controlled experiments

Development used one-change-at-a-time ablations. Retained changes included feature-field weighting, exact multi-word feature evidence, a strict category/feature route, browsing-gated local semantic similarity, the bounded popularity prior, and the buying-only retrieval-order prior. Full-catalog semantic retrieval and a 1.0-point browsing popularity prior were rejected because they reduced the recommended score or Hit Rate@10.

No model was trained or fine-tuned on the 200 public sessions. Potion is a pretrained static embedding model. This avoids claiming a learned reranker from a dataset too small for reliable training and validation.

## Robustness and fallback

Semantic loading is guarded against missing packages, files, and invalid artifacts. With the model deliberately hidden, all 200 sessions completed and produced Hit Rate@10 `0.765000`, MRR `0.414341`, MTTC `4.480000`, and technical score `0.637202`.

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
