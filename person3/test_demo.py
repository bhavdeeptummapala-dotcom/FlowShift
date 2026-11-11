import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from model import DEFAULT, HISTORY, dashboard, initial, preview, save_rules


class RulesTests(unittest.TestCase):
    def test_exact_ceiling_and_aggregate(self):
        self.assertTrue(preview(HISTORY[0], DEFAULT)["eligible"])
        self.assertFalse(preview(HISTORY[0], {**DEFAULT, "ceiling": 249999})["eligible"])
        self.assertFalse(preview(HISTORY[1], DEFAULT)["eligible"])
        self.assertTrue(all(not preview(plan, DEFAULT)["eligible"] for plan in HISTORY[1:]))

    def test_invalid_rules_never_change_active_state(self):
        state = initial()
        with self.assertRaises(ValueError):
            save_rules(state, 1, {**DEFAULT, "reserve": -1})
        self.assertEqual(state["version"], 1)
        save_rules(state, 1, {**DEFAULT, "reserve": 300000})
        with self.assertRaises(ValueError):
            save_rules(state, 1, DEFAULT)
        self.assertEqual(dashboard(state)["reserve"], 300000)


class DemoFlowTests(unittest.TestCase):
    def test_demo_http_flow(self):
        root = Path(__file__).parent
        with subprocess.Popen([sys.executable, str(root / "server.py"), "--port", "0"],
                              stdout=subprocess.PIPE, text=True) as server:
            try:
                url = server.stdout.readline().split()[-1]

                def call(path, data=None):
                    req = Request(url + path, None if data is None else json.dumps(data).encode(),
                                  {"Content-Type": "application/json"})
                    with urlopen(req, timeout=5) as response:
                        body = response.read().decode()
                        return json.loads(body) if response.headers.get_content_type() == "application/json" else body

                self.assertIn("Synthetic data", call("/"))
                self.assertIn("Run historical preview", call("/app.js"))
                original = call("/api/state")
                self.assertEqual(original["dashboard"]["safe"], 0)
                self.assertEqual(len(original["dashboard"]["days"]), 14)
                self.assertEqual(call("/api/receipt")["rows"], [])
                new = call("/api/rules", {"version": 1, "rules": {**DEFAULT, "routine": False}})
                self.assertEqual(new["version"], 2)
                with self.assertRaises(HTTPError) as error:
                    call("/api/rules", {"version": 1, "rules": DEFAULT})
                self.assertEqual(error.exception.code, 409)
                for _ in range(2):
                    notified = call("/api/notices", {"at": "2026-04-20T09:00"})
                self.assertEqual([n["key"] for n in notified["notices"]], ["payroll-0423"])
                self.assertEqual(sum(p["eligible"] for p in call("/api/preview", {})["preview"]), 1)
                stale = call("/api/fixture", {"action": "stale"})
                self.assertIsNone(stale["dashboard"]["safe"])
                with self.assertRaises(HTTPError):
                    call("/api/fixture", {"action": "settle"})
                call("/api/fixture", {"action": "refresh"})
                for _ in range(2):
                    settled = call("/api/fixture", {"action": "settle"})
                self.assertEqual(settled["dashboard"]["safe"], 83316)
                report = call("/api/receipt?period=2026-04")
                self.assertEqual((report["gross"], report["cost"], report["net"]), (3500, 1884, 1616))
                self.assertEqual(call("/api/receipt?period=2026-05")["net"], 0)
                export = list(csv.DictReader(io.StringIO(call("/api/receipt.csv?period=2026"))))
                self.assertEqual(export[-1]["Net cents"], "1616")
                events = [entry["event"] for entry in call("/api/state")["audit"]]
                self.assertEqual(events.count("fixture.settled"), 1)
                self.assertEqual(events[-1], "receipt.exported")
            finally:
                server.terminate()


if __name__ == "__main__":
    unittest.main()
