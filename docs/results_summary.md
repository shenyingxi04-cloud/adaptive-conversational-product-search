# Evaluation Results — V5.13 Final

All results use the unmodified organizer evaluator, frozen 50,000-product catalog, and 200-session public development set. The private 800-session holdout was never accessed.

## Final public result

| Metric | Result |
|---|---:|
| Samples | 200 |
| Hit Rate@10 | 0.770000 |
| MRR | 0.414903 |
| MTTC | 4.440000 |
| Efficiency | 0.656000 |
| Technical Score | 0.640671 |
| External API tokens | 0 |
| Estimated API cost | $0 |

## Scenario breakdown

| Scenario | Samples | Hit Rate@10 | MRR | MTTC |
|---|---:|---:|---:|---:|
| Boundary | 10 | 0.700000 | 0.313889 | 5.100000 |
| Browsing | 80 | 0.825000 | 0.520392 | 3.850000 |
| Buying | 80 | 0.737500 | 0.326225 | 4.212500 |
| Intent Override | 30 | 0.733333 | 0.403743 | 6.400000 |

## Improvement history

| Metric | Released starter | V5.10e | V5.12d | V5.13 Final |
|---|---:|---:|---:|---:|
| Hit Rate@10 | 0.125000 | 0.720000 | 0.770000 | 0.770000 |
| MRR | 0.068034 | 0.379129 | 0.405845 | 0.414903 |
| MTTC | 9.810000 | 4.875000 | 4.445000 | 4.440000 |
| Technical Score | — | 0.596239 | 0.637853 | 0.640671 |

V5.13 preserves V5.12d Hit Rate@10 while increasing overall MRR by 0.009058. Its bounded buying-mode retrieval-order prior improves the ordering of already relevant candidates without changing the six-route recall stage.

## Repeatability and fallback

Two complete semantic-enabled V5.13 runs produced identical aggregate metrics. Direct evaluation of `submission/agent.py` produced the same result. With the local semantic model unavailable, the full evaluator still completed at Hit Rate@10 `0.765000`, MRR `0.414341`, MTTC `4.480000`, and technical score `0.637202`.

## Development policy

Changes were evaluated as controlled ablations. Regressing experiments were discarded. No reranker was trained on the public sessions, and public results should not be interpreted as a guarantee on the private holdout.
