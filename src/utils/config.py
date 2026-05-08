import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """系统配置类"""
    
    # 项目路径
    PROJECT_ROOT = Path(os.getenv('PROJECT_ROOT', '/root/autodl-tmp/cloud-ops-qa-system'))
    
    # 模型路径
    EMBEDDING_MODEL_PATH = PROJECT_ROOT / os.getenv('EMBEDDING_MODEL_PATH', 'models/embedding_model')
    LLM_MODEL_PATH = PROJECT_ROOT / os.getenv('LLM_MODEL_PATH', 'models/qwen2.5-7b-instruct')
    
    # Milvus 配置
    MILVUS_URI = str(PROJECT_ROOT / os.getenv('MILVUS_URI', 'data/vectors/milvus_lite.db'))
    
    # 数据路径
    RAW_DATA_DIR = PROJECT_ROOT / 'data/raw'
    PROCESSED_DATA_DIR = PROJECT_ROOT / 'data/processed'
    
    # 文本切片参数
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 50
    
    # 检索参数
    TOP_K = 5
    RRF_K = 60
    
    # 产品线配置
    PRODUCT_LINES = {
        'CEPH': 'Ceph分布式存储',
        'K8S': 'Kubernetes容器编排',
        'NETWORK': '网络设备',
        'DATABASE': '数据库服务'
    }
    
    @classmethod
    def ensure_dirs(cls):
        """确保所有必要目录存在"""
        for dir_path in [cls.RAW_DATA_DIR, cls.PROCESSED_DATA_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

# 初始化时创建目录
Config.ensure_dirs()
