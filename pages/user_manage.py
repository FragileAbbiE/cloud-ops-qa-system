import streamlit as st
from utils.auth import get_current_user, require_admin, sha256_text
from utils.db import list_users, create_user, set_user_active, delete_user, update_user

st.set_page_config(page_title="用户管理", page_icon="👥", layout="wide")

user = get_current_user()
if not user:
    st.error("请先登录")
    st.stop()

if not require_admin(user):
    st.error("无权访问")
    st.stop()

st.title("用户权限管理")

with st.expander("➕ 添加用户", expanded=False):
    with st.form("add_user_form"):
        username = st.text_input("用户名")
        email = st.text_input("邮箱")
        password = st.text_input("初始密码", type="password")
        role = st.selectbox("角色", ["engineer", "admin"])
        submit = st.form_submit_button("创建用户")
    if submit:
        try:
            create_user(username, sha256_text(password), email, role)
            st.success("用户创建成功")
            st.rerun()
        except Exception as e:
            st.error(f"创建失败: {e}")

users = list_users()
st.dataframe(users, use_container_width=True)

if users:
    ids = [u["id"] for u in users]
    target_id = st.selectbox("选择用户 ID", ids)
    
    # 获取目标用户信息
    target_user = next((u for u in users if u["id"] == target_id), None)
    
    if target_user:
        # 显示当前用户基本信息
        st.markdown(f"""
        **当前选中用户：** {target_user.get('username', 'N/A')}  
        **邮箱：** {target_user.get('email', 'N/A')}  
        **角色：** {target_user.get('role', 'N/A')}  
        **状态：** {'已启用' if target_user.get('is_active', 1) == 1 else '已禁用'}
        """)
        
        st.divider()
        
        # 快捷操作按钮
        st.markdown("**快捷操作**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("禁用", use_container_width=True, key="btn_disable"):
                set_user_active(target_id, 0)
                st.success("已禁用")
                st.rerun()
        
        with col2:
            if st.button("启用", use_container_width=True, key="btn_enable"):
                set_user_active(target_id, 1)
                st.success("已启用")
                st.rerun()
        
        with col3:
            if st.button("删除", use_container_width=True, type="primary", key="btn_delete"):
                delete_user(target_id)
                st.success("已删除")
                st.rerun()
        
        st.divider()
        
        # 修改用户信息
        with st.expander("修改用户信息", expanded=False):
            with st.form("edit_user_form"):
                new_email = st.text_input("新邮箱", value=target_user.get("email", ""))
                new_password = st.text_input("新密码（留空则不修改）", type="password")
                
                role_options = ["engineer", "admin"]
                current_role = target_user.get("role", "engineer")
                role_index = 0 if current_role == "engineer" else 1
                new_role = st.selectbox("新角色", role_options, index=role_index)
                
                submit_edit = st.form_submit_button("保存修改", use_container_width=True)
            
            if submit_edit:
                try:
                    update_user(
                        user_id=target_id,
                        email=new_email if new_email != "" else None,
                        password_hash=sha256_text(new_password) if new_password else None,
                        role=new_role
                    )
                    st.success("用户信息已更新")
                    st.rerun()
                except Exception as e:
                    st.error(f"更新失败: {e}")