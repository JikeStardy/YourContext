import logging
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import TodoListMiddleware

from yourcontext.prompts import VIDEO_SUBTITLE_CONTENT_ANALYZE
from yourcontext.tools.search import TavilySearch, TongyiSearch

async def get_video_agent():
    qwen3_max = init_chat_model(
        model="openai:qwen3-max"
    )
    tools = []

    logging.info("qwen3_max initiated, now we going on create tavily")

    # tavily = TavilySearch.create("")
    # tools.extend(await tavily.tools)

    # logging.info("tavily initiated, now we going on create video agent")

    tongyi = TongyiSearch.create("")
    tools.extend(await tongyi.tools)

    logging.info("tongyi initiated, now we going on create video agent")

    # video_agent = create_agent(
    #     model=qwen3_max,
    #     tools=tavily.tools,
    #     system_prompt=VIDEO_SUBTITLE_CONTENT_ANALYZE,
    # )

    video_agent = create_agent(
        model=qwen3_max,
        tools=tools,
        system_prompt=VIDEO_SUBTITLE_CONTENT_ANALYZE,
    )

    logging.info("agent created")

    return video_agent


