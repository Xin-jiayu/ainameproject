import ast
import unittest
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / "core" / "workflow.py"


def _load_route_by_category():
    module = ast.parse(WORKFLOW_PATH.read_text(encoding="utf-8"))
    route_node = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "route_by_category"
    )
    compiled = compile(
        ast.fix_missing_locations(ast.Module(body=[route_node], type_ignores=[])),
        str(WORKFLOW_PATH),
        "exec",
    )
    namespace = {"WorkFlowState": dict}
    exec(compiled, namespace)
    return namespace["route_by_category"]


class WorkflowRoutingTest(unittest.TestCase):
    def test_naming_categories_route_to_expected_nodes(self):
        route_by_category = _load_route_by_category()

        self.assertEqual(route_by_category({"category": "人名"}), "human_naming_node")
        self.assertEqual(route_by_category({"category": "企业名"}), "company_naming_node")
        self.assertEqual(route_by_category({"category": "宠物名"}), "pet_naming_node")

    def test_unknown_category_raises_clear_error(self):
        route_by_category = _load_route_by_category()

        with self.assertRaisesRegex(ValueError, "未知起名分类.*游戏角色.*人名.*企业名.*宠物名"):
            route_by_category({"category": "游戏角色"})

    def test_expected_naming_nodes_are_registered_in_workflow(self):
        module = ast.parse(WORKFLOW_PATH.read_text(encoding="utf-8"))
        add_node_calls = [
            node
            for node in ast.walk(module)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "add_node"
        ]

        registered_nodes = {
            call.args[0].value: call.args[1].id
            for call in add_node_calls
            if len(call.args) >= 2
            and isinstance(call.args[0], ast.Constant)
            and isinstance(call.args[1], ast.Name)
        }

        self.assertEqual(registered_nodes["human_naming_node"], "human_naming_node")
        self.assertEqual(registered_nodes["company_naming_node"], "company_naming_node")
        self.assertEqual(registered_nodes["pet_naming_node"], "pet_naming_node")


if __name__ == "__main__":
    unittest.main()
