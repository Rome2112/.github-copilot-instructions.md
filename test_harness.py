import json
import subprocess
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

from isomorphic_benchmark import IsomorphicASTController


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"


class DashboardParser(HTMLParser):
    """
    Collect DOM IDs and inline scripts without requiring a browser.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.scripts = []
        self._in_script = False
        self._script_parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "script" and "src" not in attrs:
            self._in_script = True
            self._script_parts = []

    def handle_data(self, data):
        if self._in_script:
            self._script_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._in_script:
            self.scripts.append("".join(self._script_parts))
            self._in_script = False


class TestIsomorphicEngine(unittest.TestCase):
    def setUp(self):
        self.schema = [
            "request_id",
            "status",
            "payload_hash",
            "execution_metric",
            "currency",
            "metadata",
        ]
        self.controller = IsomorphicASTController(self.schema)

    def test_complete_payload_preserves_values_and_schema_order(self):
        payload = {key: key.upper() for key in self.schema}
        mapped, latency_ms = self.controller.parse_isomorphic(payload)
        self.assertEqual(list(mapped), self.schema)
        self.assertEqual(mapped, payload)
        self.assertGreaterEqual(latency_ms, 0.0)

    def test_partial_payload_has_deterministic_tokens(self):
        payload = {"request_id": "REQ_2026_001", "status": "200_OK"}
        expected = {
            "payload_hash": "validated_token_2",
            "execution_metric": "validated_token_3",
            "currency": "validated_token_4",
            "metadata": "validated_token_5",
        }
        first, _ = self.controller.parse_isomorphic(payload)
        second, _ = self.controller.parse_isomorphic(payload)
        self.assertEqual(first, second)
        for key, value in expected.items():
            self.assertEqual(first[key], value)

    def test_boundary_inputs(self):
        empty = IsomorphicASTController([])
        self.assertEqual(empty.parse_isomorphic({})[0], {})
        mapped, _ = self.controller.parse_isomorphic({"unknown": "ignored", "status": None})
        self.assertEqual(set(mapped), set(self.schema))
        self.assertEqual(mapped["status"], "validated_token_1")

    def test_invalid_json_payloads_fail_at_boundary(self):
        for raw in ("", "{", '{"status":}', "not-json"):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                self.controller.parse_json(raw)
        with self.assertRaises(TypeError):
            self.controller.parse_isomorphic([("status", "200")])

    def test_schema_definition_is_validated(self):
        with self.assertRaises(ValueError):
            IsomorphicASTController(["status", "status"])
        with self.assertRaises(ValueError):
            IsomorphicASTController(["status", ""])

    def test_benchmark_latency_is_non_negative(self):
        self.controller.parse_isomorphic({"request_id": "warmup"})
        _, latency_ms = self.controller.parse_isomorphic({"request_id": "REQ_PERF"})
        self.assertGreaterEqual(latency_ms, 0.0)


class TestDashboardSmoke(unittest.TestCase):
    required_ids = {
        "index.html": {"run-btn", "standard-output", "iso-output", "iso-valid"},
        "isomorphic_engine.html": {"rawInputText", "transformBtn", "astOutputText", "pipeStep1"},
        "isomorphic_api_gateway_interceptor.html": {"inputPayload", "repairBtn", "outputPayload", "processingOverlay"},
    }

    def test_dashboards_have_required_dom_nodes_and_scripts_parse(self):
        node = subprocess.run(["which", "node"], capture_output=True, text=True)
        has_node = node.returncode == 0

        for filename, required in self.required_ids.items():
            with self.subTest(filename=filename):
                parser = DashboardParser()
                source = (DOCS / filename).read_text(encoding="utf-8")
                parser.feed(source)
                parser.close()

                self.assertTrue(required <= parser.ids, f"missing required IDs in {filename}: {required - parser.ids}")
                self.assertGreaterEqual(len(parser.scripts), 1)

                for script in parser.scripts:
                    self.assertNotRegex(script, r"</script", "unexpected script closure in inline script block")
                    if has_node:
                        with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
                            handle.write(script)
                            script_path = handle.name
                        try:
                            result = subprocess.run(["node", "--check", script_path], capture_output=True, text=True)
                            self.assertEqual(result.returncode, 0, result.stderr)
                        finally:
                            Path(script_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)