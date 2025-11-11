#!/usr/bin/env python3
"""
LAN Clipboard Webserver

- Browser UI:  http://<HOST>:<PORT>/
- Raw GET:     http://<HOST>:<PORT>/raw
- POST write:  curl -d "data=hello" http://<HOST>:<PORT>/
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import socket

# ---------------- CONFIG ----------------
HOST = "0.0.0.0"   # 0.0.0.0 = all interfaces; use "127.0.0.1" for local only
PORT = 8080
# ----------------------------------------

CLIPBOARD_DATA = ""


HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>LAN Clipboard</title>
  <style>
    body { font-family: sans-serif; background: #20232a; color: #fff; padding: 2rem; }
    h1 { margin-bottom: 0.5rem; }
    textarea { width: 100%; height: 150px; font-size: 1rem; padding: 0.5rem; }
    button { margin-top: 0.75rem; padding: 0.5rem 1rem; font-size: 1rem; cursor: pointer; }
    #status { margin-top: 0.75rem; font-size: 0.9rem; }
    .small { font-size: 0.8rem; opacity: 0.8; margin-top: 1rem; }
  </style>
</head>
<body>
  <h1>LAN Clipboard</h1>
  <p>Shared text across devices on this network.</p>
  <form id="clipform">
    <textarea name="data" id="data" placeholder="Type or paste text..."></textarea><br>
    <button type="submit">Save</button>
  </form>
  <div id="status"></div>
  <div class="small">
    <p><b>Raw GET:</b> <code>/raw</code><br>
    Example: <code>curl http://HOST:PORT/raw</code></p>
    <p><b>Write:</b> POST <code>data=...</code><br>
    Example: <code>curl -d "data=hello" http://HOST:PORT/</code></p>
  </div>
  <script>
    async function loadClipboard() {
      try {
        const res = await fetch('/raw');
        if (!res.ok) return;
        const txt = await res.text();
        document.getElementById('data').value = txt;
      } catch (e) {}
    }

    document.getElementById('clipform').addEventListener('submit', async (e) => {
      e.preventDefault();
      const form = e.target;
      const data = new URLSearchParams(new FormData(form));
      const res = await fetch('/', { method: 'POST', body: data });
      document.getElementById('status').textContent = res.ok ? 'Saved ✅' : 'Error ❌';
    });

    loadClipboard();
  </script>
</body>
</html>
"""


def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


class ClipboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global CLIPBOARD_DATA
        if self.path.startswith("/raw"):
            # return plain clipboard text
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(CLIPBOARD_DATA.encode("utf-8"))
            return

        # serve HTML UI
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

    def do_POST(self):
        global CLIPBOARD_DATA
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        parsed = urllib.parse.parse_qs(body)
        CLIPBOARD_DATA = parsed.get("data", [""])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args, **kwargs):
        # silence default logging
        return


def main():
    lan_ip = get_lan_ip()
    print("LAN Clipboard running:")
    print(f"  Browser:  http://{lan_ip}:{PORT}/")
    print(f"  Raw GET:  curl http://{lan_ip}:{PORT}/raw")
    print(f"  POST:     curl -d \"data=hello\" http://{lan_ip}:{PORT}/")
    print("Ctrl+C to stop.")
    HTTPServer((HOST, PORT), ClipboardHandler).serve_forever()


if __name__ == "__main__":
    main()
