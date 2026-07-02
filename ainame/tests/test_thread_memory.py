import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = PROJECT_ROOT / "core" / "workflow.py"
SERVICE_PATH = PROJECT_ROOT / "services" / "name_service.py"


def _parse(path: Path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _find_async_function(module: ast.Module, name: str) -> ast.AsyncFunctionDef:
    return next(
        node
        for node in ast.walk(module)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == name
    )


def _is_thread_id_config(node: ast.AST, expected_value: ast.AST) -> bool:
    if not isinstance(node, ast.Dict) or len(node.keys) != 1:
        return False
    key = node.keys[0]
    value = node.values[0]
    if not isinstance(key, ast.Constant) or key.value != "configurable":
        return False
    if not isinstance(value, ast.Dict) or len(value.keys) != 1:
        return False
    inner_key = value.keys[0]
    inner_value = value.values[0]
    return (
        isinstance(inner_key, ast.Constant)
        and inner_key.value == "thread_id"
        and ast.dump(inner_value) == ast.dump(expected_value)
    )


class ThreadMemoryTest(unittest.TestCase):
    def test_initial_generation_creates_new_thread_id_and_uses_it_for_graph_memory(self):
        workflow = _parse(WORKFLOW_PATH)
        generate_naming_v2 = _find_async_function(workflow, "generate_naming_v2")

        uuid_assignments = [
            node
            for node in ast.walk(generate_naming_v2)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "thread_id" for target in node.targets)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "str"
            and node.value.args
            and isinstance(node.value.args[0], ast.Call)
            and isinstance(node.value.args[0].func, ast.Attribute)
            and node.value.args[0].func.attr == "uuid4"
        ]
        self.assertEqual(len(uuid_assignments), 1)

        config_assignments = [
            node
            for node in ast.walk(generate_naming_v2)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "config" for target in node.targets)
            and _is_thread_id_config(node.value, ast.Name(id="thread_id", ctx=ast.Load()))
        ]
        self.assertEqual(len(config_assignments), 1)

        graph_invocations = [
            node
            for node in ast.walk(generate_naming_v2)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "ainvoke"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.Name)
            and node.args[1].id == "config"
        ]
        self.assertEqual(len(graph_invocations), 1)

    def test_feedback_reuses_request_thread_id_for_graph_memory(self):
        workflow = _parse(WORKFLOW_PATH)
        feedback_names = _find_async_function(workflow, "feedback_names")

        request_thread_id = ast.Attribute(
            value=ast.Name(id="name_info", ctx=ast.Load()),
            attr="thread_id",
            ctx=ast.Load(),
        )
        config_assignments = [
            node
            for node in ast.walk(feedback_names)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "config" for target in node.targets)
            and _is_thread_id_config(node.value, request_thread_id)
        ]
        self.assertEqual(len(config_assignments), 1)

        thread_id_assignments = [
            node
            for node in ast.walk(feedback_names)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "thread_id" for target in node.targets)
        ]
        self.assertEqual(thread_id_assignments, [])

    def test_generate_route_persists_and_returns_generated_thread_id(self):
        service = _parse(SERVICE_PATH)
        generate_names = _find_async_function(service, "generate_names")

        create_record_calls = [
            node
            for node in ast.walk(generate_names)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "create_record"
        ]
        self.assertEqual(len(create_record_calls), 1)
        create_record_call = create_record_calls[0]
        thread_id_keywords = [
            keyword.value
            for keyword in create_record_call.keywords
            if keyword.arg == "thread_id"
        ]
        self.assertEqual(len(thread_id_keywords), 1)
        self.assertEqual(ast.unparse(thread_id_keywords[0]), "result['thread_id']")

        response_calls = [
            node
            for node in ast.walk(generate_names)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "NameSchemaWithThreadOut"
        ]
        self.assertEqual(len(response_calls), 1)
        response_thread_ids = [
            keyword.value
            for keyword in response_calls[0].keywords
            if keyword.arg == "thread_id"
        ]
        self.assertEqual(len(response_thread_ids), 1)
        self.assertEqual(ast.unparse(response_thread_ids[0]), "result['thread_id']")

    def test_feedback_route_loads_record_by_old_thread_id_and_returns_same_thread_id(self):
        service = _parse(SERVICE_PATH)
        feedback = _find_async_function(service, "feedback")

        lookup_calls = [
            node
            for node in ast.walk(feedback)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get_record_by_thread_id"
        ]
        self.assertEqual(len(lookup_calls), 1)
        self.assertEqual(ast.unparse(lookup_calls[0].args[1]), "data.thread_id")

        feedback_calls = [
            node
            for node in ast.walk(feedback)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "feedback_names"
        ]
        self.assertEqual(len(feedback_calls), 1)
        self.assertEqual(ast.unparse(feedback_calls[0].args[0]), "data")

        response_calls = [
            node
            for node in ast.walk(feedback)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "NameSchemaWithThreadOut"
        ]
        self.assertEqual(len(response_calls), 1)
        response_thread_ids = [
            keyword.value
            for keyword in response_calls[0].keywords
            if keyword.arg == "thread_id"
        ]
        self.assertEqual(len(response_thread_ids), 1)
        self.assertEqual(ast.unparse(response_thread_ids[0]), "result['thread_id']")


if __name__ == "__main__":
    unittest.main()
