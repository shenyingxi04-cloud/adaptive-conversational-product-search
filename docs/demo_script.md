# Three-Minute Demo Script

Target duration: 2 minutes 45 seconds to 2 minutes 55 seconds. Speak naturally and leave a few seconds of upload-safe margin.

## 0:00–0:20 — Problem

**Screen:** Title slide: “Adaptive Conversational Product Search — Fast, private, and fully offline.”

**Voiceover:**

> Product search becomes difficult when shoppers add preferences over several turns or suddenly change their mind. Our solution is a stateful conversational search agent that retrieves from fifty thousand real catalog products, preserves useful constraints, and adapts immediately to intent changes.

## 0:20–0:38 — Architecture

**Screen:** Show the architecture section in `submission/TECHNICAL_REPORT.md`.

**Voiceover:**

> The agent combines an in-memory SQLite FTS5 index, specialized category and constraint retrieval routes, structured reranking, and a small local Model2Vec semantic model. It requires no GPU, API key, network connection, or online LLM at runtime.

## 0:38–0:52 — Start the demo

**Screen:** Terminal in the repository root. Run:

```powershell
.\.venv-semantic\Scripts\python.exe demo.py --catalog data\catalog_test.jsonl --top-k 5
```

**Voiceover:**

> Here is the system running locally on the complete fifty-thousand-product catalog. The bundled semantic model is enabled, and startup takes about three seconds.

## 0:52–1:12 — Broad browsing request

**Screen:** Pause on turn one.

**Voiceover:**

> The shopper begins broadly: “I’m looking for women’s ankle boots.” The agent enters browsing mode and returns relevant ankle boots in about six hundredths of a second.

## 1:12–1:35 — Add requirements

**Screen:** Highlight turn two and the first result.

**Voiceover:**

> Next, the shopper adds waterproofing, comfort, and rainy-day use. The ranking changes immediately. Waterproof and comfortable outdoor boots now rise to the top, while the conversation state remains available for later turns.

## 1:35–2:00 — Intent change

**Screen:** Highlight turn three, the printed state, and result number one.

**Voiceover:**

> Finally, the shopper changes direction: “Actually, ignore waterproof. I need black leather ankle boots for casual wear.” The agent removes the obsolete waterproof preference, extracts leather, black, and casual as current constraints, and ranks a matching black leather casual boot first. The response still takes less than two tenths of a second.

## 2:00–2:25 — Results

**Screen:** Show `docs/results_summary.md` or a clean results slide.

**Voiceover:**

> On the organizer’s two-hundred-session public evaluator, V5.12d achieved seventy-seven percent Hit Rate at ten, an MRR of zero point four zero five eight, and a recommended technical score of zero point six three seven nine. Repeated full runs produced identical results.

## 2:25–2:43 — Reliability

**Screen:** Show the fallback section of the technical report.

**Voiceover:**

> Reliability was a design requirement. If the local semantic dependency is unavailable, the deterministic FTS and rule-based pipeline continues operating and still scores zero point six three four five. Runtime API calls, tokens, and inference cost are all zero.

## 2:43–2:55 — Closing

**Screen:** Final slide with the public GitHub URL and three points: “Stateful. Offline. Reproducible.”

**Voiceover:**

> This makes the system fast, private, reproducible, and practical for real conversational commerce. Thank you.

## Recording notes

- Record at 1080p with terminal font at least 18–20px.
- Hide unrelated folders, notifications, usernames, and local absolute paths where possible.
- Do not scroll rapidly; zoom in on the changed ranking and extracted state.
- Keep the final video below three minutes.
- Upload to YouTube as **Public**, then verify playback in a signed-out or incognito browser.
- Use the repository URL: https://github.com/shenyingxi04-cloud/adaptive-conversational-product-search


