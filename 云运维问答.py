import streamlit as st
import uuid
from datetime import datetime
from utils.auth import get_current_user, ensure_default_admin, logout
from utils.db import init_db
from utils.layout import inject_global_css

st.set_page_config(
    page_title="云运维问答",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

inject_global_css()
init_db()
ensure_default_admin()

user = get_current_user()

# 未登录：仅显示登录页
if not user:
    login_page = st.Page("pages/login.py", title="登录", icon=":material/login:")
    nav = st.navigation([login_page], position="sidebar")
    nav.run()
    st.stop()

# ------------------ 页面权限 ------------------
pages = [
    st.Page("pages/chat.py", title="智能问答", icon=":material/chat:", default=True)
]
if user.get("role") == "admin":
    pages.append(st.Page("pages/doc_manage.py", title="文档管理", icon=":material/folder_managed:"))
    pages.append(st.Page("pages/user_manage.py", title="用户管理", icon=":material/group:"))
    pages.append(st.Page("pages/audit_log.py", title="审计日志", icon=":material/analytics:"))

# ------------------ 角色映射 ------------------
role_map = {
    "admin": "管理员",
    "engineer": "运维工程师",
}
raw_role = str(user.get("role", "") or "")
role_text = role_map.get(raw_role.lower(), raw_role if raw_role else "未知角色")

# ------------------ 初始化会话数据（确保有默认会话）------------------
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {}

if "current_session_id" not in st.session_state or st.session_state.current_session_id is None:
    if not st.session_state.chat_sessions:
        default_session_id = str(uuid.uuid4())
        st.session_state.chat_sessions[default_session_id] = {
            "title": "新会话 1",
            "messages": [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.current_session_id = default_session_id
    else:
        st.session_state.current_session_id = list(st.session_state.chat_sessions.keys())[0]

# ------------------ 侧边栏样式 ------------------
st.markdown(
    """
    <style>
    /* 给底部固定区预留空间，防止遮挡历史会话 */
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-bottom: 220px !important;
    }

    /* 底部固定区（跟随侧边栏内边距与宽度） */
    [data-testid="stSidebar"] .bottom-user-box {
        position: fixed;
        left: 1rem;
        bottom: 1rem;
        width: calc(16rem - 2rem);  /* 默认侧边栏宽度 16rem */
        z-index: 1000;
        background: linear-gradient(to top, #ffffff 88%, rgba(255,255,255,0));
        padding-top: 0.6rem;
        border-top: 1px solid #e5e7eb;
    }

    [data-testid="stSidebar"] .user-card {
        background: #ffffff;
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        margin-bottom: 0.5rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }

    [data-testid="stSidebar"] .user-name {
        font-size: 0.95rem;
        font-weight: 600;
        color: #374151;
    }

    [data-testid="stSidebar"] .user-role {
        font-size: 0.85rem;
        color: #9ca3af;
        margin-top: 0.2rem;
    }

    /* 历史会话行内按钮对齐 */
    [data-testid="column"] button {
        vertical-align: middle;
    }

    [data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------ 侧边栏：顶部标题 ------------------
with st.sidebar:
    st.markdown("### ☁️ 云运维问答")
    st.caption("智能运维知识助手")
    st.divider()

# ------------------ 导航 ------------------
nav = st.navigation(pages, position="sidebar")

# ------------------ 历史会话功能（只在这里显示一次）------------------
with st.sidebar:
    st.markdown("#### 📝 历史会话")
    
    # 新建会话按钮
    if st.button("➕ 新对话", use_container_width=True, key="new_session"):
        new_session_id = str(uuid.uuid4())
        session_count = len(st.session_state.chat_sessions) + 1
        st.session_state.chat_sessions[new_session_id] = {
            "title": f"新会话 {session_count}",
            "messages": [],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state.current_session_id = new_session_id
        st.rerun()
    
    st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
    
    # 显示会话列表
    for session_id, session in list(st.session_state.chat_sessions.items()):
        col1, col2 = st.columns([5, 1])
        
        with col1:
            is_active = session_id == st.session_state.current_session_id
            button_type = "primary" if is_active else "secondary"
            if st.button(
                session.get("title", "未命名会话"),
                key=f"session_{session_id}",
                use_container_width=True,
                type=button_type
            ):
                st.session_state.current_session_id = session_id
                st.rerun()
        
        with col2:
            if st.button("🗑️", key=f"delete_{session_id}", help="删除会话"):
                del st.session_state.chat_sessions[session_id]
                if st.session_state.current_session_id == session_id:
                    if st.session_state.chat_sessions:
                        st.session_state.current_session_id = list(st.session_state.chat_sessions.keys())[0]
                    else:
                        new_session_id = str(uuid.uuid4())
                        st.session_state.chat_sessions[new_session_id] = {
                            "title": "新会话 1",
                            "messages": [],
                            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.session_state.current_session_id = new_session_id
                st.rerun()
    
    st.divider()

# ------------------ 侧边栏底部：用户卡片 + 退出 ------------------
with st.sidebar:
    st.markdown('<div class="bottom-user-box">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="user-card">
            <div class="user-name">{user.get("username", "未知用户")}</div>
            <div class="user-role">角色：{role_text}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("退出登录", use_container_width=True, key="global_logout", type="secondary"):
        logout()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# 运行导航
nav.run()
