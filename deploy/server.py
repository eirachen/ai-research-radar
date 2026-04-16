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

    def _no_cache(self):
        """禁止浏览器缓存，每次都拿最新文件"""
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")

    def do_GET(self):
        # 去掉查询参数（前端可能加了 ?_t=xxx 防缓存）
        if '?' in self.path:
            self.path = self.path.split('?')[0]
        super().do_GET()

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
            # Supports subdirectories: reports/arxiv-daily.json
            try:
                data = json.loads(body)
                raw_path = data["file"]
                # Security: only allow known safe paths
                ALLOWED_PREFIXES = ["reports/", ""]
                safe = False
                for prefix in ALLOWED_PREFIXES:
                    if raw_path.startswith(prefix):
                        # No .. traversal allowed
                        if ".." not in raw_path:
                            safe = True
                            break
                if not safe:
                    raise ValueError(f"Path not allowed: {raw_path}")
                content = data["content"]
                filepath = os.path.join(SERVE_DIR, raw_path)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                self._ok(json.dumps({"ok": True, "file": raw_path, "size": len(content)}))
            except Exception as e:
                self._err(str(e))

        elif self.path == "/scholar-proxy":
            # Proxy a Google Scholar request from local machine
            # Only allows scholar.google.com queries, rate-limited
            try:
                data = json.loads(body)
                scholar_url = data.get("url", "")
                # Security: only allow Google Scholar URLs
                if not scholar_url.startswith("https://scholar.google.com/"):
                    raise ValueError("Only scholar.google.com URLs allowed")
                # Rate limit: simple in-memory counter
                import time
                now = time.time()
                if not hasattr(Handler, '_scholar_reqs'):
                    Handler._scholar_reqs = []
                # Clean old entries (last 60 seconds)
                Handler._scholar_reqs = [t for t in Handler._scholar_reqs if now - t < 60]
                if len(Handler._scholar_reqs) >= 10:
                    raise ValueError("Rate limit: max 10 Scholar requests per minute")
                Handler._scholar_reqs.append(now)
                # Forward request
                req = urllib.request.Request(scholar_url, headers={
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept-Language": "en-US,en;q=0.9",
                })
                resp = urllib.request.urlopen(req, timeout=20)
                html = resp.read().decode("utf-8", errors="replace")
                self._ok(json.dumps({"ok": True, "html": html, "status": resp.status}))
            except Exception as e:
                self._err(str(e))

        elif self.path == "/pull-github":
            # Pull latest files from GitHub raw
            try:
                files = ["index.html", "reports/arxiv-daily.json", "reports/index.json"]
                results = []
                for fn in files:
                    url = GITHUB_RAW + fn
                    req = urllib.request.Request(url, headers={"User-Agent": "ai-radar-server"})
                    resp = urllib.request.urlopen(req, timeout=30)
                    content = resp.read()
                    filepath = os.path.join(SERVE_DIR, fn)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
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
        # 对 HTML/JSON 请求禁止缓存
        path = getattr(self, 'path', '').split('?')[0]
        if path.endswith(('.html', '.json')) or path == '/':
            self._no_cache()
        self._cors()
        super().end_headers()

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

print(f"AI Radar server on port {PORT}, serving {SERVE_DIR}")
HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
