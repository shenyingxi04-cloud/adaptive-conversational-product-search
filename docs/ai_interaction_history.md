# AI Tool Interaction History

This concise chronological record summarizes the relevant Codex-assisted development process without reproducing large command outputs or catalog records.

| Phase | Human direction / representative prompt | Codex-assisted work | Verified outcome |
|---|---|---|---|
| Initial build | “Build the agent from the released starter and continue improving it.” | Developed structured state, constraint extraction, intent overrides, multi-route retrieval, and field-aware reranking across V2–V5.9. | Technical score progressed from 0.106710 in the starter to 0.585551 in V5.9; measured regressions such as V3 were rejected. |
| Late-stage continuation | “在 v5.10e 的基础上继续想办法优化” | Inspected retrieval/reranking and proposed isolated changes. | V5.10e retained as rollback point. |
| Feature scoring | “继续” | Tested feature-field bonuses and exact feature phrases individually. | V5.10k and V5.10m improved the public score. |
| Strict retrieval | “下一个能不能变成 5.11” | Added a field-scoped category-plus-feature route and bounded strict bonus. | V5.11b reached technical score 0.626960. |
| LLM clarification | “这是说建议用 llm 吗” | Explained that AI tools are allowed for development but an online runtime LLM is not required. | Chose an offline semantic route. |
| Local semantics | “V5.11b + 小型离线语义模型或嵌入路线” | Rejected a slower BGE ONNX route, then installed and benchmarked Model2Vec Potion 8M. | Fast CPU embeddings with no runtime network. |
| Semantic reranking | “继续” | Tested global and browsing-gated semantic reranking. | Gated reranking became V5.12b; global catalog semantics was rejected. |
| Popularity prior | “继续吧，今天给我最终的代码部分” | Added a capped logarithmic review-volume prior and compared caps 0.5 and 1.0. | Cap 0.5 became V5.12d; cap 1.0 was rejected after losing a hit. |
| Freeze | “今天给我最终的代码部分” | Repeated evaluation, ran tests/latency, and disabled the local model to test fallback. | Score 0.637853; 10/10 tests; fallback 0.634460. |
| Final V5.13 optimization | “OK我们开始最后的算法优化吧” | Preserved V5.12d, analyzed 42 failures, and ablated bounded buying-mode popularity and retrieval-order priors. | Hit@10 stayed 0.770000; MRR rose to 0.414903; repeated score 0.640671; fallback 0.637202. |
| Packaging | “整理提交代码、依赖、README、技术报告和 LLM/AI 工具使用记录” | Packaged code/model and documented setup, results, limitations, and AI use. | Self-contained submission directory produced. |

The participant reviewed scores, selected the offline semantic direction, questioned overfitting, decided not to train a small public-set reranker, and authorized final packaging. Each retained change was evaluated on the full public set; rejected changes were not copied into the champion.
