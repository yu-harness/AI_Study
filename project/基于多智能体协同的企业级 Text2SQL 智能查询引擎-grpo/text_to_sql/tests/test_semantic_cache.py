import fnmatch
import unittest

from text_to_sql.cache.semantic_cache import SemanticCache


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


class FakeEmbedding:
    def encode(self, text, normalize_embeddings=True):
        text = text.lower()
        return [1.0 if "user" in text or "用户" in text else 0.0, 1.0]


class TestSemanticCache(unittest.TestCase):
    def test_set_and_get_with_score(self):
        cache = SemanticCache(FakeRedis(), embedding_model=FakeEmbedding(), threshold=0.5)
        cache.set("查询用户", "SELECT id FROM users", schema_version="v1")

        hit = cache.get_with_score("查询用户列表")
        self.assertEqual(hit["sql"], "SELECT id FROM users")
        self.assertEqual(hit["metadata"]["schema_version"], "v1")

    def test_miss_below_threshold(self):
        cache = SemanticCache(FakeRedis(), embedding_model=FakeEmbedding(), threshold=2.1)
        cache.set("查询用户", "SELECT id FROM users")
        self.assertIsNone(cache.get("查询用户"))

    def test_schema_version_mismatch_invalidates_cached_sql(self):
        cache = SemanticCache(FakeRedis(), embedding_model=FakeEmbedding(), threshold=0.5)
        cache.set("查询用户", "SELECT id FROM users", schema_version="v1")

        self.assertIsNone(cache.get("查询用户", schema_version="v2"))
        self.assertEqual(cache.get("查询用户", schema_version="v1"), "SELECT id FROM users")

    def test_namespaces_isolate_databases(self):
        redis = FakeRedis()
        orders = SemanticCache(redis, embedding_model=FakeEmbedding(), threshold=0.5, namespace="orders")
        users = SemanticCache(redis, embedding_model=FakeEmbedding(), threshold=0.5, namespace="users")
        orders.set("查询用户", "SELECT id FROM order_users")

        self.assertEqual(orders.get("查询用户"), "SELECT id FROM order_users")
        self.assertIsNone(users.get("查询用户"))

    def test_disabled_cache_does_not_read_or_write(self):
        redis = FakeRedis()
        cache = SemanticCache(redis, embedding_model=FakeEmbedding(), enabled=False)

        cache.set("查询用户", "SELECT id FROM users")

        self.assertEqual(redis.store, {})
        self.assertIsNone(cache.get("查询用户"))


if __name__ == "__main__":
    unittest.main()
