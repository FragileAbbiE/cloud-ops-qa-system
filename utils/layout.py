import streamlit as st

def inject_global_css():
    st.markdown(
        """
<style>
/* ===== 隐藏 Streamlit 默认元素 ===== */
#MainMenu {visibility: hidden;}
.stDeployButton {display: none;}
footer {visibility: hidden;}

/* 只隐藏顶部 header 的内容，但保留侧边栏展开按钮 */
header[data-testid="stHeader"] {
    visibility: hidden;
}

/* 强制显示侧边栏折叠/展开按钮 */
button[data-testid="collapsedControl"] {
    visibility: visible !important;
    display: block !important;
    position: fixed !important;
    top: 0.5rem !important;
    left: 0.5rem !important;
    z-index: 999999 !important;
    background: white !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    padding: 0.5rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    transition: all 0.2s !important;
}

button[data-testid="collapsedControl"]:hover {
    background: #f9fafb !important;
    border-color: #667eea !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2) !important;
}

/* 侧边栏展开时，隐藏展开按钮（因为已经有关闭按钮了） */
section[data-testid="stSidebar"]:not([aria-hidden="true"]) ~ div button[data-testid="collapsedControl"] {
    display: none !important;
}

/* ===== 侧边栏样式 ===== */
section[data-testid="stSidebar"] {
    background: #f5f7fa;
}

section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
    font-size: 15px;
    font-weight: 500;
}

section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
    background: #e8f1ff !important;
    color: #1d4ed8 !important;
    border-radius: 10px;
    font-weight: 700;
}

/* ===== 侧边栏会话列表样式 ===== */
.session-list-container {
    max-height: 50vh;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 4px;
    margin-bottom: 1rem;
}

.session-list-container::-webkit-scrollbar {
    width: 6px;
}

.session-list-container::-webkit-scrollbar-track {
    background: #f0f0f0;
    border-radius: 3px;
}

.session-list-container::-webkit-scrollbar-thumb {
    background: #c0c0c0;
    border-radius: 3px;
}

.session-list-container::-webkit-scrollbar-thumb:hover {
    background: #a0a0a0;
}

.session-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.4rem;
    padding: 0.5rem;
    border-radius: 8px;
    background: white;
    border: 1px solid #e5e7eb;
    transition: all 0.2s;
}

.session-item:hover {
    background: #f9fafb;
    border-color: #d1d5db;
}

.session-item.active {
    background: #e8f1ff !important;
    border-color: #3b82f6 !important;
}

.session-item .stButton > button {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    color: #374151 !important;
    font-size: 0.9rem !important;
    text-align: left !important;
    font-weight: 500 !important;
}

.session-item.active .stButton > button {
    color: #1d4ed8 !important;
    font-weight: 600 !important;
}

.session-item .delete-btn button {
    background: transparent !important;
    border: none !important;
    padding: 0.3rem 0.5rem !important;
    color: #9ca3af !important;
    font-size: 1.1rem !important;
    min-width: auto !important;
    width: auto !important;
}

.session-item .delete-btn button:hover {
    color: #ef4444 !important;
    background: #fee2e2 !important;
    border-radius: 6px !important;
}

.new-chat-btn button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    padding: 0.6rem !important;
    border-radius: 8px !important;
}

.new-chat-btn button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
}
</style>
""",
        unsafe_allow_html=True
    )
