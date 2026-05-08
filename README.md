# 云运维智能问答系统（Cloud Ops QA System）

本科毕业设计项目：面向云运维场景的智能问答系统，基于 RAG（检索增强生成）实现知识问答、来源溯源与审计记录。

## 1. 项目简介

本系统采用**混合数据库架构**：

- **SQLite（关系型）**：存储用户、会话、审计日志等结构化数据
- **Milvus（向量库）**：存储知识库文本向量与元数据，支持语义检索

系统支持：

- 用户登录与权限管理（`admin` / `engineer`）
- 文档知识库构建与检索
- 智能问答与答案来源溯源
- 问答操作审计日志记录与查询

## 2. 技术栈

- Python 3.x
- Streamlit（Web 交互）
- SQLite
- Milvus / Milvus Lite
- 向量模型：BGE-small-zh-v1.5（维度 512）

## 3. 项目结构
cloud-ops-qa-system/
├── pages/ # 页面模块（问答、文档管理等）
├── utils/ # 工具模块（鉴权、数据库、日志等）
├── src/ # 核心业务代码（如有）
├── scripts/ # 数据处理/初始化脚本
├── config/ # 配置文件
├── data/ # 本地数据（按提交策略可仅保留样例）
├── requirements.txt # 依赖列表
├── README.md
└── 云运维问答.py # 主入口（按实际文件名）

## 4. 环境准备

```bash
# 1) 进入项目
cd cloud-ops-qa-system

# 2) 创建并激活虚拟环境（可选）
python -m venv venv
source venv/bin/activate

# 3) 安装依赖
pip install -r requirements.txt
## 5.配置说明
请在本地创建 .env（不要提交真实密钥），例如：
MODEL_API_BASE=your_model_api_base
MODEL_API_KEY=your_model_api_key
MILVUS_URI=./milvus_lite.db
6. 启动方式
bash
streamlit run 云运维问答.py
启动后在浏览器访问提示地址（通常为 http://localhost:8501）。
7. 复现实验最小流程
启动系统并登录
导入/准备样例知识文档
构建或加载向量索引
发起运维问题
查看回答与来源
在审计日志中查看问答记录
8. 提交说明
本仓库为论文答辩代码审查版本，遵循最小可复现原则：
已包含：核心源码、依赖说明、运行说明
未包含：大模型权重、完整原始语料、大体积向量索引文件
如需全量实验数据，请按论文中的数据准备流程自行构建。
