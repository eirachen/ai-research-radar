#!/usr/bin/env python3
"""
AI Research Radar - Lighthouse Server
- Serves static files from /var/www/ai-radar/
- GET/POST /talent-notes.json for talent data
- POST /deploy with JSON {"file":"index.html","content":"..."} to update files
- POST /pull-github to pull latest index.html from GitHub raw
- CORS enabled
"""
import json, os, urllib.request
from http.server import HTTPServer, SimpleHTTPRequestHandler

SERVE_DIR = "/var/www/ai-radar"
PORT = 8800
GITHUB_RAW = "https://raw.githubusercontent.com/eirachen/ai-research-radar/main/"

os.chdir(SERVE_DIR)

class Handler(SimpleHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        if self.path == "/talent-notes.json":
            try:
                data = json.loads(body)
                with open("talent-notes.json", "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self._ok('{"ok":true}')
            except Exception as e:
                self._err(str(e))

        elif self.path == "/deploy":
            # Deploy a file: {"file":"index.html", "content":"..."}
            try:
                data = json.loads(body)
                fname = os.path.basename(data["file"])  # Security: only filename
                content = data["content"]
                filepath = os.path.join(SERVE_DIR, fname)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                self._ok(json.dumps({"ok": True, "file": fname, "size": len(content)}))
            except Exception as e:
                self._err(str(e))

        elif self.path == "/pull-github":
            # Pull latest files from GitHub raw
            try:
                files = ["index.html"]
                results = []
                for fn in files:
                    url = GITHUB_RAW + fn
                    req = urllib.request.Request(url, headers={"User-Agent": "ai-radar-server"})
                    resp = urllib.request.urlopen(req, timeout=30)
                    content = resp.read()
                    filepath = os.path.join(SERVE_DIR, fn)
                    with open(filepath, "wb") as f:
                        f.write(content)
                    results.append({"file": fn, "size": len(content)})
                self._ok(json.dumps({"ok": True, "updated": results}))
            except Exception as e:
                self._err(str(e))
        else:
            self.send_response(404)
            self._cors()
            self.end_headers()

    def _ok(self, body):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def _err(self, msg):
        self.send_response(400)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps({"error": msg}).encode("utf-8"))

    def end_headers(self):
        self._cors()
        super().end_headers()

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

print(f"AI Radar server on port {PORT}, serving {SERVE_DIR}")
HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
