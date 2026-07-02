from core.workflow import (
    feedback_names,
    generate_naming,
    generate_naming_v2,
    init_graph,
)
from schemas.name_schemas import FeedbackSchema, NameIn


class AIService:
    """Business-facing wrapper around the LangGraph naming workflow."""

    async def generate_legacy_names(self, name_info: NameIn, user_id: int):
        await init_graph()
        return await generate_naming(name_info, user_id)

    async def generate_names(self, name_info: NameIn, user_id: int):
        await init_graph()
        return await generate_naming_v2(name_info, user_id)

    async def feedback_names(self, data: FeedbackSchema, user_id: int):
        await init_graph()
        return await feedback_names(data, user_id)
