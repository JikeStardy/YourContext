from langchain_openai import ChatOpenAI


class ChatBailian(ChatOpenAI):
    """
    A ChatBailian model that extends the ChatOpenAI model.
    """
    def __init__(self, **kwargs):
        """
        Initialize the ChatBailian model with the given keyword arguments.
        """
        super().__init__(base_url=config.get("bailian_base_url"), api_key=config.get("bailian_api_key"), **kwargs)