import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from leaddock.server import build_server


class HttpSliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = build_server(port=0, seed=True)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.request("/api/reset", "POST", {})

    def request(self, path, method="GET", body=None):
        raw = None if body is None else json.dumps(body).encode()
        req = Request(f"http://127.0.0.1:{self.port}{path}", data=raw, method=method, headers={"Content-Type": "application/json"})
        with urlopen(req) as response:
            return response.status, json.load(response)

    def test_seeded_state_is_no_key_and_has_availability(self):
        status, state = self.request("/api/state")
        self.assertEqual(status, 200)
        self.assertEqual(len(state["leads"]), 4)
        self.assertGreater(len(state["availability"]), 0)
        self.assertIn("no external credentials", state["boundaries"])

    def test_http_intake_and_approve(self):
        lead = {"name":"HTTP Lead","email":"http@example.com","company":"HTTP Co","need":"booking integration","budget":8000,"company_size":20,"timeline":"now","timezone":"Europe/Vilnius"}
        status, intake = self.request("/api/leads", "POST", lead)
        self.assertEqual(status, 201)
        _, state = self.request("/api/state")
        slot = state["availability"][0]["start"]
        status, result = self.request(f"/api/leads/{intake['lead']['id']}/approve", "POST", {"slot_start":slot})
        self.assertEqual(status, 200)
        self.assertEqual(result["lead"]["status"], "booked")

    def test_invalid_payload_returns_typed_error(self):
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/leads", "POST", {"email":"bad"})
        self.assertEqual(caught.exception.code, 400)
        body = json.loads(caught.exception.read())
        self.assertEqual(body["error"], "invalid_lead")

    def test_static_ui_is_served(self):
        with urlopen(f"http://127.0.0.1:{self.port}/") as response:
            html = response.read().decode()
        self.assertIn("Appointment ledger", html)
        self.assertIn("ARRIVAL TAPE", html)


if __name__ == "__main__":
    unittest.main()
