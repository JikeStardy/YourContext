from langchain_openai import ChatOpenAI

from yourcontext.config import ConfigManager


class ChatBailian(ChatOpenAI):
    """
    A ChatBailian model that extends the ChatOpenAI model.
    """
    def __init__(self, **kwargs):
        """
        Initialize the ChatBailian model with the given keyword arguments.
        """
        super().__init__(
            base_url=ConfigManager.singleton().get("YourContext.tool.aliyun_bailian.base_url"), 
            api_key=ConfigManager.singleton().get("YourContext.tool.aliyun_bailian.api_key"), 
            **kwargs
        )