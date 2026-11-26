"""
Value-level entity linker for mapping business terms to database codes.
"""

from typing import List


class EntityLinker:
    """Lookup value mappings from the required Elasticsearch entity index."""

    def __init__(
        self,
        es_client,
        index_name: str = "text2sql_entity_index",
        analyzer: str = "ik_max_word",
    ):
        if es_client is None:
            raise ValueError("EntityLinker requires an Elasticsearch client")
        self.es = es_client
        self.index_name = index_name
        self.analyzer = analyzer

    def build_index(self, mappings: List[dict]):
        self._build_es_index(mappings)

    def _build_es_index(self, mappings: List[dict]):
        index_body = {
            "mappings": {
                "properties": {
                    "dimension": {"type": "keyword"},
                    "name": {
                        "type": "text",
                        "analyzer": self.analyzer,
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "includes": {"type": "text", "analyzer": self.analyzer},
                    "codes": {"type": "keyword"},
                    "column": {"type": "keyword"},
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            },
        }

        if self.es.indices.exists(index=self.index_name):
            self.es.indices.delete(index=self.index_name)
        self.es.indices.create(index=self.index_name, body=index_body)

        for mapping in mappings:
            dimension = mapping["dimension"]
            column = mapping.get("column")
            for value in mapping["values"]:
                normalized = self._normalize_mapping_value(value)
                if not normalized:
                    raise ValueError(f"Invalid entity mapping value in dimension {dimension}: {value}")
                self.es.index(
                    index=self.index_name,
                    body={
                        "dimension": dimension,
                        "name": normalized["name"],
                        "includes": normalized["includes"],
                        "codes": normalized["codes"],
                        "column": value.get("column", column),
                    },
                )
        self.es.indices.refresh(index=self.index_name)

    def lookup_values(self, query: str) -> List[str]:
        return self._lookup_es(query)

    def _lookup_es(self, query: str) -> List[str]:
        response = self.es.search(
            index=self.index_name,
            body={
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["name^3", "includes"],
                    }
                },
                "size": 10,
            },
        )

        mappings = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            mappings.append(
                self._format_mapping(
                    source["name"],
                    source["dimension"],
                    source["codes"],
                    source.get("column"),
                )
            )
        return mappings

    def ping(self) -> bool:
        return bool(self.es.ping())

    @staticmethod
    def _format_mapping(name: str, dimension: str, codes: List[str], column: str = None) -> str:
        quoted_codes = ",".join(f"'{code}'" for code in codes)
        target_column = column or f"{dimension}_id"
        return f"{name} -> {target_column} IN ({quoted_codes})"

    @staticmethod
    def _normalize_mapping_value(value: dict):
        name = value.get("name") or value.get("display")
        raw_codes = value.get("codes", value.get("code"))
        if not name or raw_codes is None:
            return None

        if isinstance(raw_codes, list):
            codes = raw_codes
        else:
            codes = [raw_codes]

        includes = value.get("includes", [])
        if isinstance(includes, str):
            includes = [includes]

        return {
            "name": str(name),
            "codes": [str(code) for code in codes],
            "includes": [str(include) for include in includes],
        }
