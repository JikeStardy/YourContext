from enum import Enum

class StorageType(Enum):
    """存储后端类型"""
    DOCUMENT_DB = "document_db"
    VECTOR_DB = "vector_db"
