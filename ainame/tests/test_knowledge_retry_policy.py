import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SERVICE_PATH = PROJECT_ROOT / "services" / "knowledge_service.py"


def _parse_service():
    return ast.parse(SERVICE_PATH.read_text(encoding="utf-8"))


def _find_function(module: ast.Module, name: str):
    return next(
        node
        for node in ast.walk(module)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    )


class KnowledgeRetryPolicyTest(unittest.TestCase):
    def test_retry_limit_constant_is_three(self):
        module = _parse_service()
        assignment = next(
            node
            for node in ast.walk(module)
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "MAX_RETRY_COUNT" for target in node.targets)
        )

        self.assertEqual(assignment.value.value, 3)

    def test_retry_limit_uses_retry_count(self):
        module = _parse_service()
        retry_function = _find_function(module, "retry_file")
        source = ast.unparse(retry_function)

        self.assertIn("retry_count", source)
        self.assertIn("self.MAX_RETRY_COUNT", source)
        self.assertIn(">=", source)

    def test_retry_checks_limit_before_requeue(self):
        module = _parse_service()
        retry_function = _find_function(module, "retry_file")
        source = ast.unparse(retry_function)

        self.assertIn("knowledge_file.retry_count", source)
        self.assertIn("文件处理失败次数已达到上限，请重新上传文件", source)
        self.assertLess(source.index("knowledge_file.retry_count"), source.index("repository.mark_retrying"))
        self.assertLess(source.index("knowledge_file.retry_count"), source.index("enqueue_file_task"))


if __name__ == "__main__":
    unittest.main()
