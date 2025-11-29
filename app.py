import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date

# -----------------------
# CONFIGURATION
# -----------------------
SUPABASE_URL = "https://duukgbkrjrzbvwvttfes.supabase.co"
SUPABASE_KEY = "sb_publishable_PjcqSjNTEaLUlb17Go_4XA_ckbRpHLo"
ADMIN_PASSWORD = "1234"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------
# PAGE SETUP
# -----------------------
st.set_page_config(
    page_title="کنترل پروژه Z Group",
    layout="wide",
    page_icon="📊",
)

# -----------------------
# SUPABASE FUNCTIONS
# -----------------------
def get_projects():
    res = supabase.table("projects").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data)

def add_project(name, desc, start, end):
    supabase.table("projects").insert({
        "name": name,
        "description": desc,
        "start_date": str(start),
        "end_date": str(end)
    }).execute()

def get_tasks(pid):
    res = supabase.table("tasks").select("*").eq("project_id", pid).order("id").execute()
    return pd.DataFrame(res.data)

def add_task(pid, name, desc, progress, owner, due):
    supabase.table("tasks").insert({
        "project_id": pid,
        "name": name,
        "description": desc,
        "progress": progress,
        "owner": owner,
        "due_date": str(due),
    }).execute()

def update_task_progress(tid, progress):
    supabase.table("tasks").update({"progress": progress}).eq("id", tid).execute()

def get_minutes(pid):
    res = supabase.table("minutes").select("*").eq("project_id", pid).order("meeting_date", desc=True).execute()
    return pd.DataFrame(res.data)

def add_minute(pid, d, title, content):
    supabase.table("minutes").insert({
        "project_id": pid,
        "meeting_date": str(d),
        "title": title,
        "content": content
    }).execute()

def get_task_comments(tid):
    res = supabase.table("task_comments").select("*").eq("task_id", tid).order("id", desc=True).execute()
    return pd.DataFrame(res.data)

def add_task_comment(tid, author, content):
    supabase.table("task_comments").insert({
        "task_id": tid,
        "author": author,
        "content": content
    }).execute()

def get_minute_comments(mid):
    res = supabase.table("minute_comments").select("*").eq("minute_id", mid).order("id", desc=True).execute()
    return pd.DataFrame(res.data)

def add_minute_comment(mid, author, content):
    supabase.table("minute_comments").insert({
        "minute_id": mid,
        "author": author,
        "content": content
    }).execute()


# -----------------------
# HEADER
# -----------------------
st.markdown("""
<style>
.big-title {
    font-size: 36px !important;
    font-weight: 800 !important;
    text-align: center;
    color: #1E88E5;
    padding-bottom: 10px;
}
.section-title {
    font-size: 22px !important;
    font-weight: 700 !important;
    margin-top: 30px;
    color: #1565C0;
}
.card {
    background-color: #F8F9FA;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #E0E0E0;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='big-title'>📊 نرم‌افزار کنترل پروژه Z Group</div>", unsafe_allow_html=True)

# -----------------------
# SIDEBAR MODE
# -----------------------
mode = st.sidebar.radio("حالت:", ["🔍 نمایش پروژه‌ها", "🛠 مدیریت"], index=0)

# -----------------------
# VIEW MODE (FOR MANAGER)
# -----------------------
if mode == "🔍 نمایش پروژه‌ها":
    projects = get_projects()

    if projects.empty:
        st.info("هیچ پروژه‌ای ثبت نشده است.")
        st.stop()

    selected_name = st.selectbox("انتخاب پروژه", projects["name"].tolist())
    project = projects[projects["name"] == selected_name].iloc[0]
    pid = project["id"]

    st.markdown(f"<div class='section-title'>📁 پروژه: {project['name']}</div>", unsafe_allow_html=True)
    st.write(project["description"])

    col1, col2 = st.columns(2)
    col1.write(f"📅 تاریخ شروع: **{project['start_date']}**")
    col2.write(f"⏳ تاریخ پایان: **{project['end_date']}**")

    tasks = get_tasks(pid)

    if not tasks.empty:
        avg = int(tasks["progress"].mean())
        st.metric("درصد پیشرفت پروژه", f"{avg}%")

        st.subheader("🧱 تسک‌ها")
        st.dataframe(tasks[["id", "name", "description", "owner", "due_date", "progress"]], use_container_width=True)

        # Comments
        st.subheader("💬 کامنت‌های تسک")
        task_label = st.selectbox(
            "انتخاب تسک",
            tasks.apply(lambda r: f"{r['id']} - {r['name']}", axis=1).tolist()
        )
        tid = int(task_label.split(" - ")[0])

        comments = get_task_comments(tid)
        for _, c in comments.iterrows():
            st.markdown(f"**{c['author'] or 'ناشناس'}** ({c['created_at']}): {c['content']}")

        author = st.text_input("نام شما", key="task_author_ui")
        comment_text = st.text_area("متن کامنت", key="task_comment_ui")

        if st.button("ثبت کامنت", key="btn_task_comment"):
            add_task_comment(tid, author, comment_text)
            st.success("کامنت ثبت شد. صفحه را رفرش کنید.")

    # Minutes
    st.subheader("📝 صورت‌جلسه‌ها")
    minutes = get_minutes(pid)
    for _, m in minutes.iterrows():
        with st.expander(f"{m['meeting_date']} - {m['title']}"):
            st.write(m["content"])

            st.write("کامنت‌ها:")
            m_comments = get_minute_comments(m["id"])
            for _, c in m_comments.iterrows():
                st.markdown(f"**{c['author'] or 'ناشناس'}**: {c['content']}")

            a = st.text_input(f"نام شما برای صورت‌جلسه {m['id']}", key=f"m_author_{m['id']}")
            t = st.text_area("متن کامنت", key=f"m_text_{m['id']}")

            if st.button("ثبت کامنت", key=f"m_btn_{m['id']}"):
                add_minute_comment(m["id"], a, t)
                st.success("کامنت ثبت شد.")


# -----------------------
# ADMIN MODE (FOR YOU)
# -----------------------
else:
    pwd = st.sidebar.text_input("رمز مدیریت", type="password")

    if pwd != ADMIN_PASSWORD:
        st.error("رمز مدیریت اشتباه است.")
        st.stop()

    st.success("✔️ وارد حالت مدیریت شدی.")

    tab1, tab2, tab3 = st.tabs(["📁 پروژه جدید", "🧱 تسک‌ها", "📝 صورت‌جلسه"])

    # -----------------------
    # ADD PROJECT
    # -----------------------
    with tab1:
        st.subheader("➕ افزودن پروژه جدید")

        n = st.text_input("نام پروژه")
        d = st.text_area("توضیحات", key="admin_proj_desc")
        s = st.date_input("تاریخ شروع")
        e = st.date_input("تاریخ پایان")

        if st.button("ثبت پروژه", key="btn_add_project"):
            add_project(n, d, s, e)
            st.success("پروژه اضافه شد.")

    # -----------------------
    # MANAGE TASKS
    # -----------------------
    with tab2:
        st.subheader("🧱 مدیریت تسک‌ها")
        projects = get_projects()

        if not projects.empty:
            pname = st.selectbox("انتخاب پروژه", projects["name"].tolist(), key="admin_task_proj")
            p = projects[projects["name"] == pname].iloc[0]
            pid = p["id"]

            tn = st.text_input("نام تسک")
            td = st.text_area("توضیحات", key="admin_task_desc")
            owner = st.text_input("مسئول")
            due = st.date_input("مهلت")
            prog = st.slider("درصد پیشرفت", 0, 100, 0)

            if st.button("افزودن تسک", key="btn_add_task"):
                add_task(pid, tn, td, prog, owner, due)
                st.success("تسک ثبت شد.")

            st.write("ویرایش پیشرفت تسک‌ها:")
            tasks = get_tasks(pid)
            for _, t in tasks.iterrows():
                new_prog = st.slider(t["name"], 0, 100, t["progress"], key=f"edit_task_{t['id']}")
                if new_prog != t["progress"]:
                    update_task_progress(t["id"], new_prog)

    # -----------------------
    # MINUTES
    # -----------------------
    with tab3:
        st.subheader("📝 ثبت صورت‌جلسه")

        projects = get_projects()
        if not projects.empty:
            p2 = st.selectbox("انتخاب پروژه", projects["name"].tolist(), key="admin_min_proj")
            proj2 = projects[projects["name"] == p2].iloc[0]

            md = st.date_input("تاریخ جلسه")
            title = st.text_input("عنوان")
            cont = st.text_area("متن صورت‌جلسه", key="admin_min_text")

            if st.button("ثبت صورت‌جلسه", key="btn_add_minute"):
                add_minute(proj2["id"], md, title, cont)
                st.success("صورت‌جلسه ثبت شد!")
