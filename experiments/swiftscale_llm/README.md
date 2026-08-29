# SwiftScale reranking experiment

This experiment wraps the frozen V5.10e agent. It never changes the champion files.

## Behavior

- V5.10e produces the first 20 candidates.
- Buying and Intent Override sessions are eligible for SwiftScale reranking.
- Browsing sessions retain the V5.10e order.
- Missing keys, timeouts, HTTP errors, malformed output, and invalid rankings automatically fall back to V5.10e.
- The API key is read only from `SWIFTSCALE_API_KEY`.

## Configuration

In CMD, set the key only for the current window:

```bat
set SWIFTSCALE_API_KEY=YOUR_KEY
set SWIFTSCALE_MODEL=swiftlite.auto
set SWIFTSCALE_TIMEOUT=8
```

Never put the key in source files, `.env`, screenshots, logs, or Git commits.

## Offline fallback check

With `SWIFTSCALE_API_KEY` unset, this wrapper must produce the same Top 10 as V5.10e.

## One-call smoke test

From the repository root, using the real catalog path:

```bat
python -m experiments.swiftscale_llm.smoke_test --catalog "E:\path\to\catalog.jsonl"
```

Confirm that `llm_enabled` is `true` and `usage.prompt_tokens` is greater than zero. This test makes one API request.

## Evaluation policy

Start with a small, explicitly selected development slice. Record quality, latency, and usage before considering a full 200-session run. The final submission must continue to work without network access.
