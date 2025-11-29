import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date

# -----------------------
# CONFIGURATION
# -----------------------
SUPABASE_URL = "https://duukgbkrjrzbvwvttfes.supabase.co"
SUPABASE_KEY = "sb_publishable_PjcqSjNTEaLUlb17Go_4XA_ckbRpHLo"  # publishable key
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
# SUBTASKS FUNCTIONS
# -----------------------
def get_subtasks(task_id):
    res = supabase.table("subtasks").select("*").eq("task_id", task_id).order("id").execute()
    return pd.DataFrame(res.data)

def add_subtask(task_id, name, progress):
    supabase.table("subtasks").insert({
        "task_id": task_id,
        "name": name,
        "progress": progress
    }).execute()

def update_subtask_progress(subtask_id, progress):
    supabase.table("subtasks").update({
        "progress": progress
    }).eq("id", subtask_id).execute()

def calculate_task_progress_from_subtasks(task_id):
    subs = get_subtasks(task_id)
    if subs.empty:
        return None
    return int(subs["progress"].mean())

# برای درصد پروژه از روی تسک‌ها (با درنظر گرفتن زیرتسک‌ها)
def calculate_project_progress(tasks_df):
    if tasks_df.empty:
        return 0
    effective = []
    for _, row in tasks_df.iterrows():
        auto = calculate_task_progress_from_subtasks(row["id"])
        if auto is not None:
            effective.append(auto)
        else:
            effective.append(row["progress"])
    if not effective:
        return 0
    return int(sum(effective) / len(effective))

# -----------------------
# STYLES
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
.sub-card {
    background-color: #FFFFFF;
    padding: 10px 14px;
    border-radius: 10px;
    border: 1px solid #E0E0E0;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='big-title'>📊 نرم‌افزار کنترل پروژه Z Group</div>", unsafe_allow_html=True)

# -----------------------
# SIDEBAR
# -----------------------
mode = st.sidebar.radio("حالت:", ["🔍 نمایش پروژه‌ها", "🛠 مدیریت"], index=0)

# -----------------------
# VIEW MODE
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
        avg_project = calculate_project_progress(tasks)
        st.metric("درصد پیشرفت پروژه (بر اساس تسک‌ها و زیرتسک‌ها)", f"{avg_project}%")

        st.subheader("🧱 تسک‌ها")
        st.dataframe(tasks[["id", "name", "description", "owner", "due_date", "progress"]],
                     use_container_width=True)

        # انتخاب تسک برای کامنت و زیرتسک
        st.subheader("🔎 جزئیات تسک")
        task_label = st.selectbox(
            "انتخاب تسک",
            tasks.apply(lambda r: f"{r['id']} - {r['name']}", axis=1).tolist(),
            key="view_task_select"
        )
        selected_task_id = int(task_label.split(" - ")[0])
        selected_task_row = tasks[tasks["id"] == selected_task_id].iloc[0]

        auto_task_prog = calculate_task_progress_from_subtasks(selected_task_id)
        st.write(f"🔹 درصد ثبت‌شده تسک: **{selected_task_row['progress']}%**")
        if auto_task_prog is not None:
            st.info(f"🔹 درصد محاسبه‌شده از روی زیرتسک‌ها: **{auto_task_prog}%**")

        # کامنت‌های تسک
        st.subheader("💬 کامنت‌های تسک")
        comments = get_task_comments(selected_task_id)
        if comments.empty:
            st.info("هنوز کامنتی ثبت نشده.")
        else:
            for _, c in comments.iterrows():
                st.markdown(
                    f"**{c['author'] or 'ناشناس'}** ({c.get('created_at','')})‌: {c['content']}"
                )

        author = st.text_input("نام شما", key="task_author_ui")
        comment_text = st.text_area("متن کامنت", key="task_comment_ui")

        if st.button("ثبت کامنت", key="btn_task_comment"):
            if comment_text.strip():
                add_task_comment(selected_task_id, author or None, comment_text.strip())
                st.success("کامنت ثبت شد. صفحه را رفرش کنید.")
            else:
                st.warning("متن کامنت خالی است.")

        # زیرتسک‌ها (نمایش)
        st.subheader("🔽 زیرتسک‌ها")
        subtasks = get_subtasks(selected_task_id)
        if subtasks.empty:
            st.info("برای این تسک هنوز زیرتسکی ثبت نشده.")
        else:
            for _, s in subtasks.iterrows():
                with st.container():
                    st.markdown(
                        f"""
                        <div class='sub-card'>
                        <b>{s['name']}</b><br>
                        پیشرفت: {s['progress']}%
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

    # صورت‌جلسه‌ها
    st.subheader("📝 صورت‌جلسه‌ها")
    minutes = get_minutes(pid)
    if minutes.empty:
        st.info("هیچ صورت‌جلسه‌ای برای این پروژه ثبت نشده.")
    else:
        for _, m in minutes.iterrows():
            with st.expander(f"{m['meeting_date']} - {m['title']}"):
                st.write(m["content"])

                st.write("کامنت‌ها:")
                m_comments = get_minute_comments(m["id"])
                if m_comments.empty:
                    st.info("کامنتی ثبت نشده.")
                else:
                    for _, c in m_comments.iterrows():
                        st.markdown(f"**{c['author'] or 'ناشناس'}**: {c['content']}")

                a = st.text_input(f"نام شما (صورت‌جلسه {m['id']})", key=f"m_author_{m['id']}")
                t = st.text_area("متن کامنت", key=f"m_text_{m['id']}")

                if st.button("ثبت کامنت صورت‌جلسه", key=f"m_btn_{m['id']}"):
                    if t.strip():
                        add_minute_comment(m["id"], a or None, t.strip())
                        st.success("کامنت ثبت شد.")
                    else:
                        st.warning("متن کامنت خالی است.")

# -----------------------
# ADMIN MODE
# -----------------------
else:
    pwd = st.sidebar.text_input("رمز مدیریت", type="password")

    if pwd != ADMIN_PASSWORD:
        st.error("رمز مدیریت اشتباه است.")
        st.stop()

    st.success("✔️ وارد حالت مدیریت شدی.")

    tab1, tab2, tab3 = st.tabs(["📁 پروژه‌ها", "🧱 تسک‌ها و زیرتسک‌ها", "📝 صورت‌جلسه"])

    # -----------------------
    # TAB 1: PROJECTS
    # -----------------------
    with tab1:
        st.subheader("➕ افزودن پروژه جدید")

        n = st.text_input("نام پروژه")
        d = st.text_area("توضیحات پروژه", key="admin_proj_desc")
        s = st.date_input("تاریخ شروع", value=date.today())
        e = st.date_input("تاریخ پایان", value=date.today())

        if st.button("ثبت پروژه", key="btn_add_project"):
            if n.strip():
                add_project(n.strip(), d.strip(), s, e)
                st.success("پروژه اضافه شد.")
            else:
                st.warning("نام پروژه را وارد کن.")

        st.markdown("---")
        st.subheader("لیست پروژه‌ها")
        projects = get_projects()
        if projects.empty:
            st.info("پروژه‌ای وجود ندارد.")
        else:
            st.dataframe(projects, use_container_width=True)

    # -----------------------
    # TAB 2: TASKS & SUBTASKS
    # -----------------------
    with tab2:
        st.subheader("🧱 مدیریت تسک‌ها و زیرتسک‌ها")

        projects = get_projects()
        if projects.empty:
            st.info("اول یک پروژه بساز.")
        else:
            pname = st.selectbox("انتخاب پروژه", projects["name"].tolist(), key="admin_task_proj")
            p = projects[projects["name"] == pname].iloc[0]
            pid = p["id"]

            st.markdown("### ➕ افزودن تسک")
            tn = st.text_input("نام تسک", key="admin_task_name")
            td = st.text_area("توضیحات تسک", key="admin_task_desc")
            owner = st.text_input("مسئول", key="admin_task_owner")
            due = st.date_input("مهلت تسک", value=date.today(), key="admin_task_due")
            prog = st.slider("درصد پیشرفت (اگر زیرتسک نداری)", 0, 100, 0, key="admin_task_prog")

            if st.button("افزودن تسک", key="btn_add_task"):
                if tn.strip():
                    add_task(pid, tn.strip(), td.strip(), prog, owner.strip(), due)
                    st.success("تسک ثبت شد.")
                else:
                    st.warning("نام تسک را وارد کن.")

            st.markdown("---")
            st.markdown("### ✏️ ویرایش پیشرفت تسک‌ها")
            tasks = get_tasks(pid)
            if tasks.empty:
                st.info("تسکی وجود ندارد.")
            else:
                for _, t in tasks.iterrows():
                    auto_val = calculate_task_progress_from_subtasks(t["id"])
                    label = t["name"]
                    if auto_val is not None:
                        label = f"{t['name']} (درصد از زیرتسک‌ها: {auto_val}%)"

                    new_prog = st.slider(
                        label,
                        0, 100, t["progress"],
                        key=f"edit_task_{t['id']}"
                    )
                    if new_prog != t["progress"]:
                        update_task_progress(t["id"], new_prog)

            st.markdown("---")
            st.markdown("### 🔽 مدیریت زیرتسک‌ها")

            if tasks.empty:
                st.info("تسکی نیست که برایش زیرتسک تعریف کنیم.")
            else:
                task_label_admin = st.selectbox(
                    "انتخاب تسک برای زیرتسک‌ها",
                    tasks.apply(lambda r: f"{r['id']} - {r['name']}", axis=1).tolist(),
                    key="admin_subtask_task_select"
                )
                sub_task_id = int(task_label_admin.split(" - ")[0])

                st.markdown("#### ➕ افزودن زیرتسک جدید")
                sub_name = st.text_input("نام زیرتسک", key="sub_name_admin")
                sub_prog = st.slider("درصد پیشرفت زیرتسک", 0, 100, 0, key="sub_prog_admin")

                if st.button("ثبت زیرتسک", key="add_subtask_btn"):
                    if sub_name.strip():
                        add_subtask(sub_task_id, sub_name.strip(), sub_prog)
                        st.success("زیرتسک ثبت شد.")
                    else:
                        st.warning("نام زیرتسک را وارد کن.")

                st.markdown("#### ✏️ ویرایش زیرتسک‌ها")
                subs = get_subtasks(sub_task_id)
                if subs.empty:
                    st.info("برای این تسک هنوز زیرتسکی تعریف نشده.")
                else:
                    for _, sb in subs.iterrows():
                        col1, col2 = st.columns([2, 3])
                        with col1:
                            st.write(f"🔹 {sb['name']}")
                        with col2:
                            new_val = st.slider(
                                f"پیشرفت ({sb['name']})",
                                0, 100, sb["progress"],
                                key=f"edit_sub_{sb['id']}"
                            )
                            if new_val != sb["progress"]:
                                update_subtask_progress(sb["id"], new_val)

    # -----------------------
    # TAB 3: MINUTES
    # -----------------------
    with tab3:
        st.subheader("📝 ثبت صورت‌جلسه")

        projects = get_projects()
        if projects.empty:
            st.info("اول یک پروژه بساز.")
        else:
            p2_name = st.selectbox("انتخاب پروژه", projects["name"].tolist(), key="admin_min_proj")
            proj2 = projects[projects["name"] == p2_name].iloc[0]
            pid2 = proj2["id"]

            md = st.date_input("تاریخ جلسه", value=date.today(), key="admin_min_date")
            title = st.text_input("عنوان جلسه", key="admin_min_title")
            cont = st.text_area("متن صورت‌جلسه", key="admin_min_text")

            if st.button("ثبت صورت‌جلسه", key="btn_add_minute"):
                if title.strip() and cont.strip():
                    add_minute(pid2, md, title.strip(), cont.strip())
                    st.success("صورت‌جلسه ثبت شد.")
                else:
                    st.warning("عنوان و متن صورت‌جلسه را کامل وارد کن.")

            st.markdown("---")
            st.subheader("لیست صورت‌جلسه‌ها")
            mins = get_minutes(pid2)
            if mins.empty:
                st.info("برای این پروژه صورت‌جلسه‌ای ثبت نشده.")
            else:
                st.dataframe(mins, use_container_width=True)
