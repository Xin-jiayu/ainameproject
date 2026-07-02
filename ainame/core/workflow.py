import asyncio
import json
import re
import sys
import uuid
from typing import Any, Dict, List, TypedDict

import settings
from langchain_deepseek import ChatDeepSeek
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph
from psycopg_pool import AsyncConnectionPool

from core.rag_service import retrive_user_from_knowledge
from core.tools import check_com_domain
from schemas.name_schemas import (
    CompanyNameResultSchema,
    FeedbackSchema,
    HumanNameResultSchema,
    NameIn,
    NameResultSchema,
    PetNameResultSchema,
)


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class NameGenerationError(RuntimeError):
    """Raised when the LLM does not return a usable naming result."""


JSON_FALLBACK_MAX_ATTEMPTS = 3


def _default_score_detail(scene: str) -> dict[str, Any]:
    detail: dict[str, Any] = {
        "brand_sense": 60,
        "memorability": 60,
        "differentiation": 60,
        "fit": 60,
        "spreadability": 60,
        "phonology": None,
        "meaning": None,
        "surname_fit": None,
        "industry_fit": None,
        "cuteness": None,
        "imagery": None,
        "callability": None,
    }
    if scene == "人名":
        detail.update({"phonology": 60, "meaning": 60, "surname_fit": 60})
    elif scene == "企业名":
        detail.update({"industry_fit": 60})
    elif scene == "宠物名":
        detail.update({"cuteness": 60, "imagery": 60, "callability": 60})
    return detail


def _fallback_name(scene: str, index: int) -> str:
    prefixes = {
        "人名": "候选人名",
        "企业名": "候选品牌",
        "宠物名": "候选宠物",
    }
    return f"{prefixes.get(scene, '候选名')}{index}"


def _normalize_name_item(item: Any, scene: str, index: int) -> dict[str, Any]:
    if not isinstance(item, dict):
        item = {}

    name = str(item.get("name") or "").strip() or _fallback_name(scene, index)
    reference = str(item.get("reference") or "").strip() or "AI 输出缺失出处，已由后端补默认命名依据"
    moral = str(item.get("moral") or "").strip() or "AI 输出缺失寓意，已由后端补默认寓意说明"
    score_detail = item.get("score_detail")
    if not isinstance(score_detail, dict):
        score_detail = _default_score_detail(scene)

    normalized = {
        **item,
        "name": name,
        "reference": reference,
        "moral": moral,
        "score": item.get("score") if item.get("score") is not None else 60,
        "score_detail": {**_default_score_detail(scene), **score_detail},
        "score_reason": item.get("score_reason") or "AI 输出缺失评分理由，已由后端补默认说明。",
    }

    if scene == "企业名":
        normalized["domain"] = item.get("domain") or f"ainame-candidate-{index}.com"
        normalized["domain_status"] = item.get("domain_status") or "正在查询..."
        normalized["risk_level"] = item.get("risk_level") or "unknown"
        normalized["risk_reason"] = item.get("risk_reason") or "AI 输出缺失风险说明，已由后端补默认说明。"
    else:
        normalized["domain"] = item.get("domain")
        normalized["domain_status"] = item.get("domain_status")
        normalized["risk_level"] = item.get("risk_level")
        normalized["risk_reason"] = item.get("risk_reason")

    return normalized


def _normalize_name_payload(payload: Any, scene: str) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump()
    if not isinstance(payload, dict):
        raise ValueError(f"{scene} result payload must be a dict")

    names = payload.get("names")
    if not isinstance(names, list) or not names:
        raise ValueError(f"{scene} result names must not be empty")

    normalized_names = [
        _normalize_name_item(item, scene, index)
        for index, item in enumerate(names[:5], start=1)
    ]
    while len(normalized_names) < 5:
        normalized_names.append(_normalize_name_item({}, scene, len(normalized_names) + 1))

    return {"names": normalized_names}


def _ensure_valid_name_result(
    result: NameResultSchema | dict[str, Any],
    scene: str,
    result_schema: type[NameResultSchema] = NameResultSchema,
) -> NameResultSchema:
    payload = _normalize_name_payload(result, scene)
    parsed = result_schema.model_validate(payload)
    if len(parsed.names) != 5:
        raise ValueError(f"{scene} result must contain exactly 5 names, got {len(parsed.names)}")
    return NameResultSchema.model_validate(parsed.model_dump())


def _extract_json_object(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start : end + 1])


async def _invoke_json_name_llm(
    prompt: str,
    scene: str,
    result_schema: type[NameResultSchema] = NameResultSchema,
) -> NameResultSchema:
    last_error: Exception | None = None
    for attempt in range(1, JSON_FALLBACK_MAX_ATTEMPTS + 1):
        json_prompt = f"""{prompt}

IMPORTANT:
Return valid JSON only. Do not use markdown fences or extra text.
只返回 JSON，不要返回解释、Markdown、代码块、前后缀文本或注释。
这是第 {attempt}/{JSON_FALLBACK_MAX_ATTEMPTS} 次结构化 JSON 解析重试。
The JSON schema must be:
{{
  "names": [
    {{
      "name": "string",
      "reference": "string",
      "moral": "string",
      "domain": null,
      "domain_status": null,
      "risk_level": null,
      "risk_reason": null,
      "score": 85,
      "score_detail": {{
        "brand_sense": 85,
        "memorability": 85,
        "differentiation": 85,
        "fit": 85,
        "spreadability": 85,
        "phonology": null,
        "meaning": null,
        "surname_fit": null,
        "industry_fit": null,
        "cuteness": null,
        "imagery": null,
        "callability": null
      }},
      "score_reason": "string"
    }}
  ]
}}
The names array must contain exactly 5 items."""
        try:
            raw_response = await llm.ainvoke(json_prompt)
            content = getattr(raw_response, "content", raw_response)
            if isinstance(content, dict):
                return _ensure_valid_name_result(content, scene, result_schema)

            if isinstance(content, list):
                content = "".join(str(item) for item in content)
            if not isinstance(content, str) or not content.strip():
                raise ValueError(f"{scene} JSON fallback returned empty content: {raw_response!r}")

            payload = _extract_json_object(content)
            return _ensure_valid_name_result(payload, scene, result_schema)
        except Exception as e:
            last_error = e
            print(f"[NameGeneration] {scene} JSON fallback attempt {attempt} failed: {e}")

    raise NameGenerationError(
        f"{scene}生成失败：AI 输出无法解析为有效 JSON，已重试 {JSON_FALLBACK_MAX_ATTEMPTS} 次，请稍后重试或简化需求。"
    ) from last_error


async def _invoke_name_llm(
    prompt: str,
    scene: str,
    result_schema: type[NameResultSchema] = NameResultSchema,
) -> NameResultSchema:
    if hasattr(llm, "with_structured_output"):
        structured_runner = llm.with_structured_output(result_schema).with_retry(stop_after_attempt=3)
    else:
        structured_runner = structured_llm
    response = await structured_runner.ainvoke(prompt)
    if isinstance(response, result_schema) and response.names:
        try:
            return _ensure_valid_name_result(response, scene, result_schema)
        except Exception as e:
            print(f"[NameGeneration] {scene} structured output needs fallback repair: {e}")
    if isinstance(response, NameResultSchema) and response.names:
        try:
            return _ensure_valid_name_result(response, scene, result_schema)
        except Exception as e:
            print(f"[NameGeneration] {scene} generic structured output needs fallback repair: {e}")

    print(f"[NameGeneration] {scene} structured output invalid, trying JSON fallback: {response!r}")
    try:
        return await _invoke_json_name_llm(prompt, scene, result_schema)
    except NameGenerationError:
        raise
    except Exception as e:
        print(f"[NameGeneration] {scene} JSON fallback invalid: {e}")

    raise NameGenerationError(f"{scene}生成失败：模型未返回有效的结构化起名结果，请稍后重试。")


class WorkFlowState(TypedDict, total=False):
    user_id: int
    category: str
    surname: str
    gender: str
    length: str
    other: str
    exclude: List[str]
    final_output: Dict[str, Any]
    thread_id: str
    history_names: str
    feedback: str


llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=settings.DEEPSEEK_API_KEY,
    temperature=0.5,
)
structured_llm = llm.with_structured_output(NameResultSchema).with_retry(stop_after_attempt=3)


async def supervisor_node(state: WorkFlowState):
    return {}


def _build_feedback_instruction(state: WorkFlowState) -> str:
    if not state.get("feedback") or not state.get("history_names"):
        return ""

    return f"""
【多轮反馈优化规则】
请先读取并理解上一轮候选名，不要把本次反馈当成全新起名任务。

【上一轮历史结果】
{state['history_names']}

【用户最新指出的问题】
{state['feedback']}

执行规则：
1. 保留用户没有否定的候选名特点，包括风格、意象、语气、字数、读音节奏、寓意方向、品牌/IP 调性等。
2. 只修改用户指出的问题；以用户明确指出的问题为边界，不要扩大修改范围，不要抛弃历史记录重新随机生成。
3. 如果用户只要求调整部分候选名，其余候选应延续原有满意特点，可做轻微润色但不能整体换风格。
4. 人名、企业名、宠物/IP 三类都必须参考上一轮历史结果；人名要继续参考姓氏和音韵，宠物/IP 要继续参考角色画面和呼喊感。
5. 反馈后仍然必须返回【恰好 5 个】候选名，不能多也不能少。
"""


def _format_history_names(response: NameResultSchema) -> str:
    return "\n".join(f"【{n.name}】寓意：{n.moral}" for n in response.names)


async def _check_company_domains(response: NameResultSchema, max_checks: int = 5) -> None:
    candidates = [name for name in response.names if name.domain][:max_checks]
    if not candidates:
        return

    try:
        results = await asyncio.wait_for(
            asyncio.gather(
                *(check_com_domain(name.domain) for name in candidates),
                return_exceptions=True,
            ),
            timeout=8,
        )
    except Exception as exc:
        print(f"[DOMAIN] failed to check domains: {exc}")
        for name in candidates:
            name.domain_status = "域名查询暂不可用"
        return

    for name, result in zip(candidates, results):
        if isinstance(result, Exception):
            name.domain_status = "域名查询暂不可用"
            continue
        name.domain = result.domain
        name.domain_status = result.status


def _clear_non_company_domains(response: NameResultSchema) -> None:
    for name in response.names:
        name.domain = None
        name.domain_status = None
        name.risk_level = None
        name.risk_reason = None


def _build_score_output_instruction(category: str) -> str:
    common_instruction = """

【候选名评分要求】
请为每个候选名返回可解释评分，所有分数均为 0-100 的整数。
- score：综合评分，0-100。
- score_detail：评分明细对象，必须保留 brand_sense、memorability、differentiation、fit、spreadability 五个兼容字段，并按当前类别补充专属评分字段。
  - brand_sense：品牌感/命名质感，是否像真实可用的名字，而不是普通描述词。
  - memorability：记忆度，是否顺口、简洁、容易记住。
  - differentiation：差异化，是否有独特识别点，避免同质化和套话。
  - fit：匹配度，是否贴合用户需求、行业/人物/宠物设定、调性和避讳要求。
  - spreadability：可传播性，是否便于口头传播、社媒展示、搜索识别或日常呼唤。
- score_reason：评分理由，用 1-2 句话说明该候选名为什么得到这个分数，必须点到主要优点和扣分点。
"""
    category_instructions = {
        "human": """
【人名专属评分口径】
score 综合评分按：音韵 30% + 寓意 30% + 姓氏匹配 25% + 记忆度 15%。
score_detail 必须额外包含：
- phonology：音韵评分，判断声调起伏、读音流畅度、是否拗口。
- meaning：寓意评分，判断字义、祝愿、文化出处和解释是否稳妥有美感。
- surname_fit：姓氏匹配评分，判断名字与姓氏连读是否自然，是否产生歧义或谐音问题。
兼容字段映射建议：memorability 参考音韵和记忆度，fit 参考姓氏匹配和用户要求，brand_sense 可理解为人名质感。
""",
        "company": """
【企业名专属评分口径】
score 综合评分按：品牌感 30% + 行业匹配 25% + 传播性 25% + 差异化 20%。
score_detail 必须额外包含：
- industry_fit：行业匹配评分，判断是否贴合行业、产品/服务、客群、品牌调性和知识库要点。
兼容字段映射要求：brand_sense 表示品牌感，spreadability 表示传播性，differentiation 表示差异化，fit 与 industry_fit 保持一致或接近。
""",
        "pet": """
【宠物/IP 专属评分口径】
score 综合评分按：可爱度 30% + 画面感 30% + 呼喊顺口度 25% + 传播性 15%。
score_detail 必须额外包含：
- cuteness：可爱度评分，判断名字是否亲切、有昵称感或角色亲和力。
- imagery：画面感评分，判断是否能联想到具体动作、毛色、性格或 IP 场景。
- callability：呼喊顺口度评分，判断日常反复叫唤是否自然、短促、清晰。
兼容字段映射建议：memorability 参考呼喊顺口度，fit 参考宠物/IP 设定匹配，spreadability 参考传播性。
""",
    }
    return common_instruction + category_instructions[category]


async def human_naming_node(state: WorkFlowState):
    feedback_instruction = _build_feedback_instruction(state)
    prompt = f"""你是一位精通汉语言文学、古典诗文与现代审美的人名命名专家。
请严格根据用户信息生成【恰好 5 个】候选人名，并保证每个名字都适合中文人名使用。

【姓氏】{state.get('surname', '')}
【性别倾向】{state.get('gender', '')}
【字数限制】{state.get('length', '')}
【其他具体要求】{state.get('other', '')}
【避讳排除字】{'、'.join(state.get('exclude', []))}

命名要求：
1. 每个名字必须包含姓氏，不要只给名不带姓。
2. 名字数量必须恰好 5 个，不要多也不要少。
3. 名字应自然、雅正、好读，避免生僻字、拗口字、网感过重或明显商业化表达。
4. 严格避开用户提供的避讳字；如果避讳字为空，也不要主动使用明显负面含义的字。
5. 优先从《诗经》《楚辞》、唐诗宋词、成语典故或传统文化意象中取意；如果没有直接典故，也要说明灵感来源。

输出字段要求：
- name：完整姓名。
- reference：出处或灵感来源，写清作品/典故/意象，不要留空。
- moral：同时写【寓意】和【解释】，说明名字表达的品格、祝愿、读音或字义搭配。
- domain：人名场景不需要真实域名，可以省略或填写 null。
- domain_status：人名场景不需要域名查询，可以省略或填写 null。

请只输出符合结构化格式的数据，不要输出额外说明文字。"""
    prompt += f"""
{feedback_instruction}
如果这是一次反馈优化，请优先服从用户最新修改意见，并在保留用户满意部分的基础上迭代；不要抛弃历史记录重新随机生成。
"""
    prompt += _build_score_output_instruction("human")
    response = await _invoke_name_llm(prompt, "人名", HumanNameResultSchema)
    _clear_non_company_domains(response)
    return {"final_output": response.model_dump(), "history_names": _format_history_names(response)}


async def company_naming_node(state: WorkFlowState):
    feedback_instruction = _build_feedback_instruction(state)

    user_id = state.get("user_id")
    search_query = state.get("other")
    rag_context = retrive_user_from_knowledge(user_id, search_query)

    prompt = f"""你是一位资深品牌命名顾问，擅长把行业属性、品牌调性、商业定位和用户私有知识库融合成可传播的商业品牌名。
请为用户生成【恰好 5 个】企业/品牌名候选，每个名字都要像真实商业品牌，而不是普通描述词或口号。

【用户需求 brief】
- 行业、业务方向、目标客群、品牌调性或核心诉求：{state.get("other")}
- 字数限制：{state.get('length', '')}
- 避讳排除字：{'、'.join(state.get('exclude', []))}

【用户专属知识库内容】
{rag_context}

【知识库使用规则】
- 如果知识库内容提示“用户尚未上传企业知识库”，说明当前没有私有资料可用，请直接根据用户需求 brief、行业常识和品牌命名经验完成命名。
- 如果知识库内容提示“本次未检索到相关内容”，说明用户上传过资料但与当前需求不匹配，请以用户当前输入为主，结合行业常识补足。
- 如果知识库内容提示“知识库检索服务暂时不可用”，说明 RAG 服务降级，请不要向用户暴露内部异常，按普通企业命名任务稳定输出。
- 如果知识库内容提示“已检索当前登录用户自己的企业知识库”，说明资料只来自当前用户私有知识库，可以作为命名依据；不要假设或引用其他用户资料。
- 只有当知识库内容包含真实参考资料时，才主动吸收其中的产品特点、目标客群、核心卖点、品牌调性、禁忌词、企业规则、关键词或差异化定位。
- 检索内容可能已因过长被摘要式截断；只能使用片段中明确出现的信息，不要补写未出现的具体事实、数字、资质或承诺。
- 如果资料中出现“禁用、避免、不要、禁忌、负面联想、不能使用”等表达，必须视为命名避讳，不得用于候选名。
- 如果资料中出现“高端、年轻化、科技感、东方感、亲和、可信赖、环保、专业”等调性描述，必须体现在 reference、moral 和评分理由中。

命名策略：
1. 先理解用户所在行业、核心产品/服务、目标客户和品牌调性，再命名。
2. 当知识库内容包含真实参考资料时，必须主动吸收其中的产品特点、企业规则、品牌禁忌、关键词、品牌调性或差异化卖点；不要机械复述知识库原文。
3. 名字要具备商业品牌感：简洁、好读、好记、可注册、可传播，避免像项目说明、技术参数或长句。
4. 风格要贴合品牌调性，例如科技感、亲和力、高端感、东方感、年轻化、可信赖等；如果用户没有明确调性，请根据行业做合理推断。
5. 严格避开用户提供的避讳字，也不要使用负面、低俗、歧义或容易侵权的表达。
6. 输出必须恰好 5 个候选，不要多也不要少。

输出字段要求：
- name：企业/品牌名，优先 2-4 个汉字，若用户指定长度则以用户要求为准。
- reference：说明名字的创意来源，必须尽量体现行业、产品特点、品牌调性、知识库要点或商业定位。
- moral：写清品牌寓意和商业解释，包括面向客户的价值感、传播感、差异化，以及如何避开禁忌词或负面联想。
- domain：为该名字设计一个简短、纯小写、无空格的 .com 域名建议。
- domain_status：先填写“正在查询...”，后端会统一查询并覆盖。
- risk_level：初步命名风险等级，只能填写 low、medium、high、unknown；若缺少外部检索依据，填写 unknown。
- risk_reason：初步风险说明，说明是否存在同质化、侵权联想、负面含义或传播歧义。

{feedback_instruction}
如果这是一次反馈优化，请优先服从用户最新修改意见，并在保留用户满意部分的基础上迭代；不要抛弃历史记录重新随机生成。
请只输出符合结构化格式的数据，不要输出额外说明文字。"""
    prompt += _build_score_output_instruction("company")
    response = await _invoke_name_llm(prompt, "企业名", CompanyNameResultSchema)
    names_str = _format_history_names(response)

    await _check_company_domains(response)

    return {"final_output": response.model_dump(), "history_names": names_str}


async def pet_naming_node(state: WorkFlowState) -> Dict[str, Any]:
    feedback_instruction = _build_feedback_instruction(state)
    prompt = f"""你是一位擅长宠物与虚拟 IP 命名的创意顾问，风格可爱、亲切、好记，并且富有画面感。
请根据用户描述生成【恰好 5 个】宠物名或 IP 名候选。

【宠物/IP 特征、性格或设定】{state.get('other', '')}
【字数限制】{state.get('length', '')}
【避讳排除字】{'、'.join(state.get('exclude', []))}

命名要求：
1. 名字要可爱、顺口、容易呼唤，适合日常反复叫唤或作为 IP 角色名传播。
2. 优先使用 1-3 个字；可以使用叠音、昵称感、小名感、拟声感或轻微反差萌，但不要幼稚到难以使用。
3. 必须结合宠物/IP 的毛色、体型、动作、性格、习惯、角色设定或用户给出的画面细节。
4. 每个名字都要让人能联想到一个具体画面。
5. 严格避开用户提供的避讳字，避免负面、拗口、生僻或容易误解的表达。
6. 输出必须恰好 5 个候选，不要多也不要少。

输出字段要求：
- name：宠物/IP 名，短小、可爱、好记。
- reference：说明名字来自哪个特征、性格、动作、毛色或 IP 设定。
- moral：写清名字的可爱点、画面感和适合呼唤/传播的理由。
- domain：宠物/IP 场景不需要真实域名，可以省略或填写 null。
- domain_status：宠物/IP 场景不需要域名查询，可以省略或填写 null。

请只输出符合结构化格式的数据，不要输出额外说明文字。"""
    prompt += f"""
{feedback_instruction}
如果这是一次反馈优化，请优先服从用户最新修改意见，并在保留用户满意部分的基础上迭代；不要抛弃历史记录重新随机生成。
"""
    prompt += _build_score_output_instruction("pet")
    response = await _invoke_name_llm(prompt, "宠物名", PetNameResultSchema)
    _clear_non_company_domains(response)
    return {"final_output": response.model_dump(), "history_names": _format_history_names(response)}


def route_by_category(state: WorkFlowState):
    category_map = {
        "人名": "human_naming_node",
        "企业名": "company_naming_node",
        "宠物名": "pet_naming_node",
    }
    category = state.get("category")
    target_node = category_map.get(category)
    if target_node is None:
        allowed_categories = "、".join(category_map)
        raise ValueError(f"未知起名分类: {category!r}，允许值: {allowed_categories}")
    return target_node


workflow = StateGraph(WorkFlowState)
workflow.add_node("supervisor_node", supervisor_node)
workflow.add_node("human_naming_node", human_naming_node)
workflow.add_node("company_naming_node", company_naming_node)
workflow.add_node("pet_naming_node", pet_naming_node)
workflow.set_entry_point("supervisor_node")
workflow.add_conditional_edges(
    "supervisor_node",
    route_by_category,
    {
        "human_naming_node": "human_naming_node",
        "company_naming_node": "company_naming_node",
        "pet_naming_node": "pet_naming_node",
    },
)
workflow.add_edge("human_naming_node", END)
workflow.add_edge("pet_naming_node", END)
workflow.add_edge("company_naming_node", END)


CHECKPOINT_DB_URI = settings.LANGGRAPH_CHECKPOINT_DB_URI
CHECKPOINT_CONNECT_TIMEOUT = settings.LANGGRAPH_CHECKPOINT_CONNECT_TIMEOUT
CHECKPOINT_FALLBACK_TO_MEMORY = settings.LANGGRAPH_CHECKPOINT_FALLBACK_TO_MEMORY

connection_pool: AsyncConnectionPool | None = None
memory: AsyncPostgresSaver | InMemorySaver | None = None
naming_graph = None


async def init_graph():
    """Initialize graph memory, falling back to in-memory checkpoints when PostgreSQL is unavailable."""
    global connection_pool, memory, naming_graph
    if naming_graph is not None:
        return

    try:
        connection_pool = AsyncConnectionPool(
            CHECKPOINT_DB_URI,
            max_size=10,
            open=False,
            timeout=CHECKPOINT_CONNECT_TIMEOUT,
            reconnect_timeout=CHECKPOINT_CONNECT_TIMEOUT,
            kwargs={"autocommit": True},
        )
        await connection_pool.open(wait=True, timeout=CHECKPOINT_CONNECT_TIMEOUT)
        memory = AsyncPostgresSaver(connection_pool)
        await memory.setup()
        print("[LangGraph] 使用 PostgreSQL checkpointer")
    except Exception as e:
        if connection_pool is not None:
            await connection_pool.close()
            connection_pool = None
        if not CHECKPOINT_FALLBACK_TO_MEMORY:
            raise RuntimeError(
                "LangGraph PostgreSQL checkpointer is unavailable. "
                "Set LANGGRAPH_CHECKPOINT_DB_URI to a reachable PostgreSQL database, "
                "or set LANGGRAPH_CHECKPOINT_FALLBACK_TO_MEMORY=true for local development."
            ) from e
        memory = InMemorySaver()
        print(
            "[LangGraph] PostgreSQL checkpointer unavailable; "
            "falling back to in-memory checkpoints for local development. "
            "Thread memory will not survive process restarts. "
            "Configure LANGGRAPH_CHECKPOINT_DB_URI for persistent memory. "
            f"Error: {e}"
        )

    naming_graph = workflow.compile(checkpointer=memory)


async def generate_naming(name_info: NameIn, user_id: int):
    await init_graph()
    workflow_state = {
        "user_id": user_id,
        "category": name_info.category,
        "surname": name_info.surname,
        "gender": name_info.gender,
        "length": name_info.length,
        "other": name_info.other,
        "exclude": name_info.exclude,
        "final_output": {},
    }
    final_state = await naming_graph.ainvoke(workflow_state)
    return final_state["final_output"]


async def generate_naming_v2(name_info: NameIn, user_id: int):
    await init_graph()
    thread_id = str(uuid.uuid4())
    workflow_state = {
        "thread_id": thread_id,
        "user_id": user_id,
        "category": name_info.category,
        "surname": name_info.surname,
        "gender": name_info.gender,
        "length": name_info.length,
        "other": name_info.other,
        "exclude": name_info.exclude,
        "final_output": {},
    }
    config = {"configurable": {"thread_id": thread_id}}
    final_state = await naming_graph.ainvoke(workflow_state, config)
    return {"thread_id": thread_id, "names": final_state["final_output"]}


async def feedback_names(name_info: FeedbackSchema, user_id: int):
    update_state = {
        "user_id": user_id,
        "feedback": name_info.feedback,
        "category": name_info.category,
    }
    if name_info.history_names:
        update_state["history_names"] = name_info.history_names
    config = {"configurable": {"thread_id": name_info.thread_id}}
    final_state = await naming_graph.ainvoke(update_state, config)
    return {"thread_id": name_info.thread_id, "names": final_state["final_output"]}
