import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core import workflow
from schemas.name_schemas import FeedbackSchema, NameIn, NameResultSchema


def _name_result(prefix="Name"):
    return NameResultSchema(
        names=[
            {
                "name": f"{prefix}{i}",
                "reference": "source",
                "moral": "meaning",
                "domain": None,
                "domain_status": None,
            }
            for i in range(5)
        ]
    )


class CapturingStructuredLLM:
    def __init__(self):
        self.prompts = []

    async def ainvoke(self, prompt):
        self.prompts.append(prompt)
        return _name_result()


class FakeGraph:
    def __init__(self):
        self.calls = []

    async def ainvoke(self, state, config=None):
        self.calls.append({"state": state, "config": config})
        return {
            "final_output": _name_result("Flow").model_dump(),
            "history_names": "Flow history",
        }


class FeedbackPromptFlowTest(unittest.IsolatedAsyncioTestCase):
    async def test_all_nodes_include_previous_names_and_unified_feedback_rule(self):
        state = {
            "user_id": 1,
            "surname": "Li",
            "gender": "any",
            "length": "",
            "other": "warm",
            "exclude": [],
            "feedback": "make the names softer",
            "history_names": "OldName meaning",
        }

        for node in (
            workflow.human_naming_node,
            workflow.company_naming_node,
            workflow.pet_naming_node,
        ):
            fake_llm = CapturingStructuredLLM()
            with patch.object(workflow, "structured_llm", fake_llm):
                with patch.object(workflow, "retrive_user_from_knowledge", return_value="no knowledge"):
                    await node(state)

            prompt = fake_llm.prompts[-1]
            self.assertIn("上一轮生成结果", prompt)
            self.assertIn("OldName meaning", prompt)
            self.assertIn("make the names softer", prompt)
            self.assertIn("保留上一轮中用户满意的部分", prompt)
            self.assertIn("只修改用户指出的问题", prompt)

    async def test_feedback_keeps_same_thread_id_for_all_categories(self):
        original_graph = workflow.naming_graph
        fake_graph = FakeGraph()
        workflow.naming_graph = fake_graph
        self.addCleanup(setattr, workflow, "naming_graph", original_graph)

        for category in ("person", "brand", "pet"):
            first = await workflow.generate_naming_v2(
                NameIn(category=category, surname="Li", other="warm", exclude=[]),
                user_id=1,
            )
            followup = await workflow.feedback_names(
                FeedbackSchema(
                    thread_id=first["thread_id"],
                    category=category,
                    feedback="make it softer",
                ),
                user_id=1,
            )

            self.assertEqual(followup["thread_id"], first["thread_id"])

        configs = [call["config"]["configurable"]["thread_id"] for call in fake_graph.calls]
        for index in range(0, len(configs), 2):
            self.assertEqual(configs[index + 1], configs[index])


if __name__ == "__main__":
    unittest.main()
