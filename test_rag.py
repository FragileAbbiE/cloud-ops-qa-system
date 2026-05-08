from src.retriever import MRAGRetriever
from src.generator import AnswerGenerator

# 初始化
print("正在加载检索器...")
retriever = MRAGRetriever()

print("正在加载生成器（大模型）...")
generator = AnswerGenerator()

# 测试问题
query = "Kubernetes Pod 一直 Pending 怎么办？"
print(f"\n问题: {query}\n")

# 检索
print("正在检索相关文档...")
docs = retriever.retrieve(query, top_k=3)
print(f"✓ 检索到 {len(docs)} 条相关文档\n")

# 生成答案
print("正在生成答案...\n")
answer = generator.generate(query, docs)
print("=" * 60)
print("答案:")
print("=" * 60)
print(answer)
