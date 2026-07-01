import asyncio
import uuid
from typing import TypedDict, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_deepseek import ChatDeepSeek
from pydantic import SecretStr
import settings
from schemas.name_schemas import NameIn
from schemas.name_schemas import NameResultSchema

# 定义工作流状态。这个状态是工作流的参数。也可以叫数据清单。是伴随整个流程的
# TypedDict 把我们的python类进行字典校验
class WorkFlowState(TypedDict):
    user_id: int
    category:str
    surname:str
    gender:str
    length:str
    other:str
    exclude:List[str]
    final_output:Dict[str, Any]  # 用来存大模型生成的数据
    thread_id:str
    history_names:str
    feedback: str

llm = ChatDeepSeek(
    model="deepseek-chat",
    api_key=settings.DEEPSEEK_API_KEY,
    temperature=0.5
)

# 告诉大模型，输出的格式是怎么的
structured_llm = llm.with_structured_output(NameResultSchema).with_retry(stop_after_attempt=3)

# 定义工作流的节点  这是一个工作流的入口，负责转发任务
async def supervisor_node(state: WorkFlowState):
    """主管节点：后续可在这里扩展意图清洗或记录日志"""
    return {}

async def human_naming_node(state: WorkFlowState):
    """人名专家节点"""
    prompt = f"""你是一位精通汉语言文学、古典诗文与现代审美的人名命名专家。
请严格根据用户信息生成【恰好 5 个】候选人名，并保证每个名字都适合中文人名使用。

【姓氏】{state['surname']}
【性别倾向】{state['gender']}
【字数限制】{state['length']}
【其它具体要求】{state['other']}
【避讳排除字】{'、'.join(state['exclude'])}

命名要求：
1. 每个名字必须包含姓氏，不要只给名不带姓。
2. 名字数量必须恰好为 5 个，不要多也不要少。
3. 名字应自然、雅正、好读，避免生僻字、拗口字、网感过重或明显商业化表达。
4. 严格避开用户提供的避讳字；如果避讳字为空，也不要主动使用明显负面含义的字。
5. 优先从《诗经》《楚辞》、唐诗宋词、成语典故或传统文化意象中取意；如果没有直接典故，也要说明灵感来源。

输出字段要求：
- name：完整姓名。
- reference：出处或灵感来源，写清作品/典故/意象，不要留空。
- moral：同时写【寓意】和【解释】，说明名字表达的品格、祝愿、读音或字义搭配。
- domain：人名场景不需要真实域名，请统一填写空字符串。
- domain_status：人名场景不需要域名查询，请统一填写“不适用”。

请只输出符合结构化格式的数据，不要输出额外说明文字。"""

    response = await  structured_llm.ainvoke(prompt)
    return {"final_output":response.model_dump()}

from core.rag_service import  retrive_user_from_knowledge
from core.tools import check_com_domain
async def company_naming_node(state: WorkFlowState):
    """企业品牌节点"""
    feedback_instruction = ""
    if state.get("feedback") and state.get("history_names"):
        feedback_instruction = f"""
              🟣 警告：这是一次微调请求！
              【上一轮你生成的名字是】：{state['history_names']}
              【用户的最新修改意见】：{state['feedback']}

              请严格保留上一轮中用户满意的部分，仅针对【修改意见】对历史名字进行迭代优化！绝不能抛弃历史记录重新随机生成！
              """

    user_id = state.get("user_id")
    search_query = state.get("other")

    # 1.查 通过用户的要求和useid查询语义数据库
    try:
        rag_context = retrive_user_from_knowledge(user_id, search_query)
    except Exception as exc:
        print(f"[RAG] failed to retrieve user knowledge for user_id={user_id}: {exc}")
        rag_context = "用户知识库暂不可用，请仅根据用户本次输入进行命名。"    # 2.用
    prompt = f"""你是一位资深品牌命名顾问，擅长把行业属性、品牌调性、商业定位和用户私有知识库融合成可传播的商业品牌名。
请为用户生成【恰好 5 个】企业/品牌名候选，每个名字都要像真实商业品牌，而不是普通描述词或口号。

【用户需求 brief】
- 行业、业务方向、目标客群、品牌调性或核心诉求：{state.get("other")}
- 字数限制：{state['length']}
- 避讳排除字：{'、'.join(state['exclude'])}

【用户专属知识库内容】
{rag_context}

命名策略：
1. 先理解用户所在行业、核心产品/服务、目标客户和品牌调性，再命名。
2. 必须主动吸收知识库里的产品特征、企业规则、品牌禁忌、关键词或差异化卖点；不要机械复述知识库原文。
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
如果这是一次反馈优化，请优先服从用户最新修改意见，并在保留用户满意方向的基础上迭代；不要抛弃历史记录重新随机生成。
请只输出符合结构化格式的数据，不要输出额外说明文字。"""
    response = await  structured_llm.ainvoke(prompt)
    memory_list = [f"【{n.name}】寓意：{n.moral}" for n in response.names]
    names_str = "\n".join(memory_list)

    try:
        tasks = [check_com_domain(n.domain) for n in response.names]
        statuses = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=8
        )
    except Exception as exc:
        print(f"[DOMAIN] failed to check domains: {exc}")
        statuses = ["域名查询暂不可用"] * len(response.names)

    for n, status in zip(response.names, statuses):
        if isinstance(status, Exception):
            n.domain_status = "域名查询暂不可用"
        else:
            n.domain_status = status

    # return {"final_output": response.model_dump()}
    #  "history_names": names_str}  主要是存到数据库，用来下次微调，从数据库中查询出来，给大模型，让他参考这些数据
    return {"final_output": response.model_dump(), "history_names": names_str}


async def pet_naming_node(state: WorkFlowState) -> Dict[str, Any]:
    """宠物起名节点"""
    prompt = f"""你是一位擅长宠物与虚拟 IP 命名的创意顾问，风格可爱、亲切、好记，并且富有画面感。
请根据用户描述生成【恰好 5 个】宠物名或 IP 名候选。

【宠物/IP 特征、性格或设定】{state['other']}
【字数限制】{state['length']}
【避讳排除字】{'、'.join(state['exclude'])}

命名要求：
1. 名字要可爱、顺口、容易呼唤，适合日常反复叫唤或作为 IP 角色名传播。
2. 优先使用 1-3 个字；可以使用叠音、昵称感、小名感、拟声感或轻微反差萌，但不要幼稚到难以使用。
3. 必须结合宠物/IP 的毛色、体型、动作、性格、习惯、角色设定或用户给出的画面细节。
4. 每个名字都要让人能联想到一个具体画面，例如“圆滚滚地跑来”“雪白小尾巴摇晃”“安静趴在窗边”等。
5. 严格避开用户提供的避讳字，避免负面、拗口、生僻或容易误解的表达。
6. 输出必须恰好 5 个候选，不要多也不要少。

输出字段要求：
- name：宠物/IP 名，短小、可爱、好记。
- reference：说明名字来自哪个特征、性格、动作、毛色或 IP 设定。
- moral：写清名字的可爱点、画面感和适合呼唤/传播的理由。
- domain：宠物/IP 场景不需要真实域名，请统一填写空字符串。
- domain_status：宠物/IP 场景不需要域名查询，请统一填写“不适用”。

请只输出符合结构化格式的数据，不要输出额外说明文字。"""
    response = await structured_llm.ainvoke(prompt)
    return {"final_output": response.model_dump()}

# 节点都设计了有4个，如何组成工作流，如何流转
def route_by_category(state: WorkFlowState):
    """条件路由：根据前端传来的 category 决定走哪个节点"""
    category_map = {
        "人名": "human_naming_node",
        "企业名": "company_naming_node",
        "宠物名": "pet_naming_node",
    }
    # 人名\企业名\宠物名
    category = state.get("category")
    target_node = category_map.get(category)
    if target_node is None:
        allowed_categories = "、".join(category_map)
        raise ValueError(f"未知起名分类: {category!r}，允许值: {allowed_categories}")
    return target_node

workflow = StateGraph(WorkFlowState)
# 第一个节点的名字是supervisor_node
workflow.add_node("supervisor_node",supervisor_node)
workflow.add_node("human_naming_node", human_naming_node)
workflow.add_node("company_naming_node", company_naming_node)
workflow.add_node("pet_naming_node", pet_naming_node)

# 设置工作流的入口
workflow.set_entry_point("supervisor_node")

# 从入口进来后，如何走
workflow.add_conditional_edges("supervisor_node",route_by_category,
                #{ "条件路由函数的返回值" : "目标节点的名称" }
    {
        "human_naming_node": "human_naming_node",
        "company_naming_node": "company_naming_node",
        "pet_naming_node": "pet_naming_node",
    })


workflow.add_edge("human_naming_node", END)
workflow.add_edge("pet_naming_node", END)
workflow.add_edge("company_naming_node", END)

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
# 1. 全局初始化：只执行一次，复用连接
# thread_id 存入psotgress
DB_URI = settings.POSTGRES_MEMORY_DB_URI

connection_pool: AsyncConnectionPool | None = None
memory: AsyncPostgresSaver | None = None
naming_graph = None  # 工作流实例
async def init_graph():
    """延迟初始化连接池 + 记忆 + 工作流"""
    global connection_pool, memory, naming_graph, workflow
    if connection_pool is None:
        connection_pool = AsyncConnectionPool(DB_URI, max_size=10)
        await connection_pool.open()
        memory = AsyncPostgresSaver(connection_pool)
        # 编译带记忆的图
        naming_graph = workflow.compile(checkpointer=memory)

# connection_pool = AsyncConnectionPool(DB_URI, max_size=10)
# # 挂载 PostgreSQL 记忆组件到工作流
# memory = AsyncPostgresSaver(connection_pool)
# # 带记忆的智能体
# naming_graph = workflow.compile(checkpointer=memory)
# 完成起名流程的定义
# naming_graph = workflow.compile()

#用户传过来的信息  告诉我给什么起名字，这些名字的对应要求有哪些
async def generate_naming(name_info: NameIn,user_id:int):
    await init_graph()  # 先初始化
    workflowsatae = {
        "user_id": user_id,
        "category": name_info.category,
        "surname": name_info.surname,
        "gender": name_info.gender,
        "length": name_info.length,
        "other": name_info.other,
        "exclude": name_info.exclude,
        "final_output": {}
    }
    final_state = await  naming_graph.ainvoke(workflowsatae)
    return  final_state["final_output"]

async def generate_naming_v2(name_info: NameIn,user_id:int):
    await init_graph()  # 先初始化
    # 生成窗口id
    thread_id = str(uuid.uuid4())
    workflowsatae = {
        "thread_id": thread_id,
        "user_id": user_id,
        "category": name_info.category,
        "surname": name_info.surname,
        "gender": name_info.gender,
        "length": name_info.length,
        "other": name_info.other,
        "exclude": name_info.exclude,
        "final_output": {}
    }
    config = {"configurable": {"thread_id": thread_id}}
    final_state = await  naming_graph.ainvoke(workflowsatae,config)
    return  {"thread_id": thread_id, "names":final_state["final_output"]}


from schemas.name_schemas import FeedbackSchema
async def feedback_names(name_info: FeedbackSchema,user_id:int):
    # 生成窗口id
    update_state = {
        "feedback":name_info.feedback,
        "category": name_info.category
    }
    config = {"configurable": {"thread_id": name_info.thread_id}}

    final_state = await  naming_graph.ainvoke(update_state, config)
    return {"thread_id": name_info.thread_id, "names": final_state["final_output"]}
