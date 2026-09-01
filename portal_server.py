import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app_config import DEFAULT_CONFIG_PATH, load_config
import registry


class RootRewriteHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, default_file="portal.html", **kwargs):
        self._default_file = default_file
        super().__init__(*args, directory=directory, **kwargs)

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict:
        content_length = self.headers.get("Content-Length")
        if not content_length:
            return {}
        try:
            raw = self.rfile.read(int(content_length))
        except ValueError:
            return {}
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/servers":
            self._send_json(200, registry.list_active())
            return
        if path in {"", "/"}:
            self.path = f"/{self._default_file}"
        return super().do_GET()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/register":
            payload = self._read_json_body()
            try:
                registry.register(payload)
            except ValueError as exc:
                self._send_json(400, {"ok": False, "error": str(exc)})
                return
            self._send_json(200, {"ok": True})
            return
        if path.startswith("/api/servers/") and "/actions/" in path:
            _, _, remainder = path.partition("/api/servers/")
            server_id, _, action = remainder.partition("/actions/")
            entry = registry.get(server_id)
            if entry is None:
                self._send_json(404, {"ok": False, "error": f"unknown server: {server_id}"})
                return
            if action not in registry.action_names(entry):
                self._send_json(400, {"ok": False, "error": f"unsupported action: {action}"})
                return
            # Forward whatever the browser actually posted -- e.g. a
            # parameterized action's param values. The portal never
            # inspects or validates the body; that's the adapter's job.
            body = self._read_json_body()
            request = Request(
                f"{entry['base_url']}/arcade/actions/{action}",
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            # Generous timeout: an adapter action (e.g. a container stop)
            # can legitimately take as long as that service's own graceful
            # shutdown grace period, which may be 30s+.
            try:
                with urlopen(request, timeout=45) as response:
                    body = response.read()
                    status = response.status
            except URLError as exc:
                self._send_json(502, {"ok": False, "error": f"adapter unreachable: {exc}"})
                return
            try:
                payload = json.loads(body.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                payload = {"ok": status < 400}
            if payload.get("ok") and payload.get("status"):
                registry.update_status(server_id, str(payload["status"]))
            self._send_json(status, payload)
            return
        self.send_error(405)


def main() -> None:
    load_config(DEFAULT_CONFIG_PATH)
    web_dir = Path(__file__).resolve().parent / "web"
    port = int(os.environ.get("PORTAL_PORT", "20032"))
    handler = partial(RootRewriteHandler, directory=str(web_dir), default_file="portal.html")
    server = ThreadingHTTPServer(("0.0.0.0", port), handler)
    print(f"Portal server listening on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
