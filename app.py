import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, date
import jdatetime

# -----------------------
# CONFIG
# -----------------------
SUPABASE_URL = "https://duukgbkrjrzbvwvttfes.supabase.co"
SUPABASE_KEY = "sb_publishable_PjcqSjNTEaLUlb17Go_4XA_ckbRpHLo"
ADMIN_PASSWORD = "1234"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(
    page_title="کنترل پروژه Z Group",
    layout="wide",
    page_icon="📊",
)

# -----------------------
# DATE HANDLING
# -----------------------

def jalali_to_gregorian(jdate):
    try:
        y, m, d = map(int, str(jdate).split("-"))
        return jdatetime.date(y, m, d).togregorian()
    except:
        return date.today()

def gregorian_to_jalali(gdate):
    if not gdate:
        return "بدون ددلاین"
    y, m, d = map(int, str(gdate).split("-"))
    return str(jdatetime.date.fromgregorian(year=y, month=m, day=d))


# -----------------------
# SUPABASE FUNCTIONS
# -----------------------

def get_projects():
    res = supabase.table("projects").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data)

def add_project(name, desc, start, end, no_deadline):
    supabase.table("projects").insert({
        "name": name,
        "description": desc,
        "start_date": str(start),
        "end_date": None if no_deadline else str(end)
    }).execute()

def get_tasks(pid):
    res = supabase.table("tasks").select("*").eq("project_id", int(pid)).order("id").execute()
    return pd.DataFrame(res.data)

def add_task(pid, name, desc, progress, owner, due, no_deadline):
    supabase.table("tasks").insert({
        "project_id": int(pid),
        "name": name,
        "description": desc,
        "progress": int(progress),
        "owner": owner,
        "due_date": None if no_deadline else str(due),
    }).execute()

def update_task_progress(tid, progress):
    supabase.table("tasks").update({
        "progress": int(progress)
    }).eq("id", int(tid)).execute()

def get_minutes(pid):
    res = supabase.table("minutes").select("*").eq("project_id", int(pid)).order("meeting_date", desc=True).execute()
    return pd.DataFrame(res.data)

def add_minute(pid, d, title, content):
    supabase.table("minutes").insert({
        "project_id": int(pid),
        "meeting_date": str(d),
        "title": title,
        "content": content
    }).execute()

def get_task_comments(tid):
    res = supabase.table("task_comments").select("*").eq("task_id", int(tid)).order("id", desc=True).execute()
    return pd.DataFrame(res.data)

def add_task_comment(tid, author, content):
    supabase.table("task_comments").insert({
        "task_id": int(tid),
        "author": author,
        "content": content
    }).execute()

def get_minute_comments(mid):
    res = supabase.table("minute_comments").select("*").eq("minute_id", int(mid)).order("id", desc=True).execute()
    return pd.DataFrame(res.data)

def add_minute_comment(mid, author, content):
    supabase.table("minute_comments").insert({
        "minute_id": int(mid),
        "author": author,
        "content": content
    }).execute()

# -----------------------
# SUBTASKS
# -----------------------

def get_subtasks(task_id):
    res = supabase.table("subtasks").select("*").eq("task_id", int(task_id)).order("id").execute()
    return pd.DataFrame(res.data)

def add_subtask(task_id, name, progress):
    supabase.table("subtasks").insert({
        "task_id": int(task_id),
        "name": name,
        "progress": int(progress)
    }).execute()

def update_subtask_progress(subtask_id, progress):
    supabase.table("subtasks").update({
        "progress": int(progress)
    }).eq("id", int(subtask_id)).execute()

def calculate_task_progress_from_subtasks(task_id):
    subs = get_subtasks(task_id)
    if subs.empty:
        return None
    return int(subs["progress"].mean())

def calculate_project_progress(tasks_df):
    if tasks_df.empty:
        return 0
    values = []
    for _, t in tasks_df.iterrows():
        auto = calculate_task_progress_from_subtasks(t["id"])
        values.append(auto if auto is not None else t["progress"])
    return int(sum(values) / len(values))


# -----------------------
# PAGE UI
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
    color: #1565C0;
}
.sub-card {
    background-color: #FFFFFF;
    padding: 12px;
    border-radius: 10px;
    border: 1px solid #E0E0E0;
    margin-bottom: 6px;
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
        st.info("پروژه‌ای ثبت نشده.")
        st.stop()

    pname = st.selectbox("انتخاب پروژه", projects["name"].tolist())
    proj = projects[projects["name"] == pname].iloc[0]
    pid = proj["id"]

    st.markdown(f"<div class='section-title'>📁 پروژه: {proj['name']}</div>", unsafe_allow_html=True)
    st.write(proj["description"])

    col1, col2 = st.columns(2)
    col1.write(f"📅 تاریخ شروع: **{gregorian_to_jalali(proj['start_date'])}**")
    col2.write(f"⏳ پایان: **{gregorian_to_jalali(proj['end_date'])}**")

    # Tasks
    tasks = get_tasks(pid)
    if not tasks.empty:

        avg_proj = calculate_project_progress(tasks)
        st.metric("درصد پیشرفت پروژه", f"{avg_proj}%")

        st.dataframe(tasks, use_container_width=True)

        st.subheader("🔎 انتخاب تسک")
        tlabel = st.selectbox(
            "تسک:",
            tasks.apply(lambda r: f"{r['id']} - {r['name']}", axis=1).tolist()
        )
        tid = int(tlabel.split(" - ")[0])

        sel_task = tasks[tasks["id"] == tid].iloc[0]

        auto_prog = calculate_task_progress_from_subtasks(tid)
        st.write(f"درصد ثبت‌شده: {sel_task['progress']}%")
        if auto_prog is not None:
            st.info(f"درصد محاسبه‌شده از زیرتسک‌ها: {auto_prog}%")

        # Comments
        st.subheader("💬 کامنت‌ها")
        comments = get_task_comments(tid)
        for _, c in comments.iterrows():
            st.markdown(f"**{c['author'] or 'ناشناس'}**: {c['content']}")

        author = st.text_input("نام شما", key="cname")
        ctext = st.text_area("متن کامنت", key="ctxt")
        if st.button("ارسال کامنت"):
            if ctext.strip():
                add_task_comment(tid, author or None, ctext.strip())
                st.success("کامنت ثبت شد. صفحه را رفرش کنید.")

        st.subheader("🔽 زیرتسک‌ها")
        subs = get_subtasks(tid)
        if subs.empty:
            st.info("زیرتسکی ندارد.")
        else:
            for _, sb in subs.iterrows():
                st.markdown(
                    f"<div class='sub-card'><b>{sb['name']}</b> — {sb['progress']}%</div>",
                    unsafe_allow_html=True
                )

    # Minutes
    st.subheader("📝 صورت‌جلسه‌ها")
    minutes = get_minutes(pid)
    if minutes.empty:
        st.info("صورت‌جلسه‌ای نیست.")
    else:
        for _, m in minutes.iterrows():
            with st.expander(f"{gregorian_to_jalali(m['meeting_date'])} - {m['title']}"):
                st.write(m['content'])

                mcom = get_minute_comments(m["id"])
                for _, c in mcom.iterrows():
                    st.markdown(f"**{c['author'] or 'ناشناس'}**: {c['content']}")

                an = st.text_input(f"نام شما ({m['id']})", key=f"mcname_{m['id']}")
                tx = st.text_area("کامنت", key=f"mctxt_{m['id']}")
                if st.button("ثبت کامنت", key=f"mbtn_{m['id']}"):
                    if tx.strip():
                        add_minute_comment(m["id"], an or None, tx.strip())
                        st.success("ثبت شد.")


# -----------------------
# ADMIN MODE
# -----------------------
else:
    pwd = st.sidebar.text_input("رمز مدیریت", type="password")
    if pwd != ADMIN_PASSWORD:
        st.error("رمز اشتباه است.")
        st.stop()

    st.success("وارد شدید ✔️")

    tab1, tab2, tab3 = st.tabs(["📁 پروژه‌ها", "🧱 تسک/زیرتسک", "📝 صورت‌جلسه"])

    # -----------------------
    # PROJECTS
    # -----------------------
    with tab1:
        st.subheader("➕ افزودن پروژه")

        name = st.text_input("نام پروژه")
        desc = st.text_area("توضیحات")
        jstart = st.text_input("تاریخ شروع (مثال: 1403-02-15)", key="js1")
        jend = st.text_input("تاریخ پایان (شمسی)", key="je1")
        no_deadline = st.checkbox("بدون ددلاین پروژه")

        if st.button("ثبت پروژه"):
            if name.strip():
                g_start = jalali_to_gregorian(jstart)
                g_end = jalali_to_gregorian(jend) if not no_deadline else None
                add_project(name, desc, g_start, g_end, no_deadline)
                st.success("پروژه ثبت شد.")
            else:
                st.warning("نام پروژه لازم است.")

        st.markdown("---")
        st.dataframe(get_projects(), use_container_width=True)

    # -----------------------
    # TASKS & SUBTASKS
    # -----------------------
    with tab2:
        st.subheader("🧱 مدیریت تسک‌ها")

        projs = get_projects()
        pname = st.selectbox("انتخاب پروژه", projs["name"].tolist(), key="p2")
        pid2 = projs[projs["name"] == pname].iloc[0]["id"]

        tname = st.text_input("نام تسک")
        tdesc = st.text_area("توضیحات")
        task_owner = st.text_input("مسئول")
        jdue = st.text_input("مهلت (شمسی) مثال: 1403-01-20")
        no_dl = st.checkbox("بدون ددلاین", key="ndl1")
        tprog = st.slider("درصد پیشرفت", 0, 100, 0)

        if st.button("افزودن تسک"):
            g_due = jalali_to_gregorian(jdue) if not no_dl else None
            add_task(pid2, tname, tdesc, tprog, task_owner, g_due, no_dl)
            st.success("تسک اضافه شد.")

        st.markdown("---")
        st.subheader("ویرایش پیشرفت تسک‌ها")

        tasks = get_tasks(pid2)
        for _, t in tasks.iterrows():
            auto_val = calculate_task_progress_from_subtasks(t["id"])
            label = t["name"]
            if auto_val is not None:
                label += f" (از زیرتسک‌ها {auto_val}%)"

            newp = st.slider(label, 0, 100, t["progress"], key=f"t_{t['id']}")
            if newp != t["progress"]:
                update_task_progress(t["id"], newp)

        # Subtasks
        st.markdown("---")
        st.subheader("🔽 زیرتسک‌ها")

        tlab = st.selectbox(
            "انتخاب تسک",
            tasks.apply(lambda r: f"{r['id']} - {r['name']}", axis=1).tolist(),
            key="subtselect"
        )
        sel_tid = int(tlab.split(" - ")[0])

        subname = st.text_input("نام زیرتسک")
        subprog = st.slider("پیشرفت زیرتسک", 0, 100, 0, key="sbp1")

        if st.button("افزودن زیرتسک"):
            add_subtask(sel_tid, subname, subprog)
            st.success("زیرتسک ثبت شد.")

        st.write("ویرایش زیرتسک‌ها:")
        subs = get_subtasks(sel_tid)
        for _, sb in subs.iterrows():
            np = st.slider(
                f"{sb['name']}",
                0, 100, sb["progress"],
                key=f"sb_{sb['id']}"
            )
            if np != sb["progress"]:
                update_subtask_progress(sb["id"], np)

    # -----------------------
    # MINUTES
    # -----------------------
    with tab3:
        st.subheader("📝 ثبت صورت‌جلسه")

        pname = st.selectbox("پروژه", projs["name"].tolist(), key="pm3")
        pidm = projs[projs["name"] == pname].iloc[0]["id"]

        jdate = st.text_input("تاریخ جلسه (شمسی)", key="jmin")
        title = st.text_input("عنوان")
        content = st.text_area("متن")

        if st.button("ثبت صورت‌جلسه"):
            add_minute(pidm, jalali_to_gregorian(jdate), title, content)
            st.success("صورت‌جلسه ثبت شد.")

        st.markdown("---")
        st.dataframe(get_minutes(pidm), use_container_width=True)
