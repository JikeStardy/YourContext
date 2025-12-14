import asyncio
from contextlib import asynccontextmanager
import logging
import threading
from typing import List
from langchain_core.tools.base import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

class TavilySearch:
    _instances = {}
    _lock = threading.Lock()

    def __init__(self, tavily_api_key: str):
        self._tavily_api_key = tavily_api_key
        self._client = None

    @property
    def tool_name(self):
        return "tavily"
    
    @property
    def tools(self) -> List[BaseTool]:
        return self._client.get_tools()
    
    @classmethod
    def create(cls, tavily_api_key: str) -> "TavilySearch":
        with cls._lock:
            if tavily_api_key not in cls._instances:
                self = cls(tavily_api_key)
                self._client = MultiServerMCPClient(  
                    {
                        self.tool_name: {
                            "transport": "streamable_http",
                            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={self._tavily_api_key}"
                        },
                    }
                )
                cls._instances[tavily_api_key] = self
                logging.info(f"initiated mcp client for {self.tool_name}")
        return cls._instances[tavily_api_key]
