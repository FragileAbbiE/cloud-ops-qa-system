import os
import yaml
import hashlib
from pathlib import Path
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    DirectoryLoader,
    UnstructuredMarkdownLoader,
    PyPDFLoader,
    Docx2txtLoader,
)
from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility

# 产品线中英文映射
PRODUCT_LINE_MAP = {
    "未分类": "Uncategorized",
    "K8s_Container": "K8s_Container",
    "Ansible_Automation": "Ansible_Automation",
    "MySQL_Database": "MySQL_Database",
    "Redis_Cache": "Redis_Cache",
    "Nginx_Gateway": "Nginx_Gateway",
    "Prometheus_Monitor": "Prometheus_Monitor",
    "Ceph_Storage": "Ceph_Storage",
    "Istio_ServiceMesh": "Istio_ServiceMesh",
    "KVM_Virtualization": "KVM_Virtualization",
    "Kafka_MQ": "Kafka_MQ"
}

def sanitize_collection_name(name: str) -> str:
    """将产品线名转换为合法的 Milvus 集合名"""
    if name in PRODUCT_LINE_MAP:
        return PRODUCT_LINE_MAP[name]
    
    safe_name = name.replace("/", "_").replace("-", "_").replace(" ", "_")
    safe_name = ''.join(c for c in safe_name if c.isalnum() or c == '_')
    return safe_name if safe_name else "Uncategorized"

# 加载配置
with open("config/config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# 初始化嵌入模型
print(f"加载嵌入模型: {config['embedding']['model_name']}")
embed_model = SentenceTransformer(
    config['embedding']['model_name'],
    device=config['embedding']['device']
)

# 🔥 动态获取向量维度
VECTOR_DIM = embed_model.get_sentence_embedding_dimension()
print(f"向量维度: {VECTOR_DIM}")

# 连接 Milvus
connections.connect(uri=config['milvus']['uri'])

def create_collection(product_line: str):
    """为每个产品线创建独立的 Collection"""
    safe_name = sanitize_collection_name(product_line)
    collection_name = f"{config['milvus']['collection_prefix']}_{safe_name}"

    if utility.has_collection(collection_name):
        print(f"  Collection {collection_name} 已存在，跳过创建")
        return Collection(collection_name)

    # 定义 Schema（使用动态维度）
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM),  # 🔥 动态维度
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=4096),
        FieldSchema(name="product_line", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="component", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="doc_type", dtype=DataType.VARCHAR, max_length=64),
        FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=256),
    ]

    schema = CollectionSchema(fields, description=f"{product_line} 运维知识库")
    collection = Collection(collection_name, schema)

    # 创建索引（IVF_FLAT）
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "params": {"nlist": 128}
    }
    collection.create_index("vector", index_params)
    print(f"  ✓ 创建 Collection: {collection_name}")
    return collection

def extract_metadata_from_path(file_path: str) -> Dict[str, str]:
    """从文件路径中提取元数据"""
    path = Path(file_path)
    parts = path.parts
    
    metadata = {
        "product_line": "未分类",
        "component": "通用",
        "doc_type": "操作手册"
    }
    
    # 从路径中提取产品线（假设结构是 data/raw/产品线/文件.md）
    if len(parts) >= 3:
        # 尝试从倒数第二个目录获取产品线
        potential_product = parts[-2]
        if potential_product != "raw":
            metadata["product_line"] = potential_product
    
    # 从文件名提取信息
    filename = path.stem
    
    # 识别组件
    component_keywords = {
        "OSD": "OSD", "MON": "MON", "Pod": "Pod",
        "网络": "Network", "Network": "Network",
        "MySQL": "MySQL", "mysql": "MySQL",
        "Redis": "Redis", "redis": "Redis",
        "Nginx": "Nginx", "nginx": "Nginx",
        "Ansible": "Ansible", "ansible": "Ansible",
        "Prometheus": "Prometheus", "prometheus": "Prometheus"
    }
    
    for keyword, component in component_keywords.items():
        if keyword in filename:
            metadata["component"] = component
            break
    
    # 识别文档类型
    doc_type_keywords = {
        ("故障", "排查", "troubleshoot"): "故障排障",
        ("配置", "config"): "配置指南",
        ("部署", "deploy"): "部署指南",
        ("命令", "command"): "命令参考",
        ("优化", "optimize"): "性能优化"
    }
    
    for keywords, doc_type in doc_type_keywords.items():
        if any(kw in filename.lower() for kw in keywords):
            metadata["doc_type"] = doc_type
            break
    
    return metadata


def load_all_documents(raw_dir: str) -> list:
    """加载多格式运维文档(Markdown、PDF、Word)"""
    all_documents = []

    loaders = [
        ("Markdown", "**/*.md", UnstructuredMarkdownLoader),
        ("PDF", "**/*.pdf", PyPDFLoader),
        ("Word", "**/*.docx", Docx2txtLoader),
    ]

    for name, pattern, cls in loaders:
        try:
            loader = DirectoryLoader(
                raw_dir,
                glob=pattern,
                loader_cls=cls,
                show_progress=True,
                silent_errors=True,
            )
            docs = loader.load()
            print(f"  ✓ {name} 文件: {len(docs)} 个")
            all_documents.extend(docs)
        except Exception as e:
            print(f" {name} 加载失败: {e}")

    return all_documents


def load_all_documents_strict(raw_dir: str):
    """稳定版：手动遍历加载 md/pdf/docx"""
    from pathlib import Path
    all_docs = []

    patterns = [
        ("Markdown", "*.md", UnstructuredMarkdownLoader),
        ("PDF", "*.pdf", PyPDFLoader),
        ("Word", "*.docx", Docx2txtLoader),
    ]

    root = Path(raw_dir)
    for name, pat, loader_cls in patterns:
        files = list(root.rglob(pat))
        loaded = 0
        for fp in files:
            try:
                docs = loader_cls(str(fp)).load()
                all_docs.extend(docs)
                loaded += len(docs)
            except Exception as e:
                print(f"  ⚠ {name} 解析失败: {fp} -> {e}")
        print(f"  ✓ {name} 文件: {len(files)} 个，加载文档: {loaded} 个")

    return all_docs

def process_documents():
    """处理所有 Markdown 文档"""
    raw_dir = config['data']['raw_dir']

    # 加载所有 Markdown 文件
    print(f"\n从 {raw_dir} 加载多格式文档...")
    
    documents = load_all_documents_strict(raw_dir)
    print(f"✓ 加载了 {len(documents)} 个文档")

    if len(documents) == 0:
        print("⚠️  未找到任何文档，请检查 data/raw 目录")
        return

    # 文本切片
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=config['data']['chunk_size'],
        chunk_overlap=config['data']['chunk_overlap'],
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)
    print(f"✓ 切分为 {len(chunks)} 个文本块\n")

    # 按产品线分组
    product_collections = {}
    product_stats = {}

    for i, chunk in enumerate(chunks):
        # 提取元数据
        metadata = extract_metadata_from_path(chunk.metadata['source'])
        product_line = metadata['product_line']

        # 创建或获取对应的 Collection
        if product_line not in product_collections:
            print(f"\n处理产品线: {product_line}")
            product_collections[product_line] = create_collection(product_line)
            product_stats[product_line] = 0

        # 生成唯一 ID
        chunk_id = hashlib.md5(
            (chunk.page_content + chunk.metadata['source'] + str(i)).encode()
        ).hexdigest()[:32]

        # 向量化
        vector = embed_model.encode(chunk.page_content).tolist()
        
        # 🔥 验证向量维度
        if len(vector) != VECTOR_DIM:
            print(f"  ⚠️  向量维度不匹配: 期望 {VECTOR_DIM}, 实际 {len(vector)}")
            continue

        # 准备插入数据（Milvus 需要列表的列表格式）
        data = [
            [chunk_id],
            [vector],
            [chunk.page_content[:4096]],
            [metadata['product_line']],
            [metadata['component']],
            [metadata['doc_type']],
            [Path(chunk.metadata['source']).name]
        ]

        # 插入到对应的 Collection
        try:
            product_collections[product_line].insert(data)
            product_stats[product_line] += 1
        except Exception as e:
            print(f"  ✗ 插入失败 (chunk {i}): {e}")
            print(f"    文件: {chunk.metadata['source']}")
            print(f"    向量维度: {len(vector)}")
            continue

        # 每 50 个文本块显示一次进度
        if (i + 1) % 50 == 0:
            print(f"  进度: {i + 1}/{len(chunks)}")

    # 刷新所有 Collection
    print("\n正在刷新 Collections...")
    for product_line, collection in product_collections.items():
        collection.flush()
        collection.load()
        print(f"  ✓ {product_line}: {product_stats[product_line]} 个文本块")

    print(f"\n{'='*60}")
    print(f"✓ 数据入库完成！")
    print(f"{'='*60}")
    print(f"总文档数: {len(documents)}")
    print(f"总文本块: {len(chunks)}")
    print(f"成功入库: {sum(product_stats.values())} 块")
    print(f"产品线数: {len(product_collections)}")
    print(f"向量维度: {VECTOR_DIM}")
    print(f"\n产品线分布:")
    for product_line, count in sorted(product_stats.items(), key=lambda x: x[1], reverse=True):
        safe_name = sanitize_collection_name(product_line)
        print(f"  - {product_line:20s} ({safe_name:20s}): {count:4d} 块")

if __name__ == "__main__":
    try:
        process_documents()
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        import traceback
        traceback.print_exc()

