#!/usr/bin/env python3
"""LocalMate: a small local-first Ollama assistant."""
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).parent
HOST = os.getenv("LOCALMATE_HOST", "127.0.0.1")
PORT = int(os.getenv("LOCALMATE_PORT", "8765"))
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
MAX_BODY = 1_000_000


def json_response(handler, status, value):
    body = json.dumps(value).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(body)


def web_search(query):
    """Explicitly invoked opt-in search. No call is made during normal chat."""
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    request = urllib.request.Request(url, headers={"User-Agent": "LocalMate/0.1 (personal search)"})
    with urllib.request.urlopen(request, timeout=12) as response:
        page = response.read(1_000_000).decode("utf-8", "replace")
    links = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', page, re.I | re.S)
    snippets = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', page, re.I | re.S)
    results = []
    for i, (href, title) in enumerate(links[:6]):
        clean = lambda s: html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
        results.append({"title": clean(title), "url": html.unescape(href), "snippet": clean(snippets[i]) if i < len(snippets) else ""})
    return results


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Avoid logging user prompts and email content.
        if self.path.split("?", 1)[0] in ("/api/chat", "/api/search"):
            return
        super().log_message(fmt, *args)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/status":
            json_response(self, 200, {"model": MODEL, "ollama": OLLAMA_URL, "internet": "off unless you explicitly search"})
            return
        file_path = {"/": "index.html", "/manifest.webmanifest": "manifest.webmanifest", "/sw.js": "sw.js", "/app.js": "app.js", "/style.css": "style.css"}.get(path)
        if not file_path:
            self.send_error(404)
            return
        data = (ROOT / "static" / file_path).read_bytes()
        content_type = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".webmanifest": "application/manifest+json"}[Path(file_path).suffix]
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path not in ("/api/chat", "/api/search"):
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > MAX_BODY:
                return json_response(self, 413, {"error": "Request size is invalid."})
            data = json.loads(self.rfile.read(length))
            if self.path == "/api/search":
                query = str(data.get("query", "")).strip()[:300]
                if not query:
                    return json_response(self, 400, {"error": "Enter a search query."})
                return json_response(self, 200, {"results": web_search(query)})
            messages = data.get("messages", [])
            if not isinstance(messages, list) or not messages or len(messages) > 40:
                return json_response(self, 400, {"error": "Send a conversation with up to 40 messages."})
            safe_messages = []
            for message in messages:
                if not isinstance(message, dict) or message.get("role") not in ("user", "assistant"):
                    continue
                safe_messages.append({"role": message["role"], "content": str(message.get("content", ""))[:12000]})
            req = urllib.request.Request(OLLAMA_URL + "/api/chat", data=json.dumps({"model": MODEL, "messages": safe_messages, "stream": False}).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as response:
                answer = json.loads(response.read().decode()).get("message", {}).get("content", "")
            return json_response(self, 200, {"reply": answer})
        except urllib.error.URLError as exc:
            return json_response(self, 502, {"error": "Could not reach Ollama. Make sure it is running and the model is installed.", "detail": str(exc.reason)[:180]})
        except (ValueError, json.JSONDecodeError):
            return json_response(self, 400, {"error": "Invalid request."})
        except Exception as exc:
            return json_response(self, 500, {"error": str(exc)[:200]})


if __name__ == "__main__":
    if "--host" in sys.argv:
        HOST = "0.0.0.0"
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"LocalMate listening on http://{HOST}:{PORT} (Ollama: {OLLAMA_URL}, model: {MODEL})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping LocalMate.")
        server.server_close()
