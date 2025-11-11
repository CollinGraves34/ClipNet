#!/usr/bin/env python3
"""
serve_file.py

Usage:
  python serve_file.py            # serves ./index.html (if present) on 0.0.0.0:8080
  python serve_file.py path/to/file.html --port 8080
  python serve_file.py --dir /path/to/dir --port 8080  # serve whole directory
"""

import argparse
import http.server
import socket
import socketserver
from pathlib import Path
import sys

def local_ip():
    # determine a likely LAN IP address (doesn't send packets)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "0.0.0.0"
    finally:
        s.close()

class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

def run_server(serve_dir: Path, port: int, single_file: Path | None):
    # use SimpleHTTPRequestHandler's 'directory' feature (py3.7+)
    handler_class = http.server.SimpleHTTPRequestHandler

    if single_file:
        # Change working directory to the file's parent and rewrite requests for / to the file
        singleton_name = single_file.name
        serve_dir = single_file.parent

        class SingleFileHandler(handler_class):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(serve_dir), **kwargs)

            def do_GET(self):
                if self.path == "/" or self.path == "/index.html":
                    self.path = "/" + singleton_name
                return super().do_GET()

            def list_directory(self, path):
                self.send_error(403, "Directory listing not allowed")
        handler = SingleFileHandler
    else:
        handler = lambda *args, **kwargs: handler_class(*args, directory=str(serve_dir), **kwargs)

    addr = ("0.0.0.0", port)
    with ThreadingTCPServer(addr, handler) as httpd:
        print(f"Serving directory: {serve_dir}")
        print(f"URL (this machine):  http://localhost:{port}/")
        print(f"URL (LAN devices):   http://{local_ip()}:{port}/")
        print("Press Ctrl-C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping server")
            httpd.server_close()

def main():
    p = argparse.ArgumentParser()
    p.add_argument("file", nargs="?", help="HTML file to serve (optional). If omitted, tries ./index.html or serves directory")
    p.add_argument("--dir", help="Directory to serve (optional). If set, serves the directory.")
    p.add_argument("--port", "-p", type=int, default=8080, help="Port (default 8080)")
    args = p.parse_args()

    if args.dir:
        serve_dir = Path(args.dir).resolve()
        if not serve_dir.is_dir():
            print("Error: --dir must be an existing directory", file=sys.stderr); sys.exit(1)
        run_server(serve_dir, args.port, None)
        return

    if args.file:
        f = Path(args.file).resolve()
        if not f.is_file():
            print("Error: file not found:", f, file=sys.stderr); sys.exit(1)
        run_server(f.parent, args.port, f)
        return

    # no args: try index.html in cwd; otherwise serve cwd
    cwd = Path.cwd()
    idx = cwd / "index.html"
    if idx.is_file():
        run_server(cwd, args.port, idx)
    else:
        run_server(cwd, args.port, None)

if __name__ == "__main__":
    main()
