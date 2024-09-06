from docuverse.engines.retrieval.milvus.milvus import MilvusEngine

try:
    from pymilvus import (
        FieldSchema, CollectionSchema, DataType, MilvusClient,
        Collection,
    )
    from pymilvus import model as MilvusModel
    from pymilvus.model.sparse.bm25.tokenizers import build_default_analyzer
    from milvus_model.sparse.bm25 import BM25EmbeddingFunction
except:
    print(f"You need to install pymilvus to be using Milvus functionality!")
    raise RuntimeError("fYou need to install pymilvus to be using Milvus functionality!")
from docuverse.engines.search_engine_config_params import SearchEngineConfig
from docuverse.utils import get_param

from docuverse.utils.embeddings.sparse_embedding_function import SparseEmbeddingFunction

class MilvusBM25Engine(MilvusEngine):
    def __init__(self, config: SearchEngineConfig|dict, **kwargs) -> None:
        super().__init__(config, **kwargs)
        self.analyzer = build_default_analyzer(get_param(kwargs, 'language', "en"))
        self.bm25_ef = BM25EmbeddingFunction(self.analyzer)

    def init_model(self, kwargs):
        pass
        # self.model =

    def prepare_index_params(self):
        index_params = self.client.prepare_index_params()
        index_params.add_index(
            field_name="_id",
            index_type="STL_SORT"
        )
        index_params.add_index(field_name="embeddings",
                               index_name="sparse_inverted_index",
                               index_type="SPARSE_INVERTED_INDEX",
                               metric_type="IP",
                               params={"drop_ratio_build": 0.2})
        return index_params

    def create_fields(self):
        fields = super().create_fields()
        fields.append(
            FieldSchema(name="embeddings", dtype=DataType.SPARSE_FLOAT_VECTOR)
        )
        return fields

    def get_search_params(self):
        search_params = get_param(self.config, 'search_params',
                                  self.milvus_defaults['search_params']["BM25"])

        return search_params

    def encode_data(self, texts, batch_size):
        self.bm25_ef.fit(texts)
        embeddings = self.bm25_ef.encode_documents(texts)
        return list(embeddings)

    def encode_query(self, question):
        return self.bm25_ef.encode_query(question.text)

    @classmethod
    def test(cls):
        collection_name = "hello_sparse"
        docs = [
            "Artificial intelligence was founded as an academic discipline in 1956.",
            "Alan Turing was the first person to conduct substantial research in AI.",
            "Born in Maida Vale, London, Turing was raised in southern England.",
            "The quick setup collection has two mandatory fields: the primary and vector fields. "
            "It also allows the insertion of undefined fields and their values in key-value pairs in a dynamic field."
        ]
        queries = ["Who is Alan Turing?", "What is quick setup?"]

        splade_enc, milvus_client = cls.setup(collection_name)
        cls.encode_and_index(collection_name, splade_enc, milvus_client, docs)
        cls.query(collection_name, splade_enc, milvus_client, queries)
        milvus_client.drop_collection(collection_name)

