import yaml
from pymilvus import connections, utility

# 加载配置
with open("config/config.yaml", "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# 连接 Milvus
connections.connect(uri=config['milvus']['uri'])

# 获取所有 Collection
collections = utility.list_collections()
print(f"找到 {len(collections)} 个 Collection:")

for collection_name in collections:
    print(f"  删除: {collection_name}")
    utility.drop_collection(collection_name)

print("\n✓ 所有 Collection 已删除")

