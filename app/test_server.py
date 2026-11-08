import concurrent.futures
import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from server import Handler


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def get(self, path):
        return urllib.request.urlopen(self.base + path, timeout=5)

    def test_health(self):
        with self.get("/health?probe=1") as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(json.load(r), {"status": "ok"})

    def test_root(self):
        with self.get("/") as r:
            self.assertIn("service", json.load(r))

    def test_missing(self):
        with self.assertRaises(urllib.error.HTTPError) as e:
            self.get("/missing")
        self.assertEqual(e.exception.code, 404)

    def test_metrics_increase(self):
        def counter():
            with self.get("/metrics") as r:
                self.assertIn("text/plain", r.headers["Content-Type"])
                lines = r.read().decode().splitlines()
            return int(next(x.split()[1] for x in lines if x.startswith("demo_http_requests_total ")))
        before = counter()
        with self.get("/health") as r:
            r.read()
        self.assertGreaterEqual(counter(), before + 2)

    def test_concurrent_health(self):
        def request(_):
            with self.get("/health") as r:
                return r.status
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            self.assertEqual(list(pool.map(request, range(12))), [200] * 12)

    def test_structured_log(self):
        with self.assertLogs("infra_app", level="INFO") as captured:
            with self.get("/health") as r:
                r.read()
            # Wait for the handler to complete its log after writing the body.
            import time
            for _ in range(100):
                if captured.records:
                    break
                time.sleep(0.01)
        record = json.loads(captured.records[-1].getMessage())
        self.assertEqual(record["status"], 200)
        self.assertEqual(record["event"], "request")


if __name__ == "__main__":
    unittest.main()
