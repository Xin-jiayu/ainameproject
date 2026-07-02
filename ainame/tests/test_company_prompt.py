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


class CompanyPromptTest(unittest.TestCase):
    def test_company_prompt_combines_industry_tone_knowledge_and_brand_quality(self):
        prompt = _load_prompt_template("company_naming_node")

        self.assertIn("行业属性、品牌调性、商业定位和用户私有知识库", prompt)
        self.assertIn("行业、业务方向、目标客群、品牌调性或核心诉求", prompt)
        self.assertIn("用户专属知识库内容", prompt)
        self.assertIn("用户尚未上传企业知识库", prompt)
        self.assertIn("本次未检索到相关内容", prompt)
        self.assertIn("知识库检索服务暂时不可用", prompt)
        self.assertIn("当知识库内容包含真实参考资料时", prompt)
        self.assertIn("名字要具备商业品牌感", prompt)
        self.assertIn("输出必须恰好 5 个候选", prompt)
        self.assertIn("reference：说明名字的创意来源", prompt)
        self.assertIn("moral：写清品牌寓意和商业解释", prompt)
        self.assertIn("domain：为该名字设计一个简短、纯小写、无空格的 .com 域名建议", prompt)

    def test_company_prompt_uses_rag_business_rules_and_truncation_notice(self):
        prompt = _load_prompt_template("company_naming_node")

        self.assertIn("已检索当前登录用户自己的企业知识库", prompt)
        self.assertIn("产品特点、目标客群、核心卖点、品牌调性、禁忌词", prompt)
        self.assertIn("检索内容可能已因过长被摘要式截断", prompt)
        self.assertIn("只能使用片段中明确出现的信息", prompt)
        self.assertIn("必须视为命名避讳", prompt)
        self.assertIn("必须体现在 reference、moral 和评分理由中", prompt)
        self.assertIn("如何避开禁忌词或负面联想", prompt)

    def test_company_score_instruction_covers_brand_industry_and_spreadability(self):
        score_instruction = _load_score_instruction_source()

        self.assertIn("品牌感 30%", score_instruction)
        self.assertIn("行业匹配 25%", score_instruction)
        self.assertIn("传播性 25%", score_instruction)
        self.assertIn("industry_fit", score_instruction)
        self.assertIn("brand_sense 表示品牌感", score_instruction)
        self.assertIn("spreadability 表示传播性", score_instruction)


if __name__ == "__main__":
    unittest.main()
