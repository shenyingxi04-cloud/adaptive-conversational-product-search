from __future__ import annotations

import argparse
import json
import mimetypes
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

from submission.agent import Agent


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web_demo"


def public_state(state: dict) -> dict:
    constraints = {
        key: list(values)
        for key, values in state.get("constraints", {}).items()
        if values
    }
    return {
        "mode": state.get("mode", "browsing"),
        "constraints": constraints,
        "features": list(state.get("feature_phrases", []))[-8:],
        "override_active": bool(state.get("override_active")),
    }


class DemoApp:
    def __init__(self, catalog: Path) -> None:
        started = time.perf_counter()
        self.agent = Agent(catalog)
        self.startup_seconds = time.perf_counter() - started
        self.catalog_name = catalog.name
        self.lock = threading.Lock()

    def new_session(self) -> dict:
        session_id = uuid.uuid4().hex
        with self.lock:
            self.agent.reset(session_id, user_profile={"rating_style": "usually positive"})
        return {
            "session_id": session_id,
            "product_count": len(self.agent._products),
            "semantic_status": "Local embedding" if self.agent.semantic_model is not None else "Lexical fallback",
            "startup_seconds": round(self.startup_seconds, 3),
            "catalog": self.catalog_name,
        }

    def respond(self, payload: dict) -> dict:
        session_id = str(payload.get("session_id", ""))
        message = str(payload.get("message", "")).strip()
        turn = int(payload.get("turn", 1))
        top_k = max(1, min(int(payload.get("top_k", 6)), 10))
        if not session_id or not message:
            raise ValueError("session_id and message are required")

        started = time.perf_counter()
        with self.lock:
            result = self.agent.respond(session_id, message, turn, top_k)
            state = public_state(self.agent._session_state[session_id])
            cards = []
            for rank, rec in enumerate(result["recommendations"], start=1):
                asin = rec["parent_asin"]
                product = self.agent._products.get(asin, {})
                raw_feature = product.get("features") or product.get("description") or []
                if isinstance(raw_feature, list):
                    feature = raw_feature[0] if raw_feature else ""
                else:
                    feature = str(raw_feature)
                categories = product.get("categories") or []
                if isinstance(categories, str):
                    categories = [categories]
                elif not isinstance(categories, list):
                    categories = list(categories)
                cards.append({
                    "rank": rank,
                    "parent_asin": asin,
                    "title": product.get("title") or "Untitled product",
                    "store": product.get("store") or product.get("details", {}).get("Manufacturer") or "Independent seller",
                    "price": product.get("price"),
                    "rating": product.get("average_rating"),
                    "rating_count": product.get("rating_number"),
                    "categories": categories[-3:],
                    "feature": feature,
                })
        elapsed = time.perf_counter() - started
        return {
            "message": result["message"],
            "ask_attribute": result.get("ask_attribute"),
            "recommendations": cards,
            "state": state,
            "elapsed_seconds": round(elapsed, 3),
            "api_tokens": 0,
        }


def make_handler(app: DemoApp):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args) -> None:
            return

        def send_json(self, status: int, value: dict) -> None:
            raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length) or b"{}")
                if self.path == "/api/session":
                    self.send_json(200, app.new_session())
                elif self.path == "/api/respond":
                    self.send_json(200, app.respond(payload))
                else:
                    self.send_json(404, {"error": "not found"})
            except Exception as exc:
                self.send_json(400, {"error": str(exc)})

        def do_GET(self) -> None:
            request_path = urlparse(self.path).path
            if request_path == "/api/health":
                self.send_json(200, {"status": "ready"})
                return
            relative = "index.html" if request_path == "/" else request_path.lstrip("/")
            file_path = (WEB_ROOT / relative).resolve()
            if WEB_ROOT.resolve() not in file_path.parents or not file_path.is_file():
                self.send_error(404)
                return
            content = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(file_path.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the V5.12d recording UI.")
    parser.add_argument("--catalog", type=Path, default=Path("data/catalog_copy.jsonl"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    catalog = args.catalog.resolve()
    if not catalog.is_file():
        raise FileNotFoundError(f"Catalog not found: {catalog}")
    app = DemoApp(catalog)
    server = HTTPServer((args.host, args.port), make_handler(app))
    url = f"http://{args.host}:{args.port}"
    print(f"Demo UI ready: {url}")
    print(f"Catalog: {len(app.agent._products):,} products | startup {app.startup_seconds:.2f}s")
    print("Press Ctrl+C to stop.")
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
