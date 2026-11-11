"""Local demo server; standard library only."""
import argparse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import re
from urllib.parse import parse_qs, urlsplit

from model import (HISTORY, ZONE, audit, dashboard, export_csv, initial, notices,
                   preview, receipt, save_rules, settle_fixture)

ROOT = Path(__file__).parent
STATIC = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
          "/style.css": ("style.css", "text/css")}


class Handler(BaseHTTPRequestHandler):
    timeout = 5

    def respond(self, data, status=200, mime="application/json", attachment=False):
        body = json.dumps(data).encode() if mime == "application/json" else data
        self.send_response(status)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if attachment:
            self.send_header("Content-Disposition", 'attachment; filename="flowshift-simulated-savings.csv"')
        self.end_headers()
        self.wfile.write(body)

    def view(self):
        state = self.server.state
        return {**state, "dashboard": dashboard(state)}

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path in STATIC:
            name, mime = STATIC[url.path]
            self.respond((ROOT / name).read_bytes(), mime=mime)
        elif url.path == "/api/state":
            self.respond(self.view())
        elif url.path in ("/api/receipt", "/api/receipt.csv"):
            period = parse_qs(url.query, keep_blank_values=True).get("period", ["2026"])[0]
            if not re.fullmatch(r"[0-9]{4}(-(0[1-9]|1[0-2]))?", period):
                self.respond({"error": "Choose a year or month."}, 400)
                return
            report = receipt(self.server.state, period)
            if url.path.endswith(".csv"):
                audit(self.server.state, "receipt.exported", period)
                self.respond(export_csv(report).encode(), mime="text/csv", attachment=True)
            else:
                self.respond(report)
        else:
            self.respond({"error": "Not found"}, 404)

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 8192 or self.headers.get_content_type() != "application/json":
                raise ValueError("Expected a small JSON request.")
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError("Expected a JSON object.")
            state = self.server.state
            result = {}
            if self.path == "/api/rules":
                save_rules(state, data["version"], data["rules"])
            elif self.path == "/api/preview":
                result["preview"] = [preview(p, state["rules"]) for p in HISTORY]
                audit(state, "preview.ran", "Historical synthetic decisions; no actions executed.")
            elif self.path == "/api/notices":
                local = datetime.fromisoformat(data["at"])
                if local.tzinfo is not None or not 2026 == local.year:
                    raise ValueError("Enter a local 2026 demo date and time.")
                notices(state, local.replace(tzinfo=ZONE))
            elif self.path == "/api/fixture":
                action = data["action"]
                if action == "settle":
                    settle_fixture(state)
                elif action in ("stale", "refresh"):
                    state["fresh"] = action == "refresh"
                    audit(state, "fixture." + action, "Synthetic snapshot freshness updated.")
                else:
                    raise ValueError("Unknown demo event.")
            else:
                self.respond({"error": "Not found"}, 404)
                return
            self.respond({**self.view(), **result})
        except (KeyError, TypeError, ValueError) as exc:
            status = 409 if str(exc).startswith("Rules changed") else 400
            self.respond({"error": str(exc) or "Invalid request."}, status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    with HTTPServer(("127.0.0.1", args.port), Handler) as server:
        server.state = initial()
        audit(server.state, "snapshot.loaded", "snapshot-1 / baseline-v1 / synthetic fixtures")
        print(f"FlowShift demo: http://127.0.0.1:{server.server_port}", flush=True)
        server.serve_forever()
