import streamlit as st
from streamlit_calendar import calendar
from datetime import datetime, timedelta, date
import json
import os

# --- 1. 页面基础设置 ---
st.set_page_config(page_title="课表管理", page_icon="💰", layout="wide")

# 针对手机端的 CSS 优化（减少边距，让卡片更紧凑）
st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 5rem; padding-left: 0.5rem; padding-right: 0.5rem;}
        [data-testid="stMetricValue"] {font-size: 1.5rem !important;}
    </style>
""", unsafe_allow_html=True)

# --- 2. 数据处理函数 ---
FILE_PATH = "schedule_data.json"

def load_events():
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_events(events):
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=4)

# 初始化数据
if "events" not in st.session_state:
    st.session_state["events"] = load_events()

# --- 3. 统计逻辑函数 ---
def calculate_monthly_stats(events):
    now = datetime.now()
    current_month_str = now.strftime("%Y-%m") # 例如 2026-02
    
    total_income = 0.0
    total_hours = 0.0
    lesson_count = 0
    
    for event in events:
        # 提取开始时间，判断是否属于本月
        start_iso = event.get("start") # 格式如 2026-02-01T10:00:00
        if not start_iso: continue
        
        event_date_str = start_iso[:7] # 截取到月份
        
        if event_date_str == current_month_str:
            # 累加收入
            fee = event.get("extendedProps", {}).get("fee", 0)
            total_income += float(fee)
            
            # 累加时长 (小时)
            end_iso = event.get("end")
            if start_iso and end_iso:
                s_dt = datetime.fromisoformat(start_iso)
                e_dt = datetime.fromisoformat(end_iso)
                duration = (e_dt - s_dt).total_seconds() / 3600 # 转为小时
                total_hours += duration
                lesson_count += 1
                
    avg_price = (total_income / lesson_count) if lesson_count > 0 else 0
    return total_income, total_hours, avg_price

# --- 4. 弹窗表单：添加课程 ---
@st.dialog("➕ 添加课程")
def open_add_modal(default_date):
    # 表单输入
    with st.form("add_event_form"):
        st.write(f"日期：{default_date}")
        student_name = st.text_input("🎓 学生姓名/班级", placeholder="例如：张三 钢琴")
        
        col1, col2 = st.columns(2)
        with col1:
            start_t = st.time_input("开始时间", datetime.strptime("09:00", "%H:%M").time())
        with col2:
            end_t = st.time_input("结束时间", datetime.strptime("10:30", "%H:%M").time())
            
        fee = st.number_input("💰 本次课酬 (元)", min_value=0.0, step=50.0, value=200.0)
        note = st.text_area("📝 备注", placeholder="例如：需预习第二章", height=60)
        
        # 提交按钮
        submitted = st.form_submit_button("确认添加", use_container_width=True)
        
        if submitted:
            if student_name:
                # 构造时间字符串
                start_dt = f"{default_date}T{start_t.strftime('%H:%M:%S')}"
                end_dt = f"{default_date}T{end_t.strftime('%H:%M:%S')}"
                
                new_event = {
                    "title": f"{student_name} (￥{int(fee)})", # 标题显示名字和钱
                    "start": start_dt,
                    "end": end_dt,
                    "backgroundColor": "#3788d8", # 默认蓝色
                    # 额外存详细数据方便统计
                    "extendedProps": {
                        "student": student_name,
                        "fee": fee,
                        "note": note
                    },
                    # 鼠标悬停显示的描述（电脑端有效）
                    "description": note
                }
                
                st.session_state["events"].append(new_event)
                save_events(st.session_state["events"])
                st.success("添加成功！")
                st.rerun()
            else:
                st.error("请输入学生姓名")

# --- 5. 主界面布局 ---

# 5.1 顶部统计卡片
income, hours, avg = calculate_monthly_stats(st.session_state["events"])
st.subheader(f"📊 {datetime.now().month}月 财务概览")
m1, m2, m3 = st.columns(3)
m1.metric("💰 本月收入", f"¥{int(income)}")
m2.metric("⏱️ 总课时", f"{hours:.1f} h")
m3.metric("🏷️ 课均单价", f"¥{int(avg)}")

st.divider()

# 5.2 日历配置 (手机适配版)
calendar_options = {
    "editable": True, # 允许拖拽
    "selectable": True, # 允许点击选择
    "headerToolbar": {
        "left": "today",
        "center": "title",
        "right": "dayGridMonth,listMonth" # 增加列表视图，手机看列表更爽
    },
    "initialView": "dayGridMonth",
    "height": 600,
    "locale": "zh-cn", # 中文界面
    "buttonText": {
        "today": "今",
        "month": "月",
        "list": "列表"
    }
}

# 5.3 渲染日历并监听点击
cal = calendar(
    events=st.session_state["events"], 
    options=calendar_options, 
    callbacks=["dateClick", "eventClick"] # 监听点击空白处和点击事件
)

# --- 6. 交互逻辑处理 ---

# 逻辑A：点击了某个日期（空白格子）-> 弹出添加窗口
if cal.get("dateClick"):
    clicked_date = cal["dateClick"]["dateStr"] # 获取点击的日期 "2026-02-05"
    open_add_modal(clicked_date)

# 逻辑B：点击了已有的课程 -> 显示详情/删除
if cal.get("eventClick"):
    event_data = cal["eventClick"]["event"]
    props = event_data.get("extendedProps", {})
    
    @st.dialog("课程详情")
    def show_event_detail():
        st.write(f"**学生：** {props.get('student', '未知')}")
        st.write(f"**时间：** {event_data.get('start')} 至 {event_data.get('end')}")
        st.write(f"**费用：** ¥{props.get('fee', 0)}")
        st.info(f"备注：{props.get('note', '无')}")
        
        if st.button("🗑️ 删除此课程", type="primary", use_container_width=True):
            # 简单粗暴的删除逻辑：按标题和开始时间匹配（实际开发最好用ID）
            st.session_state["events"] = [
                e for e in st.session_state["events"] 
                if not (e["start"] == event_data["start"] and e["title"] == event_data["title"])
            ]
            save_events(st.session_state["events"])
            st.rerun()

    show_event_detail()
