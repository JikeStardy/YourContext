import asyncio
import logging
from langchain.tools import tool
from langchain.agents import create_agent

from yourcontext.config.config_manager import ConfigManager
from yourcontext.models.llm.chat_bailian import ChatBailian
from yourcontext.prompts import VIDEO_SUBTITLE_CONTENT_ANALYZE
from yourcontext.tools.search import TongyiSearch
from yourcontext.tools.video.bilibili.bilibili_video import BilibiliVideo


async def get_video_agent():
    tools = []

    bili_video = BilibiliVideo.create()
    tools.extend(bili_video.tools)

    tongyi = TongyiSearch.create()
    tools.extend(await tongyi.tools)

    video_agent = create_agent(
        model=ChatBailian(model=ConfigManager.singleton().get("YourContext.model.video_analyze.model")),
        tools=tools,
        system_prompt=VIDEO_SUBTITLE_CONTENT_ANALYZE,
    )

    logging.info("agent created")

    return video_agent

video_agent = asyncio.run(get_video_agent())

@tool(
    "bilibili_video_agent",
    description="Call the video agent to obtain video-related information, such as fetching video content by its BV ID from bilibili.com",
)
def call_video_agent(query: str):
    """
    Call the video agent to obtain video-related information.

    Args:
        query (str): User query, e.g., "https://www.bilibili.com/video/BVxxxxxxxx", "BVxxxxxxxx", etc.

    Returns:
        str: Response from the video agent containing video-related information
    """
    result =  video_agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    return result["messages"][-1].content

