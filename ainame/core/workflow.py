import asyncio
import json
import os
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
from schemas.name_schemas import FeedbackSchema, NameIn, NameResultSchema


if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class NameGenerationError(RuntimeError):
    """Raised when the LLM does not return a usable naming result."""


def _ensure_valid_name_result(result: NameResultSchema, scene: str) -> NameResultSchema:
    if len(result.names) != 5:
        raise ValueError(f"{scene} result must contain exactly 5 names, got {len(result.names)}")
    return result


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


async def _invoke_json_name_llm(prompt: str, scene: str) -> NameResultSchema:
    json_prompt = f"""{prompt}

IMPORTANT:
Return valid JSON only. Do not use markdown fences or extra text.
The JSON schema must be:
{{
  "names": [
    {{
      "name": "string",
      "reference": "string",
      "moral": "string",
      "domain": null,
      "domain_status": null
    }}
  ]
}}
The names array must contain exactly 5 items."""
    raw_response = await llm.ainvoke(json_prompt)
    content = getattr(raw_response, "content", raw_response)
    if isinstance(content, dict):
        payload = content
        result = NameResultSchema.model_validate(payload)
        return _ensure_valid_name_result(result, scene)

    if isinstance(content, list):
        content = "".join(str(item) for item in content)
    if not isinstance(content, str) or not content.strip():
        raise ValueError(f"{scene} JSON fallback returned empty content: {raw_response!r}")

    payload = _extract_json_object(content)
    result = NameResultSchema.model_validate(payload)
    return _ensure_valid_name_result(result, scene)


async def _invoke_name_llm(prompt: str, scene: str) -> NameResultSchema:
    response = await structured_llm.ainvoke(prompt)
    if isinstance(response, NameResultSchema) and response.names:
        return _ensure_valid_name_result(response, scene)

    print(f"[NameGeneration] {scene} structured output invalid, trying JSON fallback: {response!r}")
    try:
        return await _invoke_json_name_llm(prompt, scene)
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
【反馈优化要求】
上一轮生成结果：
{state['history_names']}

用户最新修改意见：
{state['feedback']}

请保留上一轮中用户满意的部分，只修改用户指出的问题；不要抛弃历史记录重新随机生成。
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
    response = await _invoke_name_llm(prompt, "人名")
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
- 只有当知识库内容包含真实参考资料时，才主动吸收其中的产品特征、企业规则、品牌禁忌、关键词或差异化卖点。

命名策略：
1. 先理解用户所在行业、核心产品/服务、目标客户和品牌调性，再命名。
2. 当知识库内容包含真实参考资料时，必须主动吸收其中的产品特征、企业规则、品牌禁忌、关键词或差异化卖点；不要机械复述知识库原文。
3. 名字要具备商业品牌感：简洁、好读、好记、可注册、可传播，避免像项目说明、技术参数或长句。
4. 风格要贴合品牌调性，例如科技感、亲和力、高端感、东方感、年轻化、可信赖等；如果用户没有明确调性，请根据行业做合理推断。
5. 严格避开用户提供的避讳字，也不要使用负面、低俗、歧义或容易侵权的表达。
6. 输出必须恰好 5 个候选，不要多也不要少。

输出字段要求：
- name：企业/品牌名，优先 2-4 个汉字，若用户指定长度则以用户要求为准。
- reference：说明名字的创意来源，应体现行业、品牌调性、知识库要点或商业定位。
- moral：写清品牌寓意和商业解释，包括面向客户的价值感、传播感或差异化。
- domain：为该名字设计一个简短、纯小写、无空格的 .com 域名建议。
- domain_status：先填写“正在查询...”，后端会统一查询并覆盖。

{feedback_instruction}
如果这是一次反馈优化，请优先服从用户最新修改意见，并在保留用户满意部分的基础上迭代；不要抛弃历史记录重新随机生成。
请只输出符合结构化格式的数据，不要输出额外说明文字。"""
    response = await _invoke_name_llm(prompt, "企业名")
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
    response = await _invoke_name_llm(prompt, "宠物名")
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


CHECKPOINT_DB_URI = os.getenv("LANGGRAPH_CHECKPOINT_DB_URI", "postgresql://postgres:123456@localhost:5432/ainame")
CHECKPOINT_CONNECT_TIMEOUT = float(os.getenv("LANGGRAPH_CHECKPOINT_CONNECT_TIMEOUT", "10"))

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
        memory = InMemorySaver()
        print(f"[LangGraph] PostgreSQL checkpointer 不可用，已降级为内存记忆: {e}")

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
    config = {"configurable": {"thread_id": name_info.thread_id}}
    final_state = await naming_graph.ainvoke(update_state, config)
    return {"thread_id": name_info.thread_id, "names": final_state["final_output"]}
