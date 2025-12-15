import asyncio
import logging
from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware

from yourcontext.agents.sub_agents.video_agent import call_video_agent
from yourcontext.config.config_manager import ConfigManager
from yourcontext.models.llm.chat_bailian import ChatBailian
from yourcontext.prompts import CHATBOT_PROMPT
from yourcontext.tools.search import TongyiSearch

async def get_chat_agent():
    tools = []

    tools.append(call_video_agent)

    tongyi = TongyiSearch.create()
    tools.extend(await tongyi.tools)

    chat_agent = create_agent(
        model=ChatBailian(model=ConfigManager.singleton().get("YourContext.model.chat.model")),
        tools=tools,
        system_prompt=CHATBOT_PROMPT,
        middleware=[TodoListMiddleware()],
    )

    return chat_agent

jarvis = asyncio.run(get_chat_agent())
