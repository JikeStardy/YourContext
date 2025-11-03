

from typing import List, Dict, Type, Callable, Optional

from abc import ABC, abstractmethod

from yourcontext.consts.storage import StorageType 

class IStorageBackend(ABC):
    """
    存储后端接口类，定义了所有存储后端必须实现的方法。
    """

    @abstractmethod
    def initialize(self, config) -> bool:
        """初始化存储后端"""
    
    @abstractmethod
    def get_name(self) -> str:
        """获取存储后端名称"""

    @abstractmethod
    def get_storage_type(self) -> StorageType:
        """获取存储后端类型"""
    
    @abstractmethod
    def insert(self, data: Dict) -> bool:
        """插入数据"""

    @abstractmethod
    def query(self, data: Dict) -> Optional[List[Dict]]:
        """读取数据"""

    @abstractmethod
    def update(self, data: Dict) -> bool:
        """更新数据"""

    @abstractmethod
    def delete(self, data: Dict, recycle: bool) -> bool:
        """删除数据"""


class StorageBackendFactory:
    """
    存储后端工厂类，用于创建不同类型的存储后端实例。
    现在支持通过装饰器自动注册的backend。
    """

    def __init__(self):
        pass
        
    def get_available_backends(self) -> List[Dict]:
        """
        获取所有可用的存储后端类型。
        返回注册backend的详细信息。
        
        :return: 包含所有可用存储后端信息的列表。
        """
        return self._available_backends
    
    def get_backend_names(self) -> List[str]:
        """
        获取所有已注册的backend名称。
        
        :return: backend名称列表
        """
        return list(_backend_registry.keys())
    
    def get_backend_info(self, name: str) -> Optional[Dict]:
        """
        获取指定backend的详细信息。
        
        :param name: backend名称
        :return: backend信息字典，如果不存在返回None
        """
        return _backend_registry.get(name)
    
    def get_backends_by_type(self, storage_type: str) -> List[Dict]:
        """
        根据存储类型获取支持该类型的所有backend。
        
        :param storage_type: 存储类型
        :return: 支持该类型的backend列表，按优先级排序
        """
        matching_backends = []
        for backend_info in self._available_backends:
            if storage_type in backend_info['supported_types']:
                matching_backends.append(backend_info)
        
        # 按优先级排序（数字越大优先级越高）
        return sorted(matching_backends, key=lambda x: x['priority'], reverse=True)
    
    def create_backend(self, name: str, config: dict = None) -> Optional[IStorageBackend]:
        """
        创建指定名称的存储后端实例。
        
        :param name: backend名称
        :param config: 配置信息
        :return: backend实例，如果不存在返回None
        """
        backend_info = _backend_registry.get(name)
        if backend_info:
            backend_class = backend_info['class']
            return backend_class(config)
        return None
    
    def create_backend_by_type(self, storage_type: str, config: dict = None) -> Optional[IStorageBackend]:
        """
        根据存储类型创建最合适的存储后端实例。
        
        :param storage_type: 存储类型
        :param config: 配置信息
        :return: backend实例，如果不存在支持的backend返回None
        """
        suitable_backends = self.get_backends_by_type(storage_type)
        if suitable_backends:
            # 选择优先级最高的backend
            best_backend = suitable_backends[0]
            return self.create_backend(best_backend['name'], config)
        return None