import asyncio
from contextlib import asynccontextmanager
import logging
import threading
from typing import List
from langchain_core.tools.base import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from yourcontext.config.config_manager import ConfigManager

class TongyiSearch:
    _instances = {}
    _lock = threading.Lock()
    
    def __init__(self, tongyi_api_key: str):
        self._tongyi_api_key = tongyi_api_key
        self._client = None

    @property
    def tool_name(self):
        return "tongyi_websearch"
    
    @property
    def tools(self) -> List[BaseTool]:
        return self._client.get_tools()
    
    @classmethod
    def create(cls, tongyi_api_key: str=None) -> "TongyiSearch":
        with cls._lock:
            if not tongyi_api_key:
                tongyi_api_key = ConfigManager.singleton().get("YourContext.tools.aliyun_bailian.api_key")
            if tongyi_api_key not in cls._instances:
                self = cls(tongyi_api_key)
                self._client = MultiServerMCPClient(  
                    {
                        self.tool_name: {
                            "transport": "sse",
                            "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
                            "headers": {"Authorization": f"Bearer {self._tongyi_api_key}"},
                        },
                    }
                )
                cls._instances[tongyi_api_key] = self
                logging.info(f"initiated mcp client for {self.tool_name}")
        return cls._instances[tongyi_api_key]
