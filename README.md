# 云运维智能问答系统（Cloud Ops QA System）
## 项目简介
- 场景定位：本科毕业设计，面向云运维场景
- 核心方法：基于RAG（检索增强生成）实现知识问答、来源溯源与审计记录
- 混合数据库架构
    - SQLite（关系型）
        - 用途：存储用户、会话、审计日志等结构化数据
    - Milvus（向量库）
        - 用途：存储知识库文本向量与元数据
        - 功能：支持语义检索
- 系统功能
    - 用户登录与权限管理
        - 角色：admin
        - 角色：engineer
    - 文档知识库构建与检索
    - 智能问答与答案来源溯源
    - 问答操作审计日志记录与查询
## 技术栈
- 编程语言：Python 3.x
- Web交互框架：Streamlit
- 关系型数据库：SQLite
- 向量数据库：Milvus / Milvus Lite
- 向量模型：BGE-small-zh-v1.5
    - 向量维度：512
## 项目结构
- cloud-ops-qa-system/
    - pages/
        - 内容：页面模块（问答、文档管理等）
    - utils/
        - 内容：工具模块（鉴权、数据库、日志等）
    - src/
        - 内容：核心业务代码（如有）
    - scripts/
        - 内容：数据处理/初始化脚本
    - config/
        - 内容：配置文件
    - data/
        - 内容：本地数据（按提交策略可仅保留样例）
    - requirements.txt
        - 内容：依赖列表
    - README.md
        - 内容：项目说明文档
    - 云运维问答.py
        - 内容：主入口（按实际文件名）
## 环境准备
- 步骤1：进入项目
    - 命令：cd cloud-ops-qa-system
- 步骤2：创建并激活虚拟环境（可选）
    - 命令：python -m venv venv
    - 命令：source venv/bin/activate
- 步骤3：安装依赖
    - 命令：pip install -r requirements.txt
## 配置说明
- 配置文件：本地创建 .env（不要提交真实密钥）
- 配置示例
    - 键：MODEL_API_BASE
        - 值：your_model_api_base
    - 键：MODEL_API_KEY
        - 值：your_model_api_key
    - 键：MILVUS_URI
        - 值：./milvus_lite.db
## 启动方式
- 命令：streamlit run 云运维问答.py
- 访问地址：启动后在浏览器访问提示地址
    - 默认地址：http://localhost:8501
## 复现实验最小流程
- 流程1：启动系统并登录
- 流程2：导入/准备样例知识文档
- 流程3：构建或加载向量索引
- 流程4：发起运维问题
- 流程5：查看回答与来源
- 流程6：在审计日志中查看问答记录
## 提交说明
- 性质：本仓库为论文答辩代码审查版本
- 原则：遵循最小可复现原则
- 包含内容
    - 核心源码
    - 依赖说明
    - 运行说明
- 未包含内容
    - 大模型权重
    - 完整原始语料
    - 大体积向量索引文件
- 补充说明：如需全量实验数据，请按论文中的数据准备流程自行构建
