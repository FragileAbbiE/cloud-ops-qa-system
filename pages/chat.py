import streamlit as st
from src.retriever import MRAGRetriever
from src.generator import AnswerGenerator
from utils.auth import get_current_user
from utils.db import add_audit_log
from utils.ui_components import render_source_docs

user = get_current_user()
if not user:
    st.error("请先登录")
    st.stop()

@st.cache_resource
def get_retriever():
    return MRAGRetriever()

@st.cache_resource
def get_generator():
    return AnswerGenerator()

# ------------------ 确保会话存在 ------------------
if "chat_sessions" not in st.session_state or not st.session_state.chat_sessions:
    st.error("会话数据异常，请刷新页面")
    st.stop()

if "current_session_id" not in st.session_state or st.session_state.current_session_id is None:
    st.error("未选择会话，请在侧边栏选择或创建新会话")
    st.stop()

if st.session_state.current_session_id not in st.session_state.chat_sessions:
    st.error("当前会话不存在，请在侧边栏选择其他会话")
    st.stop()

# ------------------ 获取当前会话 ------------------
current = st.session_state.chat_sessions[st.session_state.current_session_id]
messages = current.get("messages", [])

# ------------------ 页面标题 ------------------
st.subheader("智能问答")
st.caption(f"当前会话：{current.get('title', '未命名会话')}")

# ------------------ 初始化 RAG 组件 ------------------
retriever = get_retriever()
generator = get_generator()

# ------------------ 显示历史消息 ------------------
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            render_source_docs(msg["sources"])

# ------------------ 用户输入 ------------------
if prompt := st.chat_input("请输入故障现象..."):
    # 如果是新会话，用第一条消息作为标题
    if current.get("title") == "新会话" or current.get("title", "").startswith("新会话"):
        current["title"] = prompt[:20] + ("..." if len(prompt) > 20 else "")

    # 添加用户消息
    messages.append({"role": "user", "content": prompt})
    current["messages"] = messages
    
    with st.chat_message("user"):
        st.markdown(prompt)

    # 检索相关文档
    docs = retriever.retrieve(prompt, top_k=3)

    # 生成回答
    with st.chat_message("assistant"):
        def stream_wrapper():
            for chunk in generator.generate_stream(prompt, docs):
                yield chunk

        answer = st.write_stream(stream_wrapper)
        render_source_docs(docs)

    # 添加助手消息
    messages.append({"role": "assistant", "content": answer, "sources": docs})
    current["messages"] = messages
    
    # 记录审计日志
    add_audit_log(user_id=user["id"], query=prompt, answer=answer, docs=docs)
