import ast
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = PROJECT_ROOT / "core" / "workflow.py"
INDEX_PAGE_PATH = PROJECT_ROOT.parent / "ainameapp" / "pages" / "index" / "index.vue"
DETAIL_PAGE_PATH = PROJECT_ROOT.parent / "ainameapp" / "pages" / "history" / "detail.vue"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from schemas.name_schemas import CompanyNameSchema, HumanNameSchema, NameSchema, PetNameSchema


def _parse_workflow():
    return ast.parse(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _find_function(module: ast.Module, name: str):
    return next(
        node
        for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    )


def _calls_function(function_node: ast.AST, name: str) -> bool:
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
        for node in ast.walk(function_node)
    )


class StructuredOutputContractTest(unittest.TestCase):
    def test_keeps_single_name_schema_contract(self):
        self.assertEqual(
            set(NameSchema.model_fields),
            {
                "name",
                "reference",
                "moral",
                "domain",
                "domain_status",
                "score",
                "score_detail",
                "score_reason",
                "risk_level",
                "risk_reason",
            },
        )
        self.assertFalse(NameSchema.model_fields["domain"].is_required())
        self.assertFalse(NameSchema.model_fields["domain_status"].is_required())
        self.assertFalse(NameSchema.model_fields["score"].is_required())
        self.assertFalse(NameSchema.model_fields["score_detail"].is_required())
        self.assertFalse(NameSchema.model_fields["score_reason"].is_required())
        self.assertFalse(NameSchema.model_fields["risk_level"].is_required())
        self.assertFalse(NameSchema.model_fields["risk_reason"].is_required())

    def test_category_specific_schema_drafts_keep_frontend_compatibility(self):
        self.assertFalse(HumanNameSchema.model_fields["domain"].is_required())
        self.assertFalse(HumanNameSchema.model_fields["domain_status"].is_required())
        self.assertFalse(PetNameSchema.model_fields["domain"].is_required())
        self.assertFalse(PetNameSchema.model_fields["domain_status"].is_required())

        self.assertTrue(CompanyNameSchema.model_fields["domain"].is_required())
        self.assertTrue(CompanyNameSchema.model_fields["score"].is_required())
        self.assertTrue(CompanyNameSchema.model_fields["score_detail"].is_required())
        self.assertTrue(CompanyNameSchema.model_fields["score_reason"].is_required())
        self.assertIn("risk_level", CompanyNameSchema.model_fields)
        self.assertIn("risk_reason", CompanyNameSchema.model_fields)

    def test_score_detail_calculates_composite_score(self):
        name = NameSchema(
            name="星澜",
            reference="品牌定位",
            moral="有探索感和品质感",
            score_detail={
                "brand_sense": 90,
                "memorability": 80,
                "differentiation": 70,
                "fit": 100,
                "spreadability": 60,
            },
        )

        self.assertEqual(name.score, 82)

    def test_workflow_appends_score_output_instruction(self):
        workflow = _parse_workflow()

        self.assertTrue(_calls_function(_find_function(workflow, "human_naming_node"), "_build_score_output_instruction"))
        self.assertTrue(_calls_function(_find_function(workflow, "company_naming_node"), "_build_score_output_instruction"))
        self.assertTrue(_calls_function(_find_function(workflow, "pet_naming_node"), "_build_score_output_instruction"))

    def test_non_company_nodes_clear_domain_fields(self):
        workflow = _parse_workflow()
        clear_function = _find_function(workflow, "_clear_non_company_domains")
        clear_assignments = [
            node
            for node in ast.walk(clear_function)
            if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Constant)
            and node.value.value is None
            and any(
                isinstance(target, ast.Attribute)
                and target.attr in {"domain", "domain_status"}
                for target in node.targets
            )
        ]

        self.assertEqual(len(clear_assignments), 2)
        self.assertTrue(_calls_function(_find_function(workflow, "human_naming_node"), "_clear_non_company_domains"))
        self.assertTrue(_calls_function(_find_function(workflow, "pet_naming_node"), "_clear_non_company_domains"))
        self.assertFalse(_calls_function(_find_function(workflow, "company_naming_node"), "_clear_non_company_domains"))

    def test_frontend_hides_null_domain_values(self):
        index_page = INDEX_PAGE_PATH.read_text(encoding="utf-8")
        detail_page = DETAIL_PAGE_PATH.read_text(encoding="utf-8")

        self.assertIn("if (!item.domain) return []", index_page)
        self.assertIn('v-if="item.domain"', detail_page)


if __name__ == "__main__":
    unittest.main()
