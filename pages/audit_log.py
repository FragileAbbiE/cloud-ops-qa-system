import datetime as dt
import streamlit as st
from utils.auth import get_current_user, require_admin
from utils.db import list_audit_logs

st.set_page_config(page_title="审计日志", page_icon="📊", layout="wide")

user = get_current_user()
if not user:
    st.error("请先登录")
    st.stop()

if not require_admin(user):
    st.error("无权访问")
    st.stop()

st.title("审计日志")

col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    username = st.text_input("按用户名筛选")
with col2:
    start_date = st.date_input("开始日期", value=dt.date.today() - dt.timedelta(days=7))
with col3:
    end_date = st.date_input("结束日期", value=dt.date.today())

mode = st.radio("时间范围模式", ["全天", "自定义时分秒"], horizontal=True)

start_time = ""
end_time = ""

if mode == "全天":
    start_time = f"{start_date.strftime('%Y-%m-%d')} 00:00:00"
    end_time = f"{end_date.strftime('%Y-%m-%d')} 23:59:59"
else:
    c1, c2 = st.columns(2)
    with c1:
        start_t = st.time_input("开始时间", value=dt.time(0, 0, 0))
    with c2:
        end_t = st.time_input("结束时间", value=dt.time(23, 59, 59))
    start_time = f"{start_date.strftime('%Y-%m-%d')} {start_t.strftime('%H:%M:%S')}"
    end_time = f"{end_date.strftime('%Y-%m-%d')} {end_t.strftime('%H:%M:%S')}"

if start_date > end_date:
    st.error("开始日期不能晚于结束日期")
    st.stop()

logs = list_audit_logs(username=username, start_time=start_time, end_time=end_time)

st.caption(f"当前筛选范围：{start_time} ~ {end_time}")
st.dataframe(logs, use_container_width=True)
