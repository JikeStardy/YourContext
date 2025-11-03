#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import List, Dict, Any
from storage.backend.storage_backend_factory import IStorageBackend, register_backend
from loguru import logger

logger = logger.bind(module=__name__)

@register_backend(
    name="memory",
    supported_types=["memory", "ram", "volatile"],
    description="内存存储后端 - 高速但非持久化存储",
    priority=100,
    author="AI Assistant",
    version="1.0.0"
)
class MemoryBackend(IStorageBackend):
    """
    内存存储后端实现。
    数据存储在内存中，重启后数据会丢失，但访问速度极快。
    """
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        self._data: Dict[str, Any] = {}
        self._connected = False
        self._max_size = self.config.get('max_size', 1000)
        self._ttl = self.config.get('ttl', 3600)  # 默认1小时过期
        logger.info(f"初始化MemoryBackend，配置: {self.config}")
    
    def connect(self) -> bool:
        """连接到存储后端"""
        try:
            self._connected = True
            logger.success("MemoryBackend连接成功")
            return True
        except Exception as e:
            logger.error(f"MemoryBackend连接失败: {e}")
            return False
    
    def disconnect(self) -> bool:
        """断开连接"""
        try:
            self._connected = False
            self._data.clear()  # 断开时清空数据
            logger.info("MemoryBackend已断开")
            return True
        except Exception as e:
            logger.error(f"MemoryBackend断开失败: {e}")
            return False
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    def get(self, key: str) -> Any:
        """获取数据"""
        if not self.is_connected():
            raise RuntimeError("Backend未连接")
        return self._data.get(key)
    
    def set(self, key: str, value: Any) -> bool:
        """设置数据"""
        if not self.is_connected():
            raise RuntimeError("Backend未连接")
        
        if len(self._data) >= self._max_size:
            logger.warning(f"MemoryBackend达到最大容量限制: {self._max_size}")
            return False
        
        self._data[key] = value
        return True
    
    def delete(self, key: str) -> bool:
        """删除数据"""
        if not self.is_connected():
            raise RuntimeError("Backend未连接")
        
        if key in self._data:
            del self._data[key]
            return True
        return False
    
    def keys(self) -> List[str]:
        """获取所有键"""
        if not self.is_connected():
            raise RuntimeError("Backend未连接")
        return list(self._data.keys())
    
    def clear(self) -> bool:
        """清空所有数据"""
        if not self.is_connected():
            raise RuntimeError("Backend未连接")
        
        self._data.clear()
        return True
    
    def size(self) -> int:
        """获取数据数量"""
        return len(self._data)
    
    def __repr__(self) -> str:
        return f"MemoryBackend(connected={self._connected}, size={self.size()})"