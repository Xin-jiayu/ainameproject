import ast
import unittest
from pathlib import Path


WORKFLOW_PATH = Path(__file__).resolve().parents[1] / "core" / "workflow.py"


def _load_prompt_template(function_name: str) -> str:
    module = ast.parse(WORKFLOW_PATH.read_text(encoding="utf-8"))
    function_node = next(
        node
        for node in module.body
        if isinstance(node, ast.AsyncFunctionDef) and node.name == function_name
    )
    prompt_assignment = next(
        node
        for node in function_node.body
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


class PetPromptTest(unittest.TestCase):
    def test_pet_prompt_emphasizes_cute_memorable_visual_names(self):
        prompt = _load_prompt_template("pet_naming_node")

        self.assertIn("宠物与虚拟 IP 命名", prompt)
        self.assertIn("可爱、亲切、好记，并且富有画面感", prompt)
        self.assertIn("恰好 5 个", prompt)
        self.assertIn("叠音、昵称感、小名感、拟声感或轻微反差萌", prompt)
        self.assertIn("毛色、体型、动作、性格、习惯、角色设定", prompt)
        self.assertIn("联想到一个具体画面", prompt)
        self.assertIn("moral：写清名字的可爱点、画面感和适合呼唤/传播的理由", prompt)
        self.assertIn("domain：宠物/IP 场景不需要真实域名", prompt)
        self.assertIn("domain_status：宠物/IP 场景不需要域名查询", prompt)

    def test_pet_score_instruction_covers_cuteness_imagery_and_callability(self):
        score_instruction = _load_score_instruction_source()

        self.assertIn("可爱度 30%", score_instruction)
        self.assertIn("画面感 30%", score_instruction)
        self.assertIn("呼喊顺口度 25%", score_instruction)
        self.assertIn("cuteness", score_instruction)
        self.assertIn("imagery", score_instruction)
        self.assertIn("callability", score_instruction)


if __name__ == "__main__":
    unittest.main()
