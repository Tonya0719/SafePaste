from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .pipeline import SafePastePipeline
from .redaction import restore


STATIC = Path(__file__).with_name("static") / "index.html"
MODES = ["presidio", "regex", "regex-legacy", "gliner", "hybrid"]


def make_handler(pipeline: SafePastePipeline):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path != "/":
                self._send(404, b"Not found", "text/plain")
                return
            self._send(200, STATIC.read_bytes(), "text/html; charset=utf-8")

        def do_POST(self):
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 100_000:
                    raise ValueError("Input is too large")
                payload = json.loads(self.rfile.read(length))
                if self.path == "/api/analyze":
                    response = pipeline.analyze(str(payload.get("text", "")))
                elif self.path == "/api/restore":
                    response = {"text": restore(str(payload.get("text", "")), dict(payload.get("restore_map", {})), payload.get("selected"))}
                else:
                    self._send(404, b"Not found", "text/plain")
                    return
                self._send(200, json.dumps(response, ensure_ascii=False).encode(), "application/json; charset=utf-8")
            except (ValueError, TypeError, json.JSONDecodeError, RuntimeError) as exc:
                self._send(400, json.dumps({"error": str(exc)}).encode(), "application/json")

        def log_message(self, format, *args):
            # Deliberately avoid logging request bodies or detected PII.
            return

    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--mode", choices=MODES, default="hybrid")
    args = parser.parse_args()
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("SafePaste only permits loopback binding")
    server = ThreadingHTTPServer((args.host, args.port), make_handler(SafePastePipeline(args.mode)))
    print(f"SafePaste running locally at http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
