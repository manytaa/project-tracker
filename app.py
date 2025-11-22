# redeploy fix

import sqlite3
from datetime import date, datetime
import pandas as pd
import streamlit as st

DB_NAME = "projects.db"

# ⚠️ اینو بعدا ببر تو st.secrets یا متغیر محیطی
ADMIN_PASSWORD = "1234"


# ---------- DB FUNCTIONS ----------
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        start_date TEXT,
        end_date TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        progress INTEGER DEFAULT 0,
        owner TEXT,
        due_date TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS minutes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        meeting_date TEXT,
        title TEXT,
        content TEXT,
        FOREIGN KEY(project_id) REFERENCES projects(id)
    )
    """)

    # جدول کامنت‌های تسک‌ها
    cur.execute("""
    CREATE TABLE IF NOT EXISTS task_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        author TEXT,
        content TEXT NOT NULL,
        created_at TEXT,
        FOREIGN KEY(task_id) REFERENCES tasks(id)
    )
    """)

    # جدول کامنت‌های صورت‌جلسه‌ها
    cur.execute("""
    CREATE TABLE IF NOT EXISTS minute_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        minute_id INTEGER NOT NULL,
        author TEXT,
        content TEXT NOT NULL,
        created_at TEXT,
        FOREIGN KEY(minute_id) REFERENCES minutes(id)
    )
    """)

    conn.commit()
    conn.close()

def get_projects():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM projects", conn)
    conn.close()
    return df

def add_project(name, description, start_date, end_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO projects (name, description, start_date, end_date)
        VALUES (?, ?, ?, ?)
    """, (name, description, str(start_date) if start_date else None, str(end_date) if end_date else None))
    conn.commit()
    conn.close()

def get_tasks(project_id):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM tasks WHERE project_id = ?",
        conn,
        params=(project_id,)
    )
    conn.close()
    return df

def add_task(project_id, name, description, progress, owner, due_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks (project_id, name, description, progress, owner, due_date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (project_id, name, description, progress, owner, str(due_date) if due_date else None))
    conn.commit()
    conn.close()

def update_task_progress(task_id, progress):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE tasks SET progress = ? WHERE id = ?
    """, (progress, task_id))
    conn.commit()
    conn.close()

def add_minute(project_id, meeting_date, title, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO minutes (project_id, meeting_date, title, content)
        VALUES (?, ?, ?, ?)
    """, (project_id, str(meeting_date) if meeting_date else None, title, content))
    conn.commit()
    conn.close()

def get_minutes(project_id):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM minutes WHERE project_id = ? ORDER BY meeting_date DESC",
        conn,
        params=(project_id,)
    )
    conn.close()
    return df

# ----- کامنت‌های تسک -----
def get_task_comments(task_id):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM task_comments WHERE task_id = ? ORDER BY id DESC",
        conn,
        params=(task_id,)
    )
    conn.close()
    return df

def add_task_comment(task_id, author, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO task_comments (task_id, author, content, created_at)
        VALUES (?, ?, ?, ?)
    """, (task_id, author, content, datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()

# ----- کامنت‌های صورت‌جلسه -----
def get_minute_comments(minute_id):
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM minute_comments WHERE minute_id = ? ORDER BY id DESC",
        conn,
        params=(minute_id,)
    )
    conn.close()
    return df

def add_minute_comment(minute_id, author, content):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO minute_comments (minute_id, author, content, created_at)
        VALUES (?, ?, ?, ?)
    """, (minute_id, author, content, datetime.now().isoformat(timespec="seconds")))
    conn.commit()
    conn.close()


# ---------- UI ----------
def main():
    st.set_page_config("نرم‌افزار کنترل پروژه", layout="wide")
    st.title("📊 نرم‌افزار کنترل پروژه (نسخه شخصی)")

    init_db()

    mode = st.sidebar.radio(
        "حالت کاربری",
        ("نمایش پروژه‌ها", "مدیریت / ویرایش")
    )

    projects_df = get_projects()

    if mode == "نمایش پروژه‌ها":
        if projects_df.empty:
            st.info("هنوز هیچ پروژه‌ای ثبت نشده.")
            return

        proj_names = projects_df["name"].tolist()
        selected_name = st.selectbox("پروژه را انتخاب کن:", proj_names)
        project_row = projects_df[projects_df["name"] == selected_name].iloc[0]
        project_id = project_row["id"]

        st.subheader(f"پروژه: {project_row['name']}")
        st.write(project_row["description"])

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**تاریخ شروع:** {project_row['start_date']}")
        with col2:
            st.markdown(f"**تاریخ پایان:** {project_row['end_date']}")

        # تسک‌ها
        tasks_df = get_tasks(project_id)
        if tasks_df.empty:
            st.warning("برای این پروژه هنوز هیچ تسکی ثبت نشده.")
        else:
            avg_progress = int(tasks_df["progress"].mean())
            st.metric("درصد تکمیل پروژه", f"{avg_progress} %")

            st.markdown("### تسک‌ها")
            show_df = tasks_df[["id", "name", "description", "owner", "due_date", "progress"]]
            show_df = show_df.rename(columns={
                "id": "ID",
                "name": "نام تسک",
                "description": "توضیحات",
                "owner": "مسئول",
                "due_date": "سررسید",
                "progress": "درصد تکمیل"
            })
            st.dataframe(show_df, use_container_width=True)

            # --- کامنت روی تسک‌ها ---
            st.markdown("### 💬 نظرات روی تسک‌ها")
            task_options = tasks_df[["id", "name"]].apply(lambda r: f"{r['id']} - {r['name']}", axis=1).tolist()
            if task_options:
                selected_task_label = st.selectbox("تسک را انتخاب کن:", task_options)
                selected_task_id = int(selected_task_label.split(" - ")[0])

                comments_df = get_task_comments(selected_task_id)
                if comments_df.empty:
                    st.info("هنوز کامنتی برای این تسک ثبت نشده.")
                else:
                    for _, c in comments_df.iterrows():
                        st.markdown(f"**{c['author'] or 'ناشناس'}** ({c['created_at']}):  {c['content']}")

                st.markdown("#### ثبت کامنت جدید برای این تسک")
                c_author = st.text_input("نام شما (اختیاری)", key="task_comment_author")
                c_content = st.text_area("متن کامنت", key="task_comment_content")
                if st.button("ثبت کامنت روی تسک"):
                    if not c_content.strip():
                        st.warning("متن کامنت را وارد کن.")
                    else:
                        add_task_comment(selected_task_id, c_author.strip() or None, c_content.strip())
                        st.success("کامنت ثبت شد. برای دیدن، صفحه را رفرش کن یا دوباره تسک را انتخاب کن.")

        # صورت‌جلسه‌ها
        st.markdown("### صورت‌جلسه‌ها")
        minutes_df = get_minutes(project_id)
        if minutes_df.empty:
            st.info("صورت‌جلسه‌ای برای این پروژه ثبت نشده.")
        else:
            for _, row in minutes_df.iterrows():
                with st.expander(f"{row['meeting_date']} - {row['title']}"):
                    st.write(row["content"])

                    st.markdown("**کامنت‌ها:**")
                    m_comments = get_minute_comments(row["id"])
                    if m_comments.empty:
                        st.info("کامنتی برای این صورت‌جلسه ثبت نشده.")
                    else:
                        for _, c in m_comments.iterrows():
                            st.markdown(f"- **{c['author'] or 'ناشناس'}** ({c['created_at']}): {c['content']}")

                    st.markdown("**افزودن کامنت جدید:**")
                    mc_author = st.text_input(
                        f"نام شما (اختیاری) - صورت‌جلسه {row['id']}",
                        key=f"minute_comment_author_{row['id']}"
                    )
                    mc_content = st.text_area(
                        "متن کامنت",
                        key=f"minute_comment_content_{row['id']}"
                    )
                    if st.button("ثبت کامنت روی صورت‌جلسه", key=f"minute_comment_btn_{row['id']}"):
                        if not mc_content.strip():
                            st.warning("متن کامنت را وارد کن.")
                        else:
                            add_minute_comment(row["id"], mc_author.strip() or None, mc_content.strip())
                            st.success("کامنت ثبت شد. برای دیدن، expander را ببند و دوباره باز کن یا صفحه را رفرش کن.")

    else:  # مدیریت
        pwd = st.sidebar.text_input("رمز مدیریت", type="password")
        if pwd != ADMIN_PASSWORD:
            st.error("رمز اشتباه است. فقط امکان مشاهده با حالت «نمایش پروژه‌ها» بدون رمز وجود دارد.")
            return

        st.success("✅ وارد حالت مدیریت شدی.")
        tab1, tab2, tab3 = st.tabs(["➕ پروژه جدید", "🧱 تسک‌ها", "📝 صورت‌جلسه"])

        # --- تب پروژه جدید ---
        with tab1:
            st.subheader("افزودن پروژه جدید")
            name = st.text_input("نام پروژه")
            desc = st.text_area("توضیحات پروژه")
            c1, c2 = st.columns(2)
            with c1:
                start = st.date_input("تاریخ شروع", value=date.today())
            with c2:
                end = st.date_input("تاریخ پایان", value=date.today())

            if st.button("ثبت پروژه"):
                if not name.strip():
                    st.warning("نام پروژه را وارد کن.")
                else:
                    add_project(name, desc, start, end)
                    st.success("پروژه با موفقیت ثبت شد. صفحه را رفرش کن تا در لیست نمایش داده شود.")

        # --- تب تسک‌ها ---
        with tab2:
            st.subheader("مدیریت تسک‌ها")

            if projects_df.empty:
                st.info("اول یک پروژه بساز.")
            else:
                proj_names = projects_df["name"].tolist()
                selected_name = st.selectbox("پروژه:", proj_names, key="task_proj_select")
                project_row = projects_df[projects_df["name"] == selected_name].iloc[0]
                project_id = project_row["id"]

                st.markdown("#### افزودن تسک جدید")
                t_name = st.text_input("نام تسک", key="new_task_name")
                t_desc = st.text_area("توضیحات تسک", key="new_task_desc")
                c1, c2, c3 = st.columns(3)
                with c1:
                    t_owner = st.text_input("مسئول تسک")
                with c2:
                    t_due = st.date_input("سررسید تسک", value=date.today())
                with c3:
                    t_progress = st.slider("درصد اولیه تکمیل", 0, 100, 0)

                if st.button("ثبت تسک"):
                    if not t_name.strip():
                        st.warning("نام تسک را وارد کن.")
                    else:
                        add_task(project_id, t_name, t_desc, t_progress, t_owner, t_due)
                        st.success("تسک ثبت شد.")

                st.markdown("---")
                st.markdown("#### ویرایش درصد تکمیل تسک‌ها")
                tasks_df = get_tasks(project_id)
                if tasks_df.empty:
                    st.info("برای این پروژه هنوز تسکی ثبت نشده.")
                else:
                    for _, row in tasks_df.iterrows():
                        col1, col2 = st.columns([3, 2])
                        with col1:
                            st.write(f"**{row['name']}** - {row['description']}")
                        with col2:
                            new_prog = st.slider(
                                f"درصد تکمیل (ID {row['id']})",
                                0, 100, int(row["progress"]),
                                key=f"prog_{row['id']}"
                            )
                            if new_prog != row["progress"]:
                                update_task_progress(row["id"], new_prog)
                    st.success("هر تغییری که اسلایدرها دادی، ذخیره شد.")

        # --- تب صورت‌جلسه ---
        with tab3:
            st.subheader("ثبت صورت‌جلسه")

            if projects_df.empty:
                st.info("اول یک پروژه بساز.")
            else:
                proj_names = projects_df["name"].tolist()
                selected_name = st.selectbox("پروژه:", proj_names, key="minutes_proj_select")
                project_row = projects_df[projects_df["name"] == selected_name].iloc[0]
                project_id = project_row["id"]

                m_date = st.date_input("تاریخ جلسه", value=date.today())
                m_title = st.text_input("عنوان جلسه")
                m_content = st.text_area("متن صورت‌جلسه")

                if st.button("ثبت صورت‌جلسه"):
                    if not m_title.strip():
                        st.warning("عنوان جلسه را وارد کن.")
                    else:
                        add_minute(project_id, m_date, m_title, m_content)
                        st.success("صورت‌جلسه ثبت شد.")

                st.markdown("---")
                st.markdown("#### لیست صورت‌جلسه‌های این پروژه")
                minutes_df = get_minutes(project_id)
                if minutes_df.empty:
                    st.info("صورت‌جلسه‌ای برای این پروژه ثبت نشده.")
                else:
                    for _, row in minutes_df.iterrows():
                        with st.expander(f"{row['meeting_date']} - {row['title']}"):
                            st.write(row["content"])

                            st.markdown("**کامنت‌ها:**")
                            m_comments = get_minute_comments(row["id"])
                            if m_comments.empty:
                                st.info("کامنتی برای این صورت‌جلسه ثبت نشده.")
                            else:
                                for _, c in m_comments.iterrows():
                                    st.markdown(f"- **{c['author'] or 'ناشناس'}** ({c['created_at']}): {c['content']}")

if __name__ == "__main__":
    main()


