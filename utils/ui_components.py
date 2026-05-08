import streamlit as st
from utils.auth import login, sha256_text
from utils.db import create_user, get_user_by_username

def render_header(title: str):
    st.title(title)

def render_login_form():
    tab_login, tab_register = st.tabs(["登录", "注册"])

    with tab_login:
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            submit = st.form_submit_button("登录", use_container_width=True)

        if submit:
            if login(username, password):
                st.success("登录成功")
                st.rerun()
            else:
                st.error("用户名或密码错误，或账户已被禁用")

    with tab_register:
        with st.form("register_form", clear_on_submit=True):
            reg_username = st.text_input("用户名（仅字母数字下划线）")
            reg_email = st.text_input("邮箱")
            reg_password = st.text_input("密码", type="password")
            reg_password2 = st.text_input("确认密码", type="password")
            reg_submit = st.form_submit_button("注册", use_container_width=True)

        if reg_submit:
            name = (reg_username or "").strip()
            email = (reg_email or "").strip()

            if not name:
                st.warning("用户名不能为空")
            elif len(name) < 3:
                st.warning("用户名至少 3 个字符")
            elif not all(ch.isalnum() or ch == "_" for ch in name):
                st.warning("用户名仅支持字母、数字、下划线")
            elif not reg_password:
                st.warning("密码不能为空")
            elif len(reg_password) < 6:
                st.warning("密码至少 6 位")
            elif reg_password != reg_password2:
                st.warning("两次输入的密码不一致")
            elif get_user_by_username(name):
                st.warning("用户名已存在")
            else:
                try:
                    create_user(
                        username=name,
                        password_hash=sha256_text(reg_password),
                        email=email,
                        role="engineer"
                    )
                    st.success("注册成功，请切换到登录页登录")
                except Exception as e:
                    st.error(f"注册失败：{e}")

def render_source_docs(docs):
    if not docs:
        st.info("未检索到可用知识来源。")
        return
    with st.expander("📄 知识来源", expanded=True):
        for i, doc in enumerate(docs, 1):
            st.markdown(f"**来源 {i}**：{doc.get('source_file', 'unknown')}")
            st.caption(
                f"产品线: {doc.get('product_line', '-')}"
                f" | 组件: {doc.get('component', '-')}"
                f" | 类型: {doc.get('doc_type', '-')}"
                f" | 相似度: {float(doc.get('score', 0)):.2f}"
            )
            st.text_area(
                f"文档片段 {i}",
                doc.get("text", ""),
                height=120,
                disabled=True,
                key=f"source_{i}_{doc.get('source_file','x')}"
            )
