import ast
import unittest
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / "core" / "workflow.py"


def _load_human_prompt_template() -> str:
    module = ast.parse(WORKFLOW_PATH.read_text(encoding="utf-8"))
    human_node = next(
        node
        for node in module.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "human_naming_node"
    )
    prompt_assignment = next(
        node
        for node in human_node.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "prompt" for target in node.targets)
    )

    return "".join(
        value.value
        for value in prompt_assignment.value.values
        if isinstance(value, ast.Constant) and isinstance(value.value, str)
    )


def _load_score_instruction_source() -> str:
    module = ast.parse(WORKFLOW_PATH.read_text(encoding="utf-8"))
    score_function = next(
        node
        for node in module.body
        if isinstance(node, ast.FunctionDef) and node.name == "_build_score_output_instruction"
    )
    return "\n".join(
        node.value
        for node in ast.walk(score_function)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )


class HumanPromptTest(unittest.TestCase):
    def test_human_prompt_requires_stable_five_names_with_source_moral_and_explanation(self):
        prompt = _load_human_prompt_template()

        self.assertIn("恰好 5 个", prompt)
        self.assertIn("每个名字必须包含姓氏", prompt)
        self.assertIn("reference：出处或灵感来源", prompt)
        self.assertIn("moral：同时写【寓意】和【解释】", prompt)
        self.assertIn("domain：人名场景不需要真实域名", prompt)
        self.assertIn("domain_status：人名场景不需要域名查询", prompt)

    def test_human_score_instruction_covers_phonology_meaning_and_surname_fit(self):
        score_instruction = _load_score_instruction_source()

        self.assertIn("音韵 30%", score_instruction)
        self.assertIn("寓意 30%", score_instruction)
        self.assertIn("姓氏匹配 25%", score_instruction)
        self.assertIn("phonology", score_instruction)
        self.assertIn("meaning", score_instruction)
        self.assertIn("surname_fit", score_instruction)


if __name__ == "__main__":
    unittest.main()
