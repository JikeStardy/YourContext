from enum import Enum


class ContextType(str, Enum):
    """上下文类型枚举"""
    ENTITY_CONTEXT = "entity_context"
    ACTIVITY_CONTEXT = "activity_context"
    SEMANTIC_CONTEXT = "semantic_context"
    STATE_CONTEXT = "state_context"
