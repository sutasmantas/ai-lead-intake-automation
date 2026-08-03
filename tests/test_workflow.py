import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = json.loads((ROOT / "workflows" / "leaddock-intake-booking.json").read_text(encoding="utf-8"))

    def test_is_importable_n8n_shape(self):
        self.assertIsInstance(self.workflow["nodes"], list)
        self.assertIsInstance(self.workflow["connections"], dict)
        self.assertFalse(self.workflow["active"])

    def test_central_path_nodes_exist(self):
        names = {node["name"] for node in self.workflow["nodes"]}
        self.assertTrue({"Lead intake webhook", "Normalize + validate lead", "LeadDock intake contract", "Needs approval?", "CRM + booking + handoff contract"} <= names)

    def test_only_generic_local_http_contracts_are_claimed(self):
        boundary = self.workflow["meta"]["boundary"]
        self.assertIn("no named SaaS", boundary)
        urls = [node["parameters"].get("url", "") for node in self.workflow["nodes"]]
        self.assertTrue(all("hubspot" not in url.lower() and "salesforce" not in url.lower() and "calendly" not in url.lower() for url in urls))

    def test_foundation_provenance_is_pinned(self):
        self.assertIn("01383a9419a1b72cff553ec887501b9d82907be9", self.workflow["meta"]["foundation"])


if __name__ == "__main__":
    unittest.main()
