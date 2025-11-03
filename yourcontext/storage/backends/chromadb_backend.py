from functools import lru_cache
import threading
from typing import Any, List, Optional
import chromadb
from loguru import logger
from typing import Dict

from yourcontext.consts.storage import StorageType
from yourcontext.consts.context_type import ContextType
from yourcontext.storage.backends.storage_backend_factory import IStorageBackend

logger = logger.bind(module=__name__)

class ChromaDBBackend(IStorageBackend):
    """
    ChromaDB存储后端实现类。
    """

    def __init__(self, config: dict = None):
        self._client: Optional[chromadb.Client] = None
        self._initialized: bool = False
        self._config = None
        self._max_retry_count = 3
        self._retry_delay = 1.0
        self._pending_writes = []
        self._write_lock = threading.Lock()
        self._cleanup_registered = False
        self._collections: Dict[str, Any] = {}

    def get_name(self) -> str:
        return "chromadb"
    
    def get_storage_type(self) -> StorageType:
        return StorageType.VECTOR_DB
    
    def initialize(self, config) -> bool:
        """初始化ChromaDB存储后端"""
        try:
            self._config = config
            chroma_config = config.get("config", {})

            # Check mode configuration
            mode = chroma_config.get("mode", "local")

            if mode == "server":
                # Server mode
                self._is_server_mode = True
                host = chroma_config.get("host", "localhost")
                port = chroma_config.get("port", 1733)
                ssl = chroma_config.get("ssl", False)
                headers = chroma_config.get("headers", {})
                settings = chroma_config.get("settings", {})

                # Build server URL
                protocol = "https" if ssl else "http"
                server_url = f"{protocol}://{host}:{port}"

                logger.info(
                    f"Initializing ChromaDB in server mode: {server_url}")

                # Create HTTP client and test connection
                self._client = self._create_server_client(
                    host, port, ssl, headers, settings)

            else:
                # Local persistence mode
                self._is_server_mode = False
                path = chroma_config.get("path", "./persist/chromadb")
                logger.info(
                    f"Initializing ChromaDB in local persistence mode: {path}")

                if path:
                    self._client = chromadb.PersistentClient(path=path)
                else:
                    self._client = chromadb.Client()

            # Get all available context_types
            context_types = [ct.value for ct in ContextType]
            config.get("collection_prefix", "yourcontext")

            # Create a separate collection for each context_type
            for context_type in context_types:
                collection_name = f"{context_type}"
                collection = self._client.get_or_create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine",
                              "context_type": context_type},
                )
                self._collections[context_type] = collection

            self._initialized = True
            logger.info(
                f"ChromaDB vector backend initialized successfully, created {len(self._collections)} collections"
            )
            return True

        except Exception as e:
            logger.exception(
                f"ChromaDB vector backend initialization failed: {e}")
            return False
        
    def insert(self, data: Dict) -> bool:
        """插入数据"""
        return self._upsert(data)

    def query(self, data: Dict) -> Optional[List[Dict]]:
        """读取数据"""
        collection_name = data.pop("collection_name", "")
        if not collection_name:
            logger.error("collection_name is required for query")
            return None
        
        collection = self._ensure_collection(collection_name)
        if not collection:
            logger.error(f"Collection {collection_name} not found")
            return None
        
        query_embeddings = data.get("query_embeddings", None)
        query_texts = data.get("query_texts", None)
        ids = data.get("ids", None)
        n_results = data.get("n_results", 10)
        where = data.get("where", None)
        include = data.get("include", ["documents", "metadatas", "distances"])

        if query_embeddings or query_texts:
            results = collection.query(
                query_embeddings=query_embeddings,
                query_texts=query_texts,
                ids=ids,
                n_results=n_results,
                where=where,
                include=include,
            )
        elif ids:
            results = collection.get(
                ids=ids,
            )
        else:
            logger.error("query_embeddings, query_texts, or ids is required for query")
        return results

    def update(self, data: Dict) -> bool:
        """更新数据"""
        return self._upsert(data)

    def delete(self, data: Dict, recycle: bool = True) -> bool:
        """删除数据"""
        collection_name = data.get("collection_name", "")
        if not collection_name:
            logger.error("collection_name is required for delete")
            return False
        
        collection = self._ensure_collection(collection_name)
        if not collection:
            logger.error(f"Collection {collection_name} not found")
            return False
        
        ids = data.get("ids", [])
        if not ids:
            logger.error("ids is required for delete")
            return False
        
        try:
            chroma_results = collection.get(ids=ids, include=["documents", "metadatas", "embeddings"])
            logger.debug(f"query results: {chroma_results}")
            # 先将数据移动到回收站
            if chroma_results and recycle:
                chroma_results["collection_name"] = f"{collection_name}_recycle_bin"
                self._upsert(data=chroma_results)
            # 从原始集合中删除
            collection.delete(ids=ids)
            return True
        except Exception as e:
            logger.exception(f"Failed to delete documents: {e}")
            return False

    @lru_cache(maxsize=128)
    def _ensure_collection(self, collection_name: str) -> Optional[chromadb.Collection]:
        """确保集合存在"""
        collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine",
                      "context_type": collection_name},
        )
        self._collections[collection_name] = collection
        return collection

    def _upsert(self, data: Dict) -> bool:
        """
        向指定集合中插入或更新数据。
        
        :param collection_name: 集合名称
        :param data: 要插入或更新的数据
        :return: 是否成功
        """
        if not self._initialized:
            logger.error("ChromaDB backend not initialized")
            return False
        
        logger.debug(f"_upsert() data: {data}")
        
        collection_name = data.pop("collection_name", "")
        if not collection_name:
            logger.error("collection_name is required for insert")
            return False
        
        collection = self._ensure_collection(collection_name)
        if not collection:
            logger.error(f"Collection {collection_name} not found")
            return False
        
        ids = data.get("ids", [])
        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])
        embeddings = data.get("embeddings", None)
        if not ids or not documents or not metadatas or embeddings is None:
            logger.error("ids, documents, metadatas, embeddings are required for insert")
            return False
        
        if len(ids) != len(documents) != len(metadatas) != len(embeddings):
            logger.error("ids, documents, metadatas, embeddings must have the same length")
            return False
        
        try:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas,
                embeddings=embeddings,
            )
            return True
        except Exception as e:
            logger.exception(f"Insert operation failed: {e}")
            return False