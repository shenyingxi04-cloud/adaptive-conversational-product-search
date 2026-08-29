from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
import uuid
from typing import Any

from starter.agent_v5_10e import Agent as OfflineAgent


ASIN_RE = re.compile(r"\bB[A-Z0-9]{9}\b")


class SwiftScaleReranker:
    """Small OpenAI-compatible client with fail-closed offline behavior."""

    def __init__(self) -> None:
        self.last_error: str | None = None
        self.api_key = os.environ.get("SWIFTSCALE_API_KEY", "").strip()
        self.model = os.environ.get(
            "SWIFTSCALE_MODEL",
            "swiftlite.auto",
        ).strip()
        self.endpoint = os.environ.get(
            "SWIFTSCALE_CHAT_URL",
            "https://api.swift-scale.com/v1/chat/completions",
        ).strip()
        try:
            self.timeout = max(
                1.0,
                float(os.environ.get("SWIFTSCALE_TIMEOUT", "8")),
            )
        except ValueError:
            self.timeout = 8.0

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def rerank(
        self,
        *,
        user_message: str,
        state: dict[str, Any],
        candidates: list[dict[str, Any]],
        products: dict[str, dict[str, str]],
    ) -> tuple[list[str] | None, dict[str, int]]:
        self.last_error = None
        if not self.enabled or len(candidates) < 2:
            self.last_error = "disabled_or_too_few_candidates"
            return None, {}

        allowed = [
            str(item.get("parent_asin", ""))
            for item in candidates
            if item.get("parent_asin")
        ]
        if len(allowed) < 2:
            self.last_error = "too_few_valid_candidate_ids"
            return None, {}

        candidate_lines = []
        for rank, parent_asin in enumerate(allowed, start=1):
            product = products.get(parent_asin, {})
            candidate_lines.append(
                {
                    "asin": parent_asin,
                    "offline_rank": rank,
                    "title": str(product.get("title", ""))[:220],
                    "categories": str(product.get("categories", ""))[:180],
                    "features": str(product.get("features", ""))[:260],
                    "store": str(product.get("store", ""))[:80],
                    "price": str(product.get("price", ""))[:40],
                }
            )

        context = {
            "latest_user_message": user_message[:500],
            "mode": state.get("mode"),
            "category_terms": state.get("category_anchor_terms", []),
            "constraints": state.get("constraints", {}),
            "latest_constraints": state.get("current_constraints", {}),
            "features": state.get("feature_phrases", []),
        }
        prompt = (
            "Rank the candidate products for the shopper's current intent. "
            "Respect explicit constraints and intent changes. Prefer exact "
            "product subtype and intended user over generic metadata. "
            "Return only a JSON array containing every candidate ASIN exactly "
            "once, best first. Do not add explanations or new ASINs.\n\n"
            f"SHOPPER_CONTEXT={json.dumps(context, ensure_ascii=False)}\n"
            f"CANDIDATES={json.dumps(candidate_lines, ensure_ascii=False)}"
        )
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a deterministic e-commerce reranker. "
                        "Output strict JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": 500,
            "stream": False,
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": str(uuid.uuid4()),
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=self.timeout,
            ) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            code = "unknown"
            message = ""
            try:
                error_body = json.loads(exc.read().decode("utf-8"))
                error = error_body.get("error", {})
                if isinstance(error, dict):
                    code = str(error.get("code") or error.get("type") or code)
                    message = str(error.get("message") or "")
                elif error:
                    message = str(error)
            except (OSError, ValueError, AttributeError):
                pass
            message = " ".join(message.split())[:200]
            self.last_error = f"http_{exc.code}:{code}"
            if message:
                self.last_error += f":{message}"
            return None, {}
        except urllib.error.URLError as exc:
            self.last_error = f"network_error:{type(exc.reason).__name__}"
            return None, {}
        except TimeoutError:
            self.last_error = "timeout"
            return None, {}
        except (OSError, ValueError) as exc:
            self.last_error = f"request_error:{type(exc).__name__}"
            return None, {}

        try:
            content = str(body["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError):
            self.last_error = "invalid_response_shape"
            return None, {}

        ordered = []
        seen = set()
        allowed_set = set(allowed)
        try:
            parsed = json.loads(content)
            raw_ids = parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            raw_ids = ASIN_RE.findall(content)

        for value in raw_ids:
            parent_asin = str(value)
            if parent_asin in allowed_set and parent_asin not in seen:
                ordered.append(parent_asin)
                seen.add(parent_asin)
        if not ordered:
            self.last_error = "no_valid_asins_in_model_output"
            return None, {}
        ordered.extend(parent_asin for parent_asin in allowed if parent_asin not in seen)

        raw_usage = body.get("usage") if isinstance(body, dict) else None
        usage: dict[str, int] = {}
        if isinstance(raw_usage, dict):
            for key in ("prompt_tokens", "completion_tokens"):
                value = raw_usage.get(key)
                if isinstance(value, int) and value >= 0:
                    usage[key] = value
        return ordered, usage


class Agent:
    """V5.10e plus an optional SwiftScale Top-20 reranking layer."""

    LLM_CANDIDATE_K = 20

    def __init__(self, catalog_path: str = "data/catalog.jsonl") -> None:
        self.offline = OfflineAgent(catalog_path)
        self.reranker = SwiftScaleReranker()
        self._llm_eligible: dict[str, bool] = {}

    def reset(self, session_id: str, user_profile: dict) -> None:
        self.offline.reset(session_id, user_profile)
        self._llm_eligible[session_id] = False

    def respond(
        self,
        session_id: str,
        user_message: str,
        turn: int,
        top_k: int,
    ) -> dict:
        offline_response = self.offline.respond(
            session_id,
            user_message,
            turn,
            max(top_k, self.LLM_CANDIDATE_K),
        )
        state = self.offline._session_state.get(session_id, {})
        mode = str(state.get("mode", "browsing"))
        if mode in {"buying", "intent_override"}:
            self._llm_eligible[session_id] = True

        candidates = list(offline_response.get("recommendations", []))
        if not self._llm_eligible.get(session_id, False):
            offline_response["recommendations"] = candidates[:top_k]
            return offline_response

        ordered, usage = self.reranker.rerank(
            user_message=user_message,
            state=state,
            candidates=candidates[: self.LLM_CANDIDATE_K],
            products=self.offline._products,
        )
        if ordered is None:
            offline_response["recommendations"] = candidates[:top_k]
            return offline_response

        by_id = {
            str(item.get("parent_asin")): item
            for item in candidates
            if item.get("parent_asin")
        }
        offline_response["recommendations"] = [
            by_id[parent_asin]
            for parent_asin in ordered[:top_k]
            if parent_asin in by_id
        ]
        offline_response["usage"] = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
        }
        return offline_response
