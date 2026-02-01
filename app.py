import streamlit as st
from streamlit_calendar import calendar
import datetime
import json
import os

# --- 1. 页面配置 ---
st.set_page_config(page_title="我的排课日历", page_icon="📅", layout="wide")
st.title("📅 老师排课系统")

# --- 2. 数据处理函数 ---
FILE_PATH = "schedule_data.json"

def load_events():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_events(events):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

# 初始化数据
if "events" not in st.session_state:
    st.session_state["events"] = load_events()

# --- 3. 侧边栏：添加/删除课程 ---
with st.sidebar:
    st.header("✏️ 操作面板")
    
    # 输入区域
    title = st.text_input("课程内容", placeholder="例如：1v1 张三")
    col1, col2 = st.columns(2)
    with col1:
        date_pick = st.date_input("日期", datetime.date.today())
    with col2:
        # 简单处理：让用户选开始和结束时间
        start_time = st.time_input("开始时间", datetime.time(9, 0))
        end_time = st.time_input("结束时间", datetime.time(10, 30))
    
    color = st.color_picker("标签颜色", "#FF4B4B") # 让用户选颜色，像苹果日历一样

    if st.button("➕ 添加课程", use_container_width=True):
        if title:
            # 转换为 ISO 格式字符串供日历插件使用
            start_str = f"{date_pick}T{start_time}"
            end_str = f"{date_pick}T{end_time}"
            
            new_event = {
                "title": title,
                "start": start_str,
                "end": end_str,
                "backgroundColor": color,
                "borderColor": color
            }
            st.session_state["events"].append(new_event)
            save_events(st.session_state["events"])
            st.success("添加成功！")
            st.rerun() # 刷新页面
        else:
            st.warning("请输入课程内容")

    st.divider()
    if st.button("🗑️ 清空所有课程（慎点）"):
        st.session_state["events"] = []
        save_events([])
        st.rerun()

# --- 4. 主界面：苹果风日历视图 ---
# 配置日历样式
calendar_options = {
    "editable": True, # 允许拖拽（在电脑上）
    "navLinks": True,
    "headerToolbar": {
        "left": "today prev,next",
        "center": "title",
        "right": "dayGridMonth,timeGridWeek,timeGridDay"
    },
    "initialView": "dayGridMonth", # 默认月视图
    "height": 650, # 足够高，适应手机
}

# 渲染日历
cal = calendar(events=st.session_state["events"], options=calendar_options)

st.caption("💡 提示：点击右上角的 'Week' 或 'Day' 可以切换视图。")