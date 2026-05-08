import streamlit as st
from utils.ui_components import render_login_form

st.set_page_config(
    page_title="云运维问答 - 登录",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    [data-testid="stSidebar"] {display: none;}
    /* keep collapsedControl visible */

    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf3 100%);
    }

    .block-container {
        max-width: 480px !important;
        padding-top: 4rem !important;
        padding-bottom: 2rem !important;
        margin: 0 auto;
    }

    .login-title {
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
    }

    .login-subtitle {
        text-align: center;
        color: #888;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    

    .stButton > button {
        width: 100%;
        border-radius: 8px;
        padding: 0.6rem;
        font-weight: 600;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        transition: transform 0.2s, box-shadow 0.2s;
    }

    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        color: white;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem;
        justify-content: center;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 500;
    }

/* 去掉 form 自带灰框（你截图里的大框） */
div[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
}

/* 密码框右侧提示文字太突兀，隐藏 */
[data-testid="InputInstructions"] {
    display: none !important;
}

/* 统一输入区内部容器样式，避免双层边框 */
.stTextInput > div {
    background: transparent !important;
}


    /* ===== 彻底干掉输入框的红色 focus 边框 ===== */
    .stTextInput * {
        outline: none !important;
    }

    .stTextInput > div {
        border-color: transparent !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    .stTextInput > div > div {
        border: 1.5px solid #e1e4e8 !important;
        border-radius: 8px !important;
        background-color: #f8f9fa !important;
        transition: border-color 0.2s, box-shadow 0.2s;
    }

    .stTextInput > div > div:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15) !important;
        background-color: #ffffff !important;
    }

    .stTextInput input {
        background: transparent !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
        color: #1a1a1a !important;
        padding: 0.6rem 0.9rem !important;
    }

    .stTextInput input:focus {
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }

</style>
""", unsafe_allow_html=True)

st.markdown('<div class="login-title">云运维问答</div>', unsafe_allow_html=True)
st.markdown('<div class="login-subtitle">请登录后使用系统</div>', unsafe_allow_html=True)

# 保留原有登录/注册业务逻辑（ui_components 内部）
render_login_form()
