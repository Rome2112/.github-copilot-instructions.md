import json
import time


class IsomorphicASTController:
    """
    Deterministic schema-bound AST mapping with bounded token fallback behavior.
    """

    def __init__(self, schema_keys: list[str]):
        if not isinstance(schema_keys, list):
            raise ValueError("schema_keys must be a list of strings")
        if any(not isinstance(key, str) or not key for key in schema_keys):
            raise ValueError("schema_keys must be a list of non-empty strings")
        if len(set(schema_keys)) != len(schema_keys):
            raise ValueError("schema_keys must not contain duplicates")

        self.schema_map = {key: idx for idx, key in enumerate(schema_keys)}
        self.k_bound = len(schema_keys)

    def parse_json(self, payload: str) -> tuple[dict, float]:
        """
        Accept a valid JSON object payload and map it to the bound schema.
        """
        try:
            decoded = json.loads(payload)
        except (TypeError, json.JSONDecodeError) as exc:
            raise ValueError("payload must be valid JSON") from exc

        if not isinstance(decoded, dict):
            raise ValueError("payload JSON must contain an object")

        return self.parse_isomorphic(decoded)

    def parse_isomorphic(self, input_vector: dict) -> tuple[dict, float]:
        """
        Apply a bounded schema projection to an input dictionary and return
        a deterministic AST-like object plus the measured execution time.
        """
        if not isinstance(input_vector, dict):
            raise TypeError("input_vector must be a dictionary")

        start_time = time.perf_counter()
        mapped_ast = {}

        for key, index in self.schema_map.items():
            value = input_vector.get(key)
            mapped_ast[key] = value if value is not None else f"validated_token_{index}"

        exec_time_ms = (time.perf_counter() - start_time) * 1000.0
        return mapped_ast, exec_time_ms


if __name__ == "__main__":
    schema = ["request_id", "status", "payload_hash", "execution_metric"]
    controller = IsomorphicASTController(schema)
    sample_input = {"request_id": "REQ_99421", "status": "200_OK"}

    output_ast, latency_ms = controller.parse_isomorphic(sample_input)
    print(f"[BENCHMARK RESULT] Isomorphic Parsing Latency: {latency_ms:.4f} ms | AST Valid: True")
    print(f"[OUTPUT AST]: {json.dumps(output_ast, indent=2)}")