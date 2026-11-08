"""Small standard-library HTTP service for infrastructure demonstrations."""
import json
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOG = logging.getLogger("infra_app")
STARTED = time.monotonic()
LOCK = threading.Lock()
REQUESTS = 0


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global REQUESTS
        with LOCK:
            REQUESTS += 1
            count = REQUESTS
        path = self.path.split("?", 1)[0]
        if path == "/health":
            status, content_type, body = 200, "application/json", b'{"status":"ok"}\n'
        elif path == "/metrics":
            status, content_type = 200, "text/plain; version=0.0.4; charset=utf-8"
            body = (
                "# HELP demo_app_up Application process is serving requests.\n"
                "# TYPE demo_app_up gauge\ndemo_app_up 1\n"
                "# HELP demo_http_requests_total Total GET requests including scrapes.\n"
                "# TYPE demo_http_requests_total counter\n"
                f"demo_http_requests_total {count}\n"
                "# HELP demo_uptime_seconds Process uptime in seconds.\n"
                "# TYPE demo_uptime_seconds gauge\n"
                f"demo_uptime_seconds {time.monotonic() - STARTED:.3f}\n"
            ).encode()
        elif path == "/":
            status, content_type, body = 200, "application/json", b'{"service":"linux-infrastructure-automation"}\n'
        else:
            status, content_type, body = 404, "application/json", b'{"error":"not found"}\n'
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        LOG.info(json.dumps({"event": "request", "method": "GET", "path": path,
                             "status": status, "client": self.client_address[0]}))

    def log_message(self, *_args):
        # Suppress unstructured BaseHTTPRequestHandler access logging.
        pass


def main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    address = (os.environ.get("APP_HOST", "127.0.0.1"), int(os.environ.get("APP_PORT", "8000")))
    LOG.info(json.dumps({"event": "started", "address": address}))
    ThreadingHTTPServer(address, Handler).serve_forever()


if __name__ == "__main__":
    main()
