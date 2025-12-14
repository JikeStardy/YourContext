import logging
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import TodoListMiddleware

from yourcontext.prompts import CHATBOT_PROMPT
from yourcontext.tools.search import TongyiSearch

async def get_chat_agent():
    qwen3_max = init_chat_model(
        model="openai:qwen3-max"
    )
    tools = []

    logging.info("model initiated, now we going on create tools")

    tongyi = TongyiSearch.create("")
    tools.extend(await tongyi.tools)

    logging.info("tongyi initiated, now we going on create chat agent")

    chat_agent = create_agent(
        model=qwen3_max,
        tools=tools,
        system_prompt=CHATBOT_PROMPT,
        middleware=[TodoListMiddleware()],
    )

    logging.info("agent created")

    return chat_agent


