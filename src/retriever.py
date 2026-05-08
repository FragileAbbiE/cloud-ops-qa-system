"""
M-RAG 多分区检索引擎
实现双层索引架构：意图路由层 + 分区检索层
"""

import yaml
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, utility, CollectionSchema, FieldSchema, DataType, utility, CollectionSchema, FieldSchema, DataType
from rank_bm25 import BM25Okapi
import jieba
import numpy as np

class MRAGRetriever:
    """M-RAG 检索器：基于元数据的多分区检索策略"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化检索器"""
        # 加载配置
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # 连接 Milvus
        connections.connect(uri=self.config['milvus']['uri'])

        # 加载嵌入模型
        print(f"加载嵌入模型: {self.config['embedding']['model_name']}")
        self.embed_model = SentenceTransformer(
            self.config['embedding']['model_name'],
            device=self.config['embedding']['device']
        )

        # 产品线映射（用于意图识别）
        self.product_line_keywords = {
            "K8s_Container": ["k8s", "kubernetes", "pod", "容器", "deployment", "service"],
            "MySQL_Database": ["mysql", "数据库", "sql", "innodb", "主从"],
            "Nginx_Gateway": ["nginx", "网关", "反向代理", "负载均衡"],
            "Ceph_Storage": ["ceph", "存储", "osd", "mon", "分布式存储"],
            "Ansible_Automation": ["ansible", "自动化", "playbook"],
            "Istio_ServiceMesh": ["istio", "服务网格", "envoy"],
            "KVM_Virtualization": ["kvm", "虚拟化", "虚拟机"],
            "Kafka_MQ": ["kafka", "消息队列", "mq"],
            "Prometheus_Monitor": ["prometheus", "监控", "告警"],
            "Redis_Cache": ["redis", "缓存", "内存数据库"]
        }

        self.index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 128}
        }
        self.search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }

        # 加载所有 Collection
        self.collections = self._load_collections()
        self.bm25_indexes = self._build_bm25_indexes()
        print(f"✓ 加载了 {len(self.collections)} 个产品线分区")


    def _create_collection_if_not_exists(self, collection_name: str):
        """当分区集合不存在时自动创建空集合（保证系统可启动）"""
        if utility.has_collection(collection_name):
            return

        # 通过嵌入模型动态确定向量维度
        dim = len(self.embed_model.encode("测试维度"))

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim),
            FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=8192),
            FieldSchema(name="product_line", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="component", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=512),
        ]
        schema = CollectionSchema(fields=fields, description=f"{collection_name} auto-created")
        Collection(name=collection_name, schema=schema)

    def _ensure_vector_index(self, collection: Collection):
        """确保 vector 字段存在 IVF_FLAT 索引"""
        has_index = False
        for idx in collection.indexes:
            try:
                if getattr(idx, "field_name", "") == "vector":
                    has_index = True
                    break
            except Exception:
                pass

        if not has_index:
            collection.create_index(field_name="vector", index_params=self.index_params)

    def _load_collections(self) -> Dict[str, Collection]:
        """加载所有产品线的 Collection；不存在则自动创建，并确保索引存在"""
        collections = {}
        prefix = self.config['milvus']['collection_prefix']

        for product_line in self.product_line_keywords.keys():
            collection_name = f"{prefix}_{product_line}"
            try:
                # 不存在则创建空集合
                self._create_collection_if_not_exists(collection_name)

                collection = Collection(collection_name)

                # 确保索引存在（IVF_FLAT）
                self._ensure_vector_index(collection)

                collection.load()
                collections[product_line] = collection
            except Exception as e:
                print(f"⚠️  无法加载/创建 {collection_name}: {e}")

        return collections


    def _build_bm25_indexes(self):
        """预构建每个分区 BM25 索引，避免每次查询重建。"""
        indexes = {}
        for product_line, collection in self.collections.items():
            try:
                rows = collection.query(
                    expr="text != \"\"",
                    output_fields=["text", "product_line", "component", "doc_type", "source_file"],
                    limit=16384
                )
            except Exception:
                rows = []
            if rows:
                corpus = [list(jieba.cut(r.get("text", ""))) for r in rows]
                indexes[product_line] = {
                    "bm25": BM25Okapi(corpus),
                    "docs": rows
                }
                print(f"  ✓ {product_line} BM25 索引构建完成 ({len(rows)} 文档)")
        return indexes

    def _identify_intent(self, query: str):
        """
        识别查询意图，返回[(product_line, confidence), ...]
        明确产品线：返回 Top-1
        不明确：返回 Top-3
        """
        query_lower = query.lower()
        scores = {}

        for product_line, keywords in self.product_line_keywords.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[product_line] = score

        if not scores:
            return [(pl, 0.1) for pl in self.product_line_keywords.keys()]

        max_score = max(scores.values())
        normalized = [(pl, sc / max_score) for pl, sc in scores.items()]
        sorted_scores = sorted(normalized, key=lambda x: x[1], reverse=True)

        if len(sorted_scores) == 1:
            print("[意图识别] 明确产品线，锁定 Top-1 分区")
            return sorted_scores[:1]

        top1_score = sorted_scores[0][1]
        top2_score = sorted_scores[1][1]

        if top1_score == 1.0 and (top1_score - top2_score) >= 0.5:
            print("[意图识别] 明确产品线，锁定 Top-1 分区")
            return sorted_scores[:1]
        else:
            print("[意图识别] 产品线不明确，锁定 Top-3 分区")
            return sorted_scores[:3]

    def _vector_search(self, query: str, collection: Collection, top_k: int = 10) -> List[Dict]:
        """向量检索（语义匹配）"""
        # 查询向量化
        query_vector = self.embed_model.encode(query).tolist()

        # 执行检索
        search_params = self.search_params

        results = collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=top_k,
            output_fields=["text", "product_line", "component", "doc_type", "source_file"]
        )

        # 格式化结果
        candidates = []
        for hit in results[0]:
            candidates.append({
                "text": hit.entity.get("text"),
                "score": hit.distance,
                "product_line": hit.entity.get("product_line"),
                "component": hit.entity.get("component"),
                "doc_type": hit.entity.get("doc_type"),
                "source_file": hit.entity.get("source_file"),
                "method": "vector"
            })

        return candidates

    def _bm25_search(self, query: str, product_line: str, top_k: int = 10):
        """BM25 检索（使用预构建索引）"""
        if product_line not in self.bm25_indexes:
            return []

        bm25_obj = self.bm25_indexes[product_line]["bm25"]
        docs = self.bm25_indexes[product_line]["docs"]

        query_tokens = list(jieba.cut(query))
        scores = bm25_obj.get_scores(query_tokens)
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            d = docs[int(idx)]
            results.append({
                "text": d.get("text", ""),
                "score": float(scores[int(idx)]),
                "product_line": d.get("product_line", product_line),
                "component": d.get("component", ""),
                "doc_type": d.get("doc_type", ""),
                "source_file": d.get("source_file", ""),
                "method": "bm25",
            })
        return results

    def _rrf_fusion(self, vector_results: List[Dict], bm25_results: List[Dict], k: int = 60) -> List[Dict]:
        """
        RRF (Reciprocal Rank Fusion) 结果融合
        公式: RRF(d) = Σ 1/(k + rank(d))
        """
        # 构建文档到排名的映射
        doc_scores = {}

        # 向量检索结果
        for rank, doc in enumerate(vector_results, start=1):
            doc_key = doc["text"][:100]  # 用文本前100字符作为唯一标识
            if doc_key not in doc_scores:
                doc_scores[doc_key] = {"doc": doc, "score": 0}
            doc_scores[doc_key]["score"] += 1 / (k + rank)

        # BM25 检索结果
        for rank, doc in enumerate(bm25_results, start=1):
            doc_key = doc["text"][:100]
            if doc_key not in doc_scores:
                doc_scores[doc_key] = {"doc": doc, "score": 0}
            doc_scores[doc_key]["score"] += 1 / (k + rank)

        # 按融合分数排序
        sorted_docs = sorted(doc_scores.values(), key=lambda x: x["score"], reverse=True)

        # 返回 Top-5
        return [item["doc"] for item in sorted_docs[:5]]

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        M-RAG 检索主流程

        Args:
            query: 用户查询
            top_k: 返回结果数量

        Returns:
            检索到的文档列表
        """
        print(f"\n{'='*60}")
        print(f"查询: {query}")
        print(f"{'='*60}")

        # 第一层：意图识别与路由
        intent_results = self._identify_intent(query)
        print(f"\n[意图识别] 锁定产品线:")
        for product_line, confidence in intent_results:
            print(f"  - {product_line}: {confidence:.2f}")

        # 第二层：分区内混合检索
        all_candidates = []

        for product_line, confidence in intent_results:
            if confidence < 0.3:  # 置信度过低，跳过
                continue

            collection = self.collections.get(product_line)
            if not collection:
                continue

            print(f"\n[分区检索] {product_line}")

            # 并行执行向量检索和 BM25 检索
            vector_results = self._vector_search(query, collection, top_k=10)
            bm25_results = self._bm25_search(query, product_line, top_k=10)

            print(f"  - 向量检索: {len(vector_results)} 个候选")
            print(f"  - BM25 检索: {len(bm25_results)} 个候选")

            # RRF 融合
            fused_results = self._rrf_fusion(vector_results, bm25_results)
            all_candidates.extend(fused_results)

        # 全局去重并返回 Top-K
        unique_docs = []
        seen_texts = set()

        for doc in all_candidates:
            text_key = doc["text"][:100]
            if text_key not in seen_texts:
                seen_texts.add(text_key)
                unique_docs.append(doc)

        final_results = unique_docs[:top_k]

        print(f"\n[最终结果] 返回 {len(final_results)} 个文档")
        print(f"{'='*60}\n")

        return final_results


# 测试代码
if __name__ == "__main__":
    retriever = MRAGRetriever()

    # 测试查询
    test_queries = [
        "Kubernetes Pod 一直处于 Pending 状态怎么办？",
        "MySQL 主从复制延迟如何排查？",
        "Nginx 502 错误如何解决？"
    ]

    for query in test_queries:
        results = retriever.retrieve(query)

        print(f"查询: {query}")
        print(f"检索到 {len(results)} 个相关文档:\n")

        for i, doc in enumerate(results, 1):
            print(f"{i}. [{doc['product_line']}] {doc['component']}")
            print(f"   文档类型: {doc['doc_type']}")
            print(f"   来源: {doc['source_file']}")
            print(f"   内容预览: {doc['text'][:100]}...")
            print()
