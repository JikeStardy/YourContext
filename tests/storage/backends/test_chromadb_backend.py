
from pytest import fixture
import pytest
from yourcontext.consts.storage import StorageType
from yourcontext.storage.backends.chromadb_backend import ChromaDBBackend

import logging

from yourcontext.storage.backends import ChromaDBBackend

class TestChromaDBBackend:

    @fixture(autouse=True, scope="class", name="backend")
    def setup_chromadb_backend(self) -> ChromaDBBackend:
        backend = ChromaDBBackend()
        backend.initialize({})
        return backend

    @pytest.mark.run(order=1)
    def test_initialize(self, backend: ChromaDBBackend):
        backend = ChromaDBBackend()
        backend.initialize({})
        logging.debug(f"backend._initialized returns: {backend._initialized}")
        assert backend._initialized == True
    
    @pytest.mark.run(order=2)
    def test_get_name(self, backend: ChromaDBBackend):
        backend = ChromaDBBackend()
        backend.initialize({})
        logging.debug(f"backend.get_name() returns: {backend.get_name()}")
        assert backend.get_name() == "chromadb"
    
    @pytest.mark.run(order=3)
    def test_get_storage_type(self, backend: ChromaDBBackend):
        backend = ChromaDBBackend()
        backend.initialize({})
        logging.debug(f"backend.get_storage_type() returns: {backend.get_storage_type()}")
        assert backend.get_storage_type() == StorageType.VECTOR_DB

    @pytest.mark.run(order=4)
    def test_insert(self, backend: ChromaDBBackend):
        data = {
            "ids": ["id1", "id2"],
            "embeddings": [[1.1, 2.3, 3.2], [4.5, 6.9, 4.4]],
            "documents": ["doc1", "doc2"],
            "metadatas": [{"source": "src1"}, {"source": "src2"}],
            "collection_name": "test_collection",
        }
        assert backend.insert(data) == True

    @pytest.mark.run(order=5)
    def test_query(self, backend: ChromaDBBackend):
        data = {
            "query_embeddings": [[1.1, 2.3, 3.2]],
            "collection_name": "test_collection",
            "n_results": 1,
        }
        results = backend.query(data)
        logging.debug(f"backend.query() returns: {results}")
        
        assert results == {
            'ids': [['id1']], 
            'embeddings': None, 
            'documents': [['doc1']], 
            'uris': None, 
            'included': ['metadatas', 'documents', 'distances'], 
            'data': None, 
            'metadatas': [[{'source': 'src1'}]], 
            'distances': [[0.0]]
        }
        logging.debug(f"queried data is: {results}")

    @pytest.mark.run(order=6)
    def test_update(self, backend: ChromaDBBackend):
        data = {
            "ids": ["id1"],
            "embeddings": [[1.1, 2.3, 3.2]],
            "documents": ["doc1"],
            "metadatas": [{"source": "src1"}],
            "collection_name": "test_collection",
        }
        backend.insert(data.copy())
        data["metadatas"][0].update({"update_info": "this_record_is_upated!"})
        assert backend.update(data) == True
        logging.debug(f"updated data is: {backend.query(data)}")

    @pytest.mark.run(order=7)
    def test_delete(self, backend: ChromaDBBackend):
        data = {
            "ids": ["id1"],
            "collection_name": "test_collection",
        }
        assert backend.delete(data) == True
        data["collection_name"] = "test_collection_recycle_bin"
        logging.debug(f"recycle bin returns: {backend.query(data)}")

    @pytest.mark.run(order=9999)
    def test_delete_collection(self, backend: ChromaDBBackend):
        data = {
            "collection_name": "test_collection",
        }
        assert backend._client.delete_collection(name=data["collection_name"]) == None
