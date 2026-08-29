# Evaluation Results — V5.12d Final

All results use the unmodified organizer evaluator, frozen 50,000-product catalog, and 200-session public development set. The private 800-session holdout was never accessed.

## Final public result

| Metric | Result |
|---|---:|
| Samples | 200 |
| Hit Rate@10 | 0.770000 |
| MRR | 0.405845 |
| MTTC | 4.445000 |
| Efficiency | 0.655500 |
| Technical Score | 0.637853 |
| External API tokens | 0 |
| Estimated API cost | $0 |

## Scenario breakdown

| Scenario | Samples | Hit Rate@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Boundary | 10 | 0.700000 | 0.313889 | 5.100000 |
| Browsing | 80 | 0.825000 | 0.520392 | 3.850000 |
| Buying | 80 | 0.737500 | 0.303581 | 4.225000 |
| Intent Override | 30 | 0.733333 | 0.403743 | 6.400000 |

## Improvement over released starter and V5.10e

| Metric | Released starter | V5.10e | V5.12d Final |
|---|---:|---:|---:|
| Hit Rate@10 | 0.125000 | 0.720000 | 0.770000 |
| MRR | 0.068034 | 0.379129 | 0.405845 |
| MTTC | 9.810000 | 4.875000 | 4.445000 |
| Technical Score | — | 0.596239 | 0.637853 |

V5.12d improves Hit Rate@10 by 6.16 times relative to the released starter and raises the technical score by 0.041614 relative to V5.10e.

## Repeatability and fallback

Two complete semantic-enabled runs produced identical aggregate metrics. With the local semantic model deliberately unavailable, the full evaluator still completed at Hit Rate@10 `0.765000`, MRR `0.405534`, MTTC `4.485000`, and technical score `0.634460`.

## Development policy

Changes were evaluated as controlled ablations. Regressing experiments were discarded. No reranker was trained on the public sessions, and public results should not be interpreted as a guarantee on the private holdout.

