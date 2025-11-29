import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import date, datetime

# -----------------------------
# CONFIG: Fill these from Supabase
# -----------------------------
SUPABASE_URL = "https://duukgbkrjrzbvwvttfes.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_PjcqSjNTEaLUlb17Go_4XA_ckbRpHLo"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

ADMIN_PASSWORD = "1234"


# -----------------------------
# PROJECT FUNCTIONS
# -----------------------------

def get_projects():
    data = supabase.table("projects").select("*").execute()
    return pd.DataFrame(data.data)

def add_project(name, description, start_date, end_date):
    supabase.table("projects").insert({
        "name": name,
        "description": description,
        "start_date": str(start_date),
        "end_date": str(end_date)
    }).execute()


# -----------------------------
# TASK FUNCTIONS
# -----------------------------

def get_tasks(project_id):
    data = supabase.table("tasks").select("*").eq("project_id", project_id).execute()
    return pd.DataFrame(data.data)

def add_task(project_id, name, description, progress, owner, due_date):
    supabase.table("tasks").insert({
        "project_id": project_id,
        "name": name,
        "description": description,
        "progress": progress,
        "owner": owner,
        "due_date": str(due_date)
    }).execute()

def update_task_progress(task_id, progress):
    supabase.table("tasks").update({"progress": progress}).eq("id", task_id).execute()


# -----------------------------
# MINUTES / MEETING FUNCTIONS
# -----------------------------

def get_minutes(project_id):
    data = supabase.table("minutes").select("*").eq("project_id", project_id).order("meeting_date", desc=True).execute()
    return pd.DataFrame(data.data)

def add_minute(project_id, meeting_date, title, content):
    supabase.table("minutes").insert({
        "project_id": project_id,
        "meeting_date": str(meeting_date),
        "title": title,
        "content": content
    }).execute()


# -----------------------------
# TASK COMMENT FUNCTIONS
# -----------------------------

def get_task_comments(task_id):
    data = supabase.table("task_comments").select("*").eq("task_id", task_id).order("id", desc=True).execute()
    return pd.DataFrame(data.data)

def add_task_comment(task_id, author, content):
    supabase.table("task_comments").insert({
        "task_id": task_id,
        "author": author,
        "content": content
    }).execute()


# -----------------------------
# MINUTE COMMENT FUNCTIONS
# -----------------------------

def get_minute_comments(minute_id):
    data = supabase.table("minute_comments").select("*").eq("minute_id", minute_id).order("id", desc=True).execute()
    return pd.DataFrame(data.data)

def add_minute_comment(minute_id, author, content):
    supabase.table("minute_comments").insert({
        "minute_id": minute_id,
        "author": author,
        "content": content
    }).execute()


# -----------------------------
# STREAMLIT UI
# -----------------------------

def main():
    st.set_page_config("Project Tracker", layout="wide")
    st.title("📊 نرم‌افزار کنترل پروژه (Supabase Version)")

    mode = st.sidebar.radio("حالت نمایش", ("نمایش پروژه‌ها", "مدیریت"))

    projects_df = get_projects()

    # -----------------------------
    # MODE: VIEW
    # -----------------------------
    if mode == "نمایش پروژه‌ها":

        if projects_df.empty:
            st.info("هنوز هیچ پروژه‌ای ساخته نشده.")
            return

        # انتخاب پروژه
        selected_project = st.selectbox("انتخاب پروژه", projects_df["name"].tolist())
        project_row = projects_df[projects_df["name"] == selected_project].iloc[0]
        project_id = project_row["id"]

        st.subheader(f"پروژه: {project_row['name']}")
        st.write(project_row["description"])

        col1, col2 = st.columns(2)
        col1.write(f"تاریخ شروع: {project_row['start_date']}")
        col2.write(f"تاریخ پایان: {project_row['end_date']}")

        tasks = get_tasks(project_id)
        if not tasks.empty:
            avg_progress = int(tasks["progress"].mean())
            st.metric("درصد پیشرفت پروژه", f"{avg_progress}%")

            st.subheader("تسک‌ها")
            st.dataframe(tasks[["id", "name", "description", "owner", "due_date", "progress"]], use_container_width=True)

            # Comments for tasks
            st.subheader("💬 کامنت‌های تسک")
            options = tasks.apply(lambda r: f"{r['id']} - {r['name']}", axis=1).tolist()
            selected_task_label = st.selectbox("انتخاب تسک", options)
            selected_task_id = int(selected_task_label.split(" - ")[0])

            comments = get_task_comments(selected_task_id)
            for _, c in comments.iterrows():
                st.markdown(f"**{c['author'] or 'ناشناس'}** ({c['created_at']}): {c['content']}")

            # New comment
            author = st.text_input("نام شما", key="task_author")
            content = st.text_area("متن کامنت", key="task_comment")
            if st.button("ثبت کامنت"):
                add_task_comment(selected_task_id, author or None, content)
                st.success("کامنت ثبت شد. صفحه را رفرش کنید.")

        # Minutes
        st.subheader("📝 صورت‌جلسه‌ها")
        minutes = get_minutes(project_id)
        for _, row in minutes.iterrows():
            with st.expander(f"{row['meeting_date']} - {row['title']}"):
                st.write(row["content"])

                st.write("کامنت‌ها:")
                m_comments = get_minute_comments(row["id"])
                for _, c in m_comments.iterrows():
                    st.markdown(f"**{c['author'] or 'ناشناس'}**: {c['content']}")

                new_author = st.text_input(f"نام شما برای صورت‌جلسه {row['id']}", key=f"m_author_{row['id']}")
                new_content = st.text_area("متن کامنت", key=f"m_content_{row['id']}")
                if st.button("افزودن کامنت", key=f"m_btn_{row['id']}"):
                    add_minute_comment(row["id"], new_author, new_content)
                    st.success("کامنت ثبت شد.")

    # -----------------------------
    # MODE: ADMIN
    # -----------------------------
    else:
        pwd = st.sidebar.text_input("رمز مدیریت", type="password")
        if pwd != ADMIN_PASSWORD:
            st.error("رمز اشتباه است.")
            return

        st.success("وارد حالت مدیریت شدی.")

        tab1, tab2, tab3 = st.tabs(["➕ پروژه جدید", "🧱 تسک‌ها", "📝 صورت‌جلسه"])

        # Add project
        with tab1:
            st.write("افزودن پروژه جدید")
            name = st.text_input("نام پروژه")
            desc = st.text_area("توضیحات")
            start = st.date_input("تاریخ شروع")
            end = st.date_input("تاریخ پایان")
            if st.button("ثبت پروژه"):
                add_project(name, desc, start, end)
                st.success("پروژه ثبت شد.")

        # Tasks
        with tab2:
            st.write("مدیریت تسک‌ها")
            if not projects_df.empty:
                selected_project = st.selectbox("انتخاب پروژه", projects_df["name"].tolist(), key="admin_proj")
                project_row = projects_df[projects_df["name"] == selected_project].iloc[0]
                project_id = project_row["id"]

                t_name = st.text_input("نام تسک")
                t_desc = st.text_area("توضیحات")
                owner = st.text_input("مسئول")
                t_due = st.date_input("سررسید")
                t_prog = st.slider("پیشرفت", 0, 100, 0)

                if st.button("افزودن تسک"):
                    add_task(project_id, t_name, t_desc, t_prog, owner, t_due)
                    st.success("تسک ثبت شد.")

                st.write("ویرایش تسک‌ها")
                tasks = get_tasks(project_id)
                for _, row in tasks.iterrows():
                    new_progress = st.slider(row["name"], 0, 100, row["progress"])
                    if new_progress != row["progress"]:
                        update_task_progress(row["id"], new_progress)

        # Minutes
        with tab3:
            st.write("ثبت صورت‌جلسه")
            if not projects_df.empty:
                selected_project = st.selectbox("انتخاب پروژه", projects_df["name"].tolist(), key="admin_minutes")
                project_row = projects_df[projects_df["name"] == selected_project].iloc[0]
                project_id = project_row["id"]

                date_m = st.date_input("تاریخ جلسه")
                title = st.text_input("عنوان")
                content = st.text_area("متن")

                if st.button("ثبت صورت‌جلسه"):
                    add_minute(project_id, date_m, title, content)
                    st.success("ثبت شد.")

if __name__ == "__main__":
    main()
