import asyncio
import sys

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from settings import LANGGRAPH_CHECKPOINT_DB_URI


async def setup_memory_db():
    try:
        print("Connecting to LangGraph PostgreSQL checkpoint database...")
        async with AsyncPostgresSaver.from_conn_string(LANGGRAPH_CHECKPOINT_DB_URI) as saver:
            await saver.setup()
    except Exception as exc:
        raise RuntimeError(
            "Unable to initialize LangGraph PostgreSQL checkpoint tables. "
            "Set LANGGRAPH_CHECKPOINT_DB_URI to a reachable PostgreSQL database."
        ) from exc

    print("LangGraph PostgreSQL checkpoint tables are ready.")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(setup_memory_db())
