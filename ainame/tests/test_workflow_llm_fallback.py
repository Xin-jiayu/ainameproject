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
    def __init__(self):
        self.calls = 0
        self.prompts = []

    async def ainvoke(self, prompt):
        self.calls += 1
        self.prompts.append(prompt)
        return ""


class EmptyListStructuredLLM:
    async def ainvoke(self, prompt):
        return workflow.NameResultSchema(names=[])


class ShortStructuredLLM:
    async def ainvoke(self, prompt):
        return workflow.NameResultSchema(
            names=[
                {
                    "name": f"\u674e\u660e{i}",
                    "reference": "\u8bd7\u6587\u610f\u8c61",
                    "moral": "\u6e29\u548c\u660e\u6717",
                }
                for i in range(3)
            ]
        )


class MissingFieldRawLLM:
    async def ainvoke(self, prompt):
        return {"names": [{"name": "\u674e\u660e"} for _ in range(5)]}


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


class InvalidJsonThenValidRawLLM:
    def __init__(self):
        self.calls = 0
        self.prompts = []

    async def ainvoke(self, prompt):
        self.calls += 1
        self.prompts.append(prompt)
        if self.calls == 1:
            return "这不是 JSON"
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

        fake_llm = EmptyRawLLM()
        with patch.object(workflow, "structured_llm", EmptyStructuredLLM()):
            with patch.object(workflow, "llm", fake_llm):
                with self.assertRaises(workflow.NameGenerationError):
                    await workflow.human_naming_node(state)

        self.assertEqual(fake_llm.calls, workflow.JSON_FALLBACK_MAX_ATTEMPTS)
        self.assertTrue(all("只返回 JSON" in prompt for prompt in fake_llm.prompts))

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

    async def test_empty_name_list_triggers_json_fallback(self):
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

        with patch.object(workflow, "structured_llm", EmptyListStructuredLLM()):
            with patch.object(workflow, "llm", fake_llm):
                result = await workflow.human_naming_node(state)

        self.assertEqual(fake_llm.calls, 1)
        self.assertEqual(len(result["final_output"]["names"]), 5)

    async def test_short_structured_result_is_completed_to_five_names(self):
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

        with patch.object(workflow, "structured_llm", ShortStructuredLLM()):
            with patch.object(workflow, "llm", EmptyRawLLM()):
                result = await workflow.human_naming_node(state)

        names = result["final_output"]["names"]
        self.assertEqual(len(names), 5)
        self.assertEqual(names[3]["name"], "\u5019\u9009\u4eba\u540d4")
        self.assertEqual(names[4]["name"], "\u5019\u9009\u4eba\u540d5")

    async def test_missing_fields_are_filled_with_defaults(self):
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
            with patch.object(workflow, "llm", MissingFieldRawLLM()):
                result = await workflow.human_naming_node(state)

        first = result["final_output"]["names"][0]
        self.assertEqual(first["reference"], "AI \u8f93\u51fa\u7f3a\u5931\u51fa\u5904\uff0c\u5df2\u7531\u540e\u7aef\u8865\u9ed8\u8ba4\u547d\u540d\u4f9d\u636e")
        self.assertEqual(first["moral"], "AI \u8f93\u51fa\u7f3a\u5931\u5bd3\u610f\uff0c\u5df2\u7531\u540e\u7aef\u8865\u9ed8\u8ba4\u5bd3\u610f\u8bf4\u660e")
        self.assertEqual(first["score"], 60)
        self.assertEqual(first["score_detail"]["phonology"], 60)

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

    async def test_invalid_json_retries_with_json_only_prompt_then_succeeds(self):
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
        fake_llm = InvalidJsonThenValidRawLLM()

        with patch.object(workflow, "structured_llm", EmptyStructuredLLM()):
            with patch.object(workflow, "llm", fake_llm):
                result = await workflow.human_naming_node(state)

        self.assertEqual(fake_llm.calls, 2)
        self.assertTrue(all("只返回 JSON" in prompt for prompt in fake_llm.prompts))
        self.assertIn("第 2/3 次结构化 JSON 解析重试", fake_llm.prompts[1])
        self.assertEqual(len(result["final_output"]["names"]), 5)


if __name__ == "__main__":
    unittest.main()
