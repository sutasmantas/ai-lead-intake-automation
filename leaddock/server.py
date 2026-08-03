from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .domain import LeadDockError, LeadDockService


ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"


def make_handler(service: LeadDockService):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            print(f"[leaddock] {self.address_string()} {fmt % args}")

        def _json(self, status: int, body: object) -> None:
            raw = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(raw)

        def _body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 100_000:
                raise LeadDockError("payload_too_large", "request exceeds 100 KB", 413)
            try:
                value = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError as exc:
                raise LeadDockError("invalid_json", "body must be valid JSON") from exc
            if not isinstance(value, dict):
                raise LeadDockError("invalid_json", "body must be a JSON object")
            return value

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/api/state":
                tz_name = parse_qs(parsed.query).get("timezone", ["Europe/Vilnius"])[0]
                try:
                    self._json(200, service.state(tz_name))
                except LeadDockError as exc:
                    self._json(exc.status, {"error": exc.code, "message": str(exc)})
                return
            rel = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
            path = (PUBLIC / rel).resolve()
            if PUBLIC not in path.parents and path != PUBLIC:
                self._json(404, {"error": "not_found"})
                return
            if not path.is_file():
                self._json(404, {"error": "not_found"})
                return
            raw = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self) -> None:
            nonlocal service
            try:
                body = self._body()
                parts = [part for part in urlparse(self.path).path.split("/") if part]
                if parts == ["api", "reset"]:
                    service = LeadDockService(seed=True)
                    self._json(200, service.state())
                elif parts == ["api", "leads"]:
                    self._json(201, service.intake(body))
                elif len(parts) == 4 and parts[:2] == ["api", "leads"] and parts[3] == "approve":
                    self._json(200, service.approve(parts[2], str(body.get("slot_start", ""))))
                elif len(parts) == 4 and parts[:2] == ["api", "leads"] and parts[3] == "reject":
                    self._json(200, service.reject(parts[2], str(body.get("reason", ""))))
                elif len(parts) == 4 and parts[:2] == ["api", "dead-letters"] and parts[3] == "replay":
                    self._json(200, service.replay_dead_letter(parts[2]))
                else:
                    self._json(404, {"error": "not_found"})
            except LeadDockError as exc:
                self._json(exc.status, {"error": exc.code, "message": str(exc)})

    return Handler


def build_server(host: str = "127.0.0.1", port: int = 4310, seed: bool = True) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), make_handler(LeadDockService(seed=seed)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4310)
    args = parser.parse_args()
    server = build_server(args.host, args.port)
    print(f"LeadDock deterministic demo: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
