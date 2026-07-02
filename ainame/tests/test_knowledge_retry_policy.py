import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROUTER_PATH = PROJECT_ROOT / "routers" / "rag_router.py"


def _parse_router():
    return ast.parse(ROUTER_PATH.read_text(encoding="utf-8"))


def _find_function(module: ast.Module, name: str):
    return next(
        node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    )


class KnowledgeRetryPolicyTest(unittest.TestCase):
    def test_retry_limit_constant_is_three(self):
        module = _parse_router()
        assignment = next(
            node
            for node in module.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "MAX_KNOWLEDGE_FILE_RETRY_COUNT" for target in node.targets)
        )

        self.assertEqual(assignment.value.value, 3)

    def test_retry_limit_helper_uses_retry_count(self):
        module = _parse_router()
        helper = _find_function(module, "has_reached_retry_limit")
        source = ast.unparse(helper)

        self.assertIn("retry_count", source)
        self.assertIn("MAX_KNOWLEDGE_FILE_RETRY_COUNT", source)
        self.assertIn(">=", source)

    def test_retry_route_checks_limit_before_requeue(self):
        module = _parse_router()
        retry_function = _find_function(module, "retry_knowledge_file")
        source = ast.unparse(retry_function)

        self.assertIn("has_reached_retry_limit(knowledge_file)", source)
        self.assertIn("文件处理失败次数已达到上限，请重新上传文件", source)
        self.assertLess(source.index("has_reached_retry_limit(knowledge_file)"), source.index("repository.mark_retrying"))
        self.assertLess(source.index("has_reached_retry_limit(knowledge_file)"), source.index("send_to_queue"))


if __name__ == "__main__":
    unittest.main()
