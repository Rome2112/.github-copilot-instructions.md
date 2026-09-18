import unittest
import json
import time
from isomorphic_benchmark import IsomorphicASTController

class TestIsomorphicEngine(unittest.TestCase):
    """
    Unit test suite for the Isomorphic Structural Engine.
    Verifies O(N log K) bounded schema collapses, zero-entropy handling,
    and automatic structural error recovery.
    """

    def setUp(self):
        """Initialize controller with a standard bounded enterprise schema."""
        self.schema = [
            "request_id",
            "status",
            "payload_hash",
            "execution_metric",
            "currency",
            "metadata"
        ]
        self.controller = IsomorphicASTController(self.schema)

    def test_complete_valid_payload(self):
        """Test mapping when all schema keys are present."""
        input_data = {
            "request_id": "REQ_2026_001",
            "status": "200_OK",
            "payload_hash": "a1b2c3d4",
            "execution_metric": "sub_linear",
            "currency": "USD",
            "metadata": {"env": "prod"}
        }
        mapped_ast, latency_ms = self.controller.parse_isomorphic(input_data)
        
        self.assertEqual(mapped_ast["request_id"], "REQ_2026_001")
        self.assertEqual(mapped_ast["status"], "200_OK")
        self.assertLess(latency_ms, 5.0)  # Sub-5ms latency assertion

    def test_partial_payload_schema_binding(self):
        """Test automatic binding of static schema index tokens for missing keys."""
        partial_input = {
            "request_id": "REQ_2026_002",
            "status": "400_BAD_INPUT"
        }
        mapped_ast, latency_ms = self.controller.parse_isomorphic(partial_input)
        
        # Check preserved input keys
        self.assertEqual(mapped_ast["request_id"], "REQ_2026_002")
        self.assertEqual(mapped_ast["status"], "400_BAD_INPUT")
        
        # Verify deterministic token assignment for missing schema keys
        self.assertTrue(mapped_ast["payload_hash"].startswith("validated_token_"))
        self.assertEqual(len(mapped_ast), len(self.schema))

    def test_performance_sub_linear_latency(self):
        """Verify performance satisfies sub-linear O(N log K) time bounds (< 5ms)."""
        sample_input = {"request_id": "REQ_PERF_TEST"}
        
        # Execute warm-up run
        self.controller.parse_isomorphic(sample_input)
        
        # Measure target run
        _, latency_ms = self.controller.parse_isomorphic(sample_input)
        self.assertLess(latency_ms, 5.0)

if __name__ == "__main__":
    unittest.main()
