from storage.backend.storage_backend_factory import StorageBackendFactory
from loguru import logger

logger = logger.bind(module=__name__)

class UnifiedStorage:
    """
    统一存储类，用于管理不同类型的存储后端。

    :param storage_type: 存储类型，例如 'memory', 'redis', 'mongodb' 等。
    :param storage_config: 存储配置，包含连接信息、认证信息等。
    """

    def __init__(self, storage_type: str, storage_config: dict):
        self._factory = StorageBackendFactory()
        self._initialized = False
        self._available_backends = list()

    def initialize(self):
        """
        初始化存储后端。
        """
        try:
            if not self._initialized:
                for backend in self._factory.get_available_backends():
                    self._available_backends.append(backend)
                self._storage = self._factory._create_storage(storage_type, storage_config)
                self._initialized = True
        except Exception as e:
            logger.exception(f"初始化存储后端失败: {e}")
