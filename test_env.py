import os
import sys

# 【终极防御】在导入 pymilvus 之前，强制清除环境变量
os.environ.pop('MILVUS_URI', None)

import torch
from transformers import AutoTokenizer
from sentence_transformers import SentenceTransformer
from pymilvus import MilvusClient

print("=" * 50)
print("环境检查")
print("=" * 50)

# 检查 CUDA
print(f"✓ PyTorch 版本: {torch.__version__}")
print(f"✓ CUDA 可用: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"✓ GPU 设备: {torch.cuda.get_device_name(0)}")
    print(f"✓ GPU 显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")

# 检查嵌入模型
try:
    model = SentenceTransformer('./models/embedding_model')
    test_text = "测试文本"
    embedding = model.encode(test_text)
    print(f"✓ 嵌入模型加载成功，向量维度: {len(embedding)}")
except Exception as e:
    print(f"✗ 嵌入模型加载失败: {e}")

# 检查 Milvus
try:
    os.makedirs("./data/vectors", exist_ok=True)
    # 【显式指定 uri 参数】
    client = MilvusClient(uri="./data/vectors/test.db")
    print("✓ Milvus Lite 初始化成功")
except Exception as e:
    print(f"✗ Milvus 初始化失败: {e}")
    # 打印详细的库版本信息，方便排查
    import pymilvus
    print(f"  (当前 pymilvus 版本: {pymilvus.__version__})")

print("=" * 50)
print("环境检查完成！")
print("=" * 50)
