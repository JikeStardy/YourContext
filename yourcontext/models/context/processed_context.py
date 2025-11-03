
import uuid
from pydantic import BaseModel, Field


class ProcessedContext(BaseModel):
    """
    处理后的上下文模型，包含原始上下文和处理后的上下文。
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_context: str
    processed_context: str