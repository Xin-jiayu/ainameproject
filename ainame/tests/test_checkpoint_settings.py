import ast
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = PROJECT_ROOT / "core" / "workflow.py"
SETTINGS_PATH = PROJECT_ROOT / "settings" / "__init__.py"
ENV_EXAMPLE_PATH = PROJECT_ROOT / ".env.example"
INIT_MEMORY_PATH = PROJECT_ROOT / "init_pg_memory.py"


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _assignment_source(module: ast.Module, name: str) -> str:
    for node in module.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.unparse(node.value)
    raise AssertionError(f"{name} assignment not found")


class CheckpointSettingsTest(unittest.TestCase):
    def test_workflow_reads_checkpoint_config_from_settings(self):
        workflow = _parse(WORKFLOW_PATH)

        self.assertEqual(_assignment_source(workflow, "CHECKPOINT_DB_URI"), "settings.LANGGRAPH_CHECKPOINT_DB_URI")
        self.assertEqual(
            _assignment_source(workflow, "CHECKPOINT_CONNECT_TIMEOUT"),
            "settings.LANGGRAPH_CHECKPOINT_CONNECT_TIMEOUT",
        )
        self.assertEqual(
            _assignment_source(workflow, "CHECKPOINT_FALLBACK_TO_MEMORY"),
            "settings.LANGGRAPH_CHECKPOINT_FALLBACK_TO_MEMORY",
        )

        source = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertNotIn('os.getenv("LANGGRAPH_CHECKPOINT_DB_URI"', source)
        self.assertNotIn('os.getenv("LANGGRAPH_CHECKPOINT_CONNECT_TIMEOUT"', source)

    def test_settings_separates_mysql_business_db_from_postgres_memory_db(self):
        settings_source = SETTINGS_PATH.read_text(encoding="utf-8")

        self.assertIn("DB_URI", settings_source)
        self.assertIn("mysql+aiomysql", settings_source)
        self.assertIn("LANGGRAPH_CHECKPOINT_DB_URI", settings_source)
        self.assertIn("postgresql://", settings_source)
        self.assertIn("used only for LangGraph thread memory", settings_source)

    def test_env_example_documents_checkpoint_config(self):
        env_example = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

        self.assertIn("DB_URI=mysql+aiomysql://", env_example)
        self.assertIn("LANGGRAPH_CHECKPOINT_DB_URI=postgresql://", env_example)
        self.assertIn("LANGGRAPH_CHECKPOINT_CONNECT_TIMEOUT=10", env_example)
        self.assertIn("LANGGRAPH_CHECKPOINT_FALLBACK_TO_MEMORY=true", env_example)
        self.assertIn("separate from the MySQL business DB_URI", env_example)

    def test_missing_postgres_can_raise_clear_startup_error(self):
        workflow_source = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn("if not CHECKPOINT_FALLBACK_TO_MEMORY", workflow_source)
        self.assertIn("LangGraph PostgreSQL checkpointer is unavailable", workflow_source)
        self.assertIn("Set LANGGRAPH_CHECKPOINT_DB_URI to a reachable PostgreSQL database", workflow_source)
        self.assertIn("CHECKPOINT_FALLBACK_TO_MEMORY=true", workflow_source)

    def test_memory_init_script_uses_same_checkpoint_setting(self):
        init_source = INIT_MEMORY_PATH.read_text(encoding="utf-8")

        self.assertIn("LANGGRAPH_CHECKPOINT_DB_URI", init_source)
        self.assertNotIn("postgresql://postgres:123456@localhost:5432/ainame", init_source)
        self.assertIn("Unable to initialize LangGraph PostgreSQL checkpoint tables", init_source)


if __name__ == "__main__":
    unittest.main()
