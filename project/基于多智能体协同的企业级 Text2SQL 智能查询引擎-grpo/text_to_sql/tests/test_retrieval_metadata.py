import fnmatch
from pathlib import Path
from types import SimpleNamespace
import unittest

from text_to_sql.agents.planner_node import planner_node
from text_to_sql.main import Text2SQLSystem
from text_to_sql.metadata.collector import SchemaCollector
from text_to_sql.retrieval.business_kb import BusinessKnowledgeBase
from text_to_sql.retrieval.entity_linker import EntityLinker
from text_to_sql.retrieval.router import SemanticRouter
from text_to_sql.retrieval.schema_retriever import SchemaRetriever


class FakeRedis:
    def __init__(self):
        self.store = {}

    def set(self, key, value, *args, **kwargs):
        self.store[key] = value

    def get(self, key):
        if isinstance(key, bytes):
            key = key.decode("utf-8")
        return self.store.get(key)

    def scan_iter(self, pattern):
        for key in list(self.store):
            if fnmatch.fnmatch(key, pattern):
                yield key


class FakeElasticsearchIndices:
    def __init__(self, client):
        self.client = client

    def exists(self, index):
        return index in self.client.documents

    def delete(self, index):
        self.client.documents.pop(index, None)

    def create(self, index, body):
        self.client.documents[index] = []
        self.client.index_body = body

    def refresh(self, index):
        return None


class FakeElasticsearch:
    def __init__(self):
        self.documents = {}
        self.index_body = None
        self.indices = FakeElasticsearchIndices(self)

    def ping(self):
        return True

    def index(self, index, body):
        self.documents[index].append(body)

    def search(self, index, body):
        query = body["query"]["multi_match"]["query"]
        hits = []
        for document in self.documents[index]:
            if document["name"] in query or any(alias in query for alias in document["includes"]):
                hits.append({"_source": document})
        return {"hits": {"hits": hits[: body.get("size", 10)]}}


class FakeEmbedding:
    def encode(self, texts, normalize_embeddings=True):
        if isinstance(texts, list):
            return [self._vec(text) for text in texts]
        return self._vec(texts)

    @staticmethod
    def _vec(text):
        text = text.lower()
        return [
            1.0 if "user" in text or "用户" in text else 0.0,
            1.0 if "order" in text or "订单" in text else 0.0,
            1.0 if "amount" in text or "金额" in text else 0.0,
        ]


class FakeInspector:
    def get_table_names(self):
        return ["users", "orders"]

    def get_table_comment(self, table):
        return {"text": "用户表" if table == "users" else "订单表"}

    def get_columns(self, table):
        if table == "users":
            return [
                {"name": "id", "type": "INT", "comment": "用户 ID"},
                {"name": "name", "type": "VARCHAR", "comment": "用户名"},
            ]
        return [
            {"name": "id", "type": "INT", "comment": "订单 ID"},
            {"name": "user_id", "type": "INT", "comment": "用户 ID"},
            {"name": "amount", "type": "DECIMAL", "comment": "金额"},
        ]


class EnglishOnlyInspector:
    def get_table_names(self):
        return ["users", "orders", "products"]

    def get_table_comment(self, table):
        return {"text": ""}

    def get_pk_constraint(self, table):
        return {"constrained_columns": ["id"]}

    def get_foreign_keys(self, table):
        if table == "orders":
            return [{"constrained_columns": ["user_id"], "referred_table": "users", "referred_columns": ["id"]}]
        return []

    def get_columns(self, table):
        schemas = {
            "users": [
                {"name": "id", "type": "INTEGER", "comment": ""},
                {"name": "name", "type": "TEXT", "comment": ""},
                {"name": "city", "type": "TEXT", "comment": ""},
                {"name": "active", "type": "INTEGER", "comment": ""},
            ],
            "orders": [
                {"name": "id", "type": "INTEGER", "comment": ""},
                {"name": "user_id", "type": "INTEGER", "comment": ""},
                {"name": "amount", "type": "REAL", "comment": ""},
                {"name": "status", "type": "TEXT", "comment": ""},
                {"name": "created_at", "type": "TEXT", "comment": ""},
            ],
            "products": [
                {"name": "id", "type": "INTEGER", "comment": ""},
                {"name": "name", "type": "TEXT", "comment": ""},
                {"name": "category", "type": "TEXT", "comment": ""},
                {"name": "price", "type": "REAL", "comment": ""},
            ],
        }
        return schemas[table]


class FakePlannerLLM:
    def generate(self, prompts, sampling_params=None):
        text = '{"execution_plan": "scan selected schema"}'
        return [SimpleNamespace(outputs=[SimpleNamespace(text=text)])]


class RecordingSchemaRetriever:
    def __init__(self):
        self.table_top_k = None
        self.column_top_k = None

    def retrieve_tables(self, query, top_k=10):
        self.table_top_k = top_k
        return ["users"]

    def retrieve_columns(self, query, tables, top_k=20):
        self.column_top_k = top_k
        return ["users.name"]


class SimpleSchemaCollector:
    def __init__(self):
        self.max_hops = None
        self.max_tables = None

    def bloodline_completion(self, tables, max_hops=2, max_tables=None):
        self.max_hops = max_hops
        self.max_tables = max_tables
        return list(tables)

    def get_compressed_schema(self, tables, target_columns=None):
        return "Table users:\n  - id (INTEGER)\n  - name (TEXT)"


class RecordingBusinessKB:
    def __init__(self):
        self.top_k = None

    def search(self, query, rewritten_query=None, top_k=3):
        self.top_k = top_k
        return "none"


class EmptyEntityLinker:
    def lookup_values(self, query):
        return []


class ChainInspector:
    def get_table_names(self):
        return ["a", "b", "c", "d"]

    def get_foreign_keys(self, table):
        edges = {
            "a": [{"constrained_columns": ["b_id"], "referred_table": "b", "referred_columns": ["id"]}],
            "b": [{"constrained_columns": ["c_id"], "referred_table": "c", "referred_columns": ["id"]}],
            "c": [{"constrained_columns": ["d_id"], "referred_table": "d", "referred_columns": ["id"]}],
        }
        return edges.get(table, [])


class TestSchemaRetriever(unittest.TestCase):
    def test_retrieve_columns_returns_table_qualified_names(self):
        redis = FakeRedis()
        retriever = SchemaRetriever(redis, embedding_model=FakeEmbedding())
        retriever.build_index(FakeInspector())

        tables = retriever.retrieve_tables("查询用户", top_k=1)
        self.assertEqual(tables[0], "users")

        columns = retriever.retrieve_columns("查询订单金额", tables=["orders"], top_k=2)
        self.assertTrue(all(column.startswith("orders.") for column in columns))


    def test_chinese_query_matches_english_schema_aliases(self):
        redis = FakeRedis()
        retriever = SchemaRetriever(redis, embedding_model=FakeEmbedding())
        retriever.build_index(EnglishOnlyInspector())

        tables = retriever.retrieve_tables("查询用户姓名", top_k=1)
        columns = retriever.retrieve_columns("查询订单金额", tables=["orders"], top_k=1)

        self.assertEqual(tables, ["users"])
        self.assertEqual(columns, ["orders.amount"])


class TestPlannerRetrievalConfig(unittest.TestCase):
    def test_planner_uses_configured_retrieval_top_k(self):
        retriever = RecordingSchemaRetriever()
        business_kb = RecordingBusinessKB()
        schema_collector = SimpleSchemaCollector()

        planner_node(
            {
                "query": "查询用户",
                "dialect": "sqlite",
                "dialect_rules": [],
            },
            llm=FakePlannerLLM(),
            schema_collector=schema_collector,
            schema_retriever=retriever,
            business_kb=business_kb,
            entity_linker=EmptyEntityLinker(),
            table_top_k=2,
            column_top_k=4,
            business_kb_top_k=5,
            bloodline_max_hops=3,
            bloodline_max_tables=8,
        )

        self.assertEqual(retriever.table_top_k, 2)
        self.assertEqual(retriever.column_top_k, 4)
        self.assertEqual(business_kb.top_k, 5)
        self.assertEqual(schema_collector.max_hops, 3)
        self.assertEqual(schema_collector.max_tables, 8)


class TestEntityMappingLoad(unittest.TestCase):
    def test_loads_mapping_files_from_business_knowledge(self):
        system = Text2SQLSystem.__new__(Text2SQLSystem)
        system.config = {"paths": {"business_knowledge": "./business_knowledge"}}
        system.config_dir = Path("text_to_sql").resolve()

        mappings = system._load_entity_mappings()

        self.assertTrue(any(mapping.get("dimension") == "region" for mapping in mappings))
        self.assertTrue(any(mapping.get("dimension") == "category" for mapping in mappings))
        self.assertTrue(any(mapping.get("dimension") == "order_status" for mapping in mappings))


class TestEntityLinker(unittest.TestCase):
    def test_mapping_can_target_actual_column(self):
        linker = EntityLinker(FakeElasticsearch())
        linker.build_index(
            [
                {
                    "dimension": "order_status",
                    "column": "orders.status",
                    "values": [
                        {
                            "name": "已支付",
                            "codes": ["paid"],
                            "includes": ["支付成功"],
                        }
                    ],
                }
            ]
        )

        self.assertEqual(linker.lookup_values("统计支付成功订单"), ["已支付 -> orders.status IN ('paid')"])

    def test_mapping_accepts_display_and_code_fields(self):
        linker = EntityLinker(FakeElasticsearch())
        linker.build_index(
            [
                {
                    "dimension": "channel",
                    "column": "orders.channel",
                    "values": [
                        {
                            "display": "APP",
                            "code": "app",
                            "includes": ["mobile app"],
                        }
                    ],
                }
            ]
        )

        self.assertEqual(linker.lookup_values("orders from mobile app"), ["APP -> orders.channel IN ('app')"])


class TestBusinessKnowledgeRetrieval(unittest.TestCase):
    def test_vector_results_below_min_score_are_filtered(self):
        redis = FakeRedis()
        kb = BusinessKnowledgeBase(redis, embedding_model=FakeEmbedding(), min_score=0.9)
        redis.set("kb:business:orders", '{"id": "orders", "definition": "订单口径"}')
        redis.set("kb:vec:orders", "[0.0, 1.0, 0.0]")

        result = kb.search("查询用户", top_k=1)

        self.assertEqual(result, "无相关业务知识")

    def test_paid_order_metric_is_recalled_by_keyword_supplement(self):
        redis = FakeRedis()
        kb = BusinessKnowledgeBase(
            redis,
            kb_path=str(Path("text_to_sql/business_knowledge").resolve()),
            embedding_model=FakeEmbedding(),
            min_score=0.9,
        )
        kb.build_index()

        result = kb.search("统计每个地区已支付订单数量", top_k=1)

        self.assertIn("orders.status = 'paid'", result)
        self.assertIn("orders.region", result)

    def test_vector_results_are_primary_and_keyword_results_supplement_them(self):
        redis = FakeRedis()
        kb = BusinessKnowledgeBase(redis, embedding_model=FakeEmbedding(), min_score=0.1)
        redis.set("kb:business:vector", '{"id": "vector", "definition": "向量命中"}')
        redis.set("kb:vec:vector", "[0.0, 1.0, 1.0]")
        redis.set(
            "kb:business:keyword",
            '{"id": "keyword", "definition": "关键词补充", "keywords": ["用户"]}',
        )

        result = kb.search("用户订单金额", top_k=1)

        self.assertLess(result.index("向量命中"), result.index("关键词补充"))


class TestSemanticRouter(unittest.TestCase):
    def test_routes_with_local_descriptor_embeddings_without_faiss(self):
        router = SemanticRouter(
            None,
            FakeRedis(),
            descriptors=[
                {
                    "db_id": "user_db",
                    "domain": "用户",
                    "engine": "sqlite",
                    "tables": ["users"],
                    "keywords": ["用户"],
                },
                {
                    "db_id": "order_db",
                    "domain": "订单",
                    "engine": "postgresql",
                    "tables": ["orders"],
                    "keywords": ["订单", "金额"],
                },
            ],
            embedding_model=FakeEmbedding(),
        )

        result = router.route("查询订单金额")

        self.assertEqual(result["target_db"], "order_db")
        self.assertEqual(result["dialect"], "postgresql")


class TestSchemaCollectorCompression(unittest.TestCase):
    def test_bloodline_completion_is_ordered_and_limited(self):
        collector = SchemaCollector.__new__(SchemaCollector)
        collector.inspector = ChainInspector()
        collector.max_bloodline_tables = None

        expanded = collector.bloodline_completion(["b", "a"], max_hops=2, max_tables=3)

        self.assertEqual(expanded, ["b", "a", "c"])

    def test_compress_keeps_only_target_and_relationship_columns(self):
        collector = SchemaCollector.__new__(SchemaCollector)
        schema = {
            "table": "orders",
            "comment": "订单表",
            "columns": [
                {"name": "id", "type": "INT"},
                {"name": "user_id", "type": "INT"},
                {"name": "status", "type": "VARCHAR"},
                {"name": "category", "type": "VARCHAR"},
                {"name": "active", "type": "INT"},
                {"name": "name", "type": "VARCHAR"},
                {"name": "amount", "type": "DECIMAL"},
                {"name": "created_at", "type": "DATETIME"},
                {"name": "internal_note", "type": "VARCHAR"},
            ],
            "primary_keys": ["id"],
            "foreign_keys": [
                {"column": ["user_id"], "referred_table": "users", "referred_columns": ["id"]}
            ],
        }

        compressed = collector._compress_ddl("", schema, target_columns=["orders.status"])
        self.assertIn("status", compressed)
        self.assertIn("FK -> users.id", compressed)
        self.assertNotIn("category", compressed)
        self.assertNotIn("active", compressed)
        self.assertNotIn("name", compressed)
        self.assertNotIn("amount", compressed)
        self.assertNotIn("created_at", compressed)
        self.assertNotIn("internal_note", compressed)

    def test_compression_cache_key_includes_target_columns(self):
        collector = SchemaCollector.__new__(SchemaCollector)
        collector.prefix = "schema:compression:"
        collector.schema_version = "v1"
        schema = {
            "table": "orders",
            "columns": [
                {"name": "id", "type": "INT"},
                {"name": "amount", "type": "DECIMAL"},
                {"name": "status", "type": "VARCHAR"},
            ],
            "primary_keys": ["id"],
            "foreign_keys": [],
        }
        redis = FakeRedis()
        collector.redis = redis

        collector._cache_schema("orders", schema, ["amount"])
        collector._cache_schema("orders", schema, ["status"])

        self.assertEqual(len(redis.store), 2)
        self.assertNotEqual(
            collector._compression_key("orders", ["amount"]),
            collector._compression_key("orders", ["status"]),
        )

    def test_compression_cache_key_includes_schema_version(self):
        collector = SchemaCollector.__new__(SchemaCollector)
        collector.prefix = "schema:compression:"

        collector.schema_version = "v1"
        first = collector._compression_key("orders", ["amount"])
        collector.schema_version = "v2"
        second = collector._compression_key("orders", ["amount"])

        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
