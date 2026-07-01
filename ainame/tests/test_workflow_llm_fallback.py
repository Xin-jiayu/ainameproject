import sys
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core import workflow

class EmptyStructuredLLM:
    async def ainvoke(self, prompt):
        return None


class EmptyRawLLM:
    async def ainvoke(self, prompt):
        return ""


class ValidRawLLM:
    def __init__(self):
        self.calls = 0

    async def ainvoke(self, prompt):
        self.calls += 1
        return {
            "names": [
                {
                    "name": f"\u674e\u660e{i}",
                    "reference": "\u8bd7\u6587\u610f\u8c61",
                    "moral": "\u6e29\u548c\u660e\u6717",
                    "domain": None,
                    "domain_status": None,
                }
                for i in range(5)
            ]
        }


class WorkflowLLMFallbackTest(unittest.IsolatedAsyncioTestCase):
    async def test_human_node_raises_name_generation_error_for_empty_llm_result(self):
        state = {
            "user_id": 1,
            "category": "\u4eba\u540d",
            "surname": "\u674e",
            "gender": "\u4e0d\u9650",
            "length": "",
            "other": "\u6e29\u548c\u5927\u65b9",
            "exclude": [],
            "final_output": {},
        }

        with patch.object(workflow, "structured_llm", EmptyStructuredLLM()):
            with patch.object(workflow, "llm", EmptyRawLLM()):
                with self.assertRaises(workflow.NameGenerationError):
                    await workflow.human_naming_node(state)

    async def test_human_node_uses_json_fallback_for_empty_structured_result(self):
        state = {
            "user_id": 1,
            "category": "\u4eba\u540d",
            "surname": "\u674e",
            "gender": "\u4e0d\u9650",
            "length": "",
            "other": "\u6e29\u548c\u5927\u65b9",
            "exclude": [],
            "final_output": {},
        }
        fake_llm = ValidRawLLM()

        with patch.object(workflow, "structured_llm", EmptyStructuredLLM()):
            with patch.object(workflow, "llm", fake_llm):
                result = await workflow.human_naming_node(state)

        self.assertEqual(fake_llm.calls, 1)
        self.assertEqual(len(result["final_output"]["names"]), 5)

    async def test_json_extract_handles_markdown_fenced_json(self):
        state = {
            "user_id": 1,
            "category": "\u4eba\u540d",
            "surname": "\u674e",
            "gender": "\u4e0d\u9650",
            "length": "",
            "other": "\u6e29\u548c\u5927\u65b9",
            "exclude": [],
            "final_output": {},
        }
        class FencedRawLLM:
            async def ainvoke(self, prompt):
                return """```json
{"names":[{"name":"\u674e\u660e0","reference":"\u8bd7\u6587\u610f\u8c61","moral":"\u6e29\u548c\u660e\u6717"},{"name":"\u674e\u660e1","reference":"\u8bd7\u6587\u610f\u8c61","moral":"\u6e29\u548c\u660e\u6717"},{"name":"\u674e\u660e2","reference":"\u8bd7\u6587\u610f\u8c61","moral":"\u6e29\u548c\u660e\u6717"},{"name":"\u674e\u660e3","reference":"\u8bd7\u6587\u610f\u8c61","moral":"\u6e29\u548c\u660e\u6717"},{"name":"\u674e\u660e4","reference":"\u8bd7\u6587\u610f\u8c61","moral":"\u6e29\u548c\u660e\u6717"}]}
```"""

        with patch.object(workflow, "structured_llm", EmptyStructuredLLM()):
            with patch.object(workflow, "llm", FencedRawLLM()):
                result = await workflow.human_naming_node(state)

        self.assertEqual(len(result["final_output"]["names"]), 5)


if __name__ == "__main__":
    unittest.main()
