"""
QuizNest — JEE Preparation Quiz System (Flask Backend)

Run with:
    pip install -r requirements.txt
    python app.py

Then open http://127.0.0.1:5000

First-time setup:
    python create_admin.py      # create an admin login
    python seed_jee_data.py     # load JEE subjects/topics/questions/quizzes
"""

import math
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, abort, Response
)
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "quiz_system.db"

app = Flask(__name__)
app.secret_key = "replace-this-with-a-random-secret-key-before-deploying"  # dev only

DIFFICULTIES = ("Easy", "Medium", "Hard")
OPTION_KEYS = ("A", "B", "C", "D")


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def query_db(query, args=(), one=False):
    conn = get_db()
    cur = conn.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    return (rows[0] if rows else None) if one else rows


def execute_db(query, args=()):
    conn = get_db()
    cur = conn.execute(query, args)
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def init_db():
    conn = get_db()

    # ---- existing users table (unchanged) ---------------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    existing_cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)")]
    if "is_admin" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")

    # ---- JEE question-bank schema (new) ------------------------------------
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            UNIQUE(subject_id, name)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
            topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
            question_text TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_option TEXT NOT NULL CHECK (correct_option IN ('A','B','C','D')),
            explanation TEXT,
            difficulty TEXT NOT NULL DEFAULT 'Medium' CHECK (difficulty IN ('Easy','Medium','Hard')),
            marks INTEGER NOT NULL DEFAULT 4,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL,
            is_mock INTEGER NOT NULL DEFAULT 0,
            duration_minutes INTEGER NOT NULL DEFAULT 30,
            created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
            question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
            position INTEGER NOT NULL DEFAULT 0,
            UNIQUE(quiz_id, question_id)
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            quiz_id INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
            started_at TEXT NOT NULL,
            submitted_at TEXT,
            score REAL,
            total_marks REAL,
            status TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN ('in_progress','submitted'))
        )
        """
    )

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS attempt_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id INTEGER NOT NULL REFERENCES attempts(id) ON DELETE CASCADE,
            question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
            selected_option TEXT CHECK (selected_option IN ('A','B','C','D')),
            is_correct INTEGER NOT NULL DEFAULT 0,
            marks_awarded REAL NOT NULL DEFAULT 0,
            UNIQUE(attempt_id, question_id)
        )
        """
    )

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Auth helpers / decorators
# ---------------------------------------------------------------------------
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access your dashboard.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in as an admin to view this page.", "warning")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Public pages
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not full_name or not email or not password:
            flash("Please fill in all fields.", "danger")
            return redirect(url_for("register"))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password should be at least 6 characters.", "danger")
            return redirect(url_for("register"))

        existing = query_db("SELECT id FROM users WHERE email = ?", (email,), one=True)
        if existing:
            flash("An account with that email already exists. Please log in.", "warning")
            return redirect(url_for("login"))

        execute_db(
            "INSERT INTO users (full_name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (full_name, email, generate_password_hash(password), now_iso()),
        )
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = query_db("SELECT * FROM users WHERE email = ?", (email,), one=True)

        if user and check_password_hash(user["password_hash"], password):
            if user["is_admin"]:
                flash("This is an admin account. Please use the Admin Login page.", "warning")
                return redirect(url_for("admin_login"))

            session["user_id"] = user["id"]
            session["full_name"] = user["full_name"]
            flash(f"Welcome back, {user['full_name']}!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.", "danger")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# Student dashboard
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]

    attempts = query_db(
        "SELECT status, score, total_marks FROM attempts WHERE user_id = ? AND status = 'submitted'",
        (user_id,),
    )
    quizzes_taken = len(attempts)
    if quizzes_taken:
        pct_list = [
            (a["score"] / a["total_marks"] * 100) if a["total_marks"] else 0
            for a in attempts
        ]
        avg_score = round(sum(pct_list) / len(pct_list), 1)
    else:
        avg_score = 0

    subjects = query_db("SELECT * FROM subjects ORDER BY id")
    recent_attempts = query_db(
        """
        SELECT a.id, a.score, a.total_marks, a.submitted_at, q.title
        FROM attempts a JOIN quizzes q ON q.id = a.quiz_id
        WHERE a.user_id = ? AND a.status = 'submitted'
        ORDER BY a.submitted_at DESC LIMIT 5
        """,
        (user_id,),
    )

    return render_template(
        "dashboard.html",
        full_name=session.get("full_name"),
        quizzes_taken=quizzes_taken,
        avg_score=avg_score,
        subjects=subjects,
        recent_attempts=recent_attempts,
    )


# ---------------------------------------------------------------------------
# Admin auth
# ---------------------------------------------------------------------------
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = query_db(
            "SELECT * FROM users WHERE email = ? AND is_admin = 1", (email,), one=True
        )

        if user and check_password_hash(user["password_hash"], password):
            session["admin_id"] = user["id"]
            session["admin_name"] = user["full_name"]
            flash(f"Welcome back, {user['full_name']}.", "success")
            return redirect(url_for("admin_dashboard"))

        flash("Invalid admin credentials.", "danger")
        return redirect(url_for("admin_login"))

    return render_template("admin_login.html")


@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_id", None)
    session.pop("admin_name", None)
    flash("Admin logged out.", "info")
    return redirect(url_for("home"))


@app.route("/admin/dashboard")
@admin_required
def admin_dashboard():
    students = query_db(
        "SELECT id, full_name, email, created_at FROM users WHERE is_admin = 0 ORDER BY created_at DESC"
    )
    total_admins = query_db("SELECT COUNT(*) AS c FROM users WHERE is_admin = 1", one=True)["c"]

    per_subject = []
    for subj in query_db("SELECT * FROM subjects ORDER BY id"):
        per_subject.append(
            {
                "name": subj["name"],
                "topics": query_db(
                    "SELECT COUNT(*) c FROM topics WHERE subject_id = ?", (subj["id"],), one=True
                )["c"],
                "questions": query_db(
                    "SELECT COUNT(*) c FROM questions WHERE subject_id = ?", (subj["id"],), one=True
                )["c"],
            }
        )

    total_questions = query_db("SELECT COUNT(*) c FROM questions", one=True)["c"]
    total_quizzes = query_db("SELECT COUNT(*) c FROM quizzes", one=True)["c"]
    total_topics = query_db("SELECT COUNT(*) c FROM topics", one=True)["c"]
    total_attempts = query_db(
        "SELECT COUNT(*) c FROM attempts WHERE status = 'submitted'", one=True
    )["c"]

    recent_results = query_db(
        """
        SELECT a.id, a.score, a.total_marks, a.submitted_at, u.full_name, q.title
        FROM attempts a
        JOIN users u ON u.id = a.user_id
        JOIN quizzes q ON q.id = a.quiz_id
        WHERE a.status = 'submitted'
        ORDER BY a.submitted_at DESC LIMIT 8
        """
    )

    return render_template(
        "admin_dashboard.html",
        admin_name=session.get("admin_name"),
        students=students,
        total_students=len(students),
        total_admins=total_admins,
        per_subject=per_subject,
        total_questions=total_questions,
        total_quizzes=total_quizzes,
        total_topics=total_topics,
        total_attempts=total_attempts,
        recent_results=recent_results,
    )


# ---------------------------------------------------------------------------
# Admin — Subjects & Topics
# ---------------------------------------------------------------------------
@app.route("/admin/content")
@admin_required
def admin_content():
    subjects = query_db("SELECT * FROM subjects ORDER BY name")
    topics_by_subject = {}
    for s in subjects:
        topics_by_subject[s["id"]] = query_db(
            "SELECT * FROM topics WHERE subject_id = ? ORDER BY name", (s["id"],)
        )
    return render_template(
        "admin_content.html",
        admin_name=session.get("admin_name"),
        subjects=subjects,
        topics_by_subject=topics_by_subject,
    )


@app.route("/admin/subjects/add", methods=["POST"])
@admin_required
def admin_subject_add():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Subject name is required.", "danger")
    else:
        try:
            execute_db("INSERT INTO subjects (name) VALUES (?)", (name,))
            flash(f"Subject '{name}' added.", "success")
        except sqlite3.IntegrityError:
            flash("That subject already exists.", "warning")
    return redirect(url_for("admin_content"))


@app.route("/admin/subjects/<int:subject_id>/edit", methods=["POST"])
@admin_required
def admin_subject_edit(subject_id):
    name = request.form.get("name", "").strip()
    if not name:
        flash("Subject name is required.", "danger")
    else:
        try:
            execute_db("UPDATE subjects SET name = ? WHERE id = ?", (name, subject_id))
            flash("Subject updated.", "success")
        except sqlite3.IntegrityError:
            flash("Another subject already has that name.", "warning")
    return redirect(url_for("admin_content"))


@app.route("/admin/subjects/<int:subject_id>/delete", methods=["POST"])
@admin_required
def admin_subject_delete(subject_id):
    execute_db("DELETE FROM subjects WHERE id = ?", (subject_id,))
    flash("Subject and its topics/questions were deleted.", "info")
    return redirect(url_for("admin_content"))


@app.route("/admin/topics/add", methods=["POST"])
@admin_required
def admin_topic_add():
    subject_id = request.form.get("subject_id", type=int)
    name = request.form.get("name", "").strip()
    if not subject_id or not name:
        flash("Subject and topic name are required.", "danger")
    else:
        try:
            execute_db(
                "INSERT INTO topics (subject_id, name) VALUES (?, ?)", (subject_id, name)
            )
            flash(f"Topic '{name}' added.", "success")
        except sqlite3.IntegrityError:
            flash("That topic already exists for this subject.", "warning")
    return redirect(url_for("admin_content"))


@app.route("/admin/topics/<int:topic_id>/edit", methods=["POST"])
@admin_required
def admin_topic_edit(topic_id):
    name = request.form.get("name", "").strip()
    if not name:
        flash("Topic name is required.", "danger")
    else:
        execute_db("UPDATE topics SET name = ? WHERE id = ?", (name, topic_id))
        flash("Topic updated.", "success")
    return redirect(url_for("admin_content"))


@app.route("/admin/topics/<int:topic_id>/delete", methods=["POST"])
@admin_required
def admin_topic_delete(topic_id):
    execute_db("DELETE FROM topics WHERE id = ?", (topic_id,))
    flash("Topic and its questions were deleted.", "info")
    return redirect(url_for("admin_content"))


# ---------------------------------------------------------------------------
# Admin — Questions
# ---------------------------------------------------------------------------
@app.route("/admin/questions")
@admin_required
def admin_questions():
    subject_id = request.args.get("subject_id", type=int)
    topic_id = request.args.get("topic_id", type=int)

    sql = """
        SELECT q.*, s.name AS subject_name, t.name AS topic_name
        FROM questions q
        JOIN subjects s ON s.id = q.subject_id
        JOIN topics t ON t.id = q.topic_id
        WHERE 1=1
    """
    args = []
    if subject_id:
        sql += " AND q.subject_id = ?"
        args.append(subject_id)
    if topic_id:
        sql += " AND q.topic_id = ?"
        args.append(topic_id)
    sql += " ORDER BY q.id DESC"

    questions = query_db(sql, tuple(args))
    subjects = query_db("SELECT * FROM subjects ORDER BY name")
    topics = query_db("SELECT * FROM topics ORDER BY name") if not subject_id else query_db(
        "SELECT * FROM topics WHERE subject_id = ? ORDER BY name", (subject_id,)
    )

    return render_template(
        "admin_questions.html",
        admin_name=session.get("admin_name"),
        questions=questions,
        subjects=subjects,
        topics=topics,
        selected_subject=subject_id,
        selected_topic=topic_id,
    )


def _question_form_context(subject_id=None):
    subjects = query_db("SELECT * FROM subjects ORDER BY name")
    topics = query_db(
        "SELECT * FROM topics WHERE subject_id = ? ORDER BY name", (subject_id,)
    ) if subject_id else []
    return subjects, topics


@app.route("/admin/questions/add", methods=["GET", "POST"])
@admin_required
def admin_question_add():
    if request.method == "POST":
        ok, err = _save_question_from_form()
        if ok:
            flash("Question added.", "success")
            return redirect(url_for("admin_questions"))
        flash(err, "danger")

    subject_id = request.args.get("subject_id", type=int) or request.form.get("subject_id", type=int)
    subjects, topics = _question_form_context(subject_id)
    return render_template(
        "admin_question_form.html",
        admin_name=session.get("admin_name"),
        subjects=subjects,
        topics=topics,
        difficulties=DIFFICULTIES,
        question=None,
        form=request.form,
    )


@app.route("/admin/questions/<int:question_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_question_edit(question_id):
    question = query_db("SELECT * FROM questions WHERE id = ?", (question_id,), one=True)
    if not question:
        abort(404)

    if request.method == "POST":
        ok, err = _save_question_from_form(question_id=question_id)
        if ok:
            flash("Question updated.", "success")
            return redirect(url_for("admin_questions"))
        flash(err, "danger")

    subject_id = request.form.get("subject_id", type=int) or question["subject_id"]
    subjects, topics = _question_form_context(subject_id)
    return render_template(
        "admin_question_form.html",
        admin_name=session.get("admin_name"),
        subjects=subjects,
        topics=topics,
        difficulties=DIFFICULTIES,
        question=question,
        form=request.form if request.method == "POST" else question,
    )


def _save_question_from_form(question_id=None):
    subject_id = request.form.get("subject_id", type=int)
    topic_id = request.form.get("topic_id", type=int)
    question_text = request.form.get("question_text", "").strip()
    option_a = request.form.get("option_a", "").strip()
    option_b = request.form.get("option_b", "").strip()
    option_c = request.form.get("option_c", "").strip()
    option_d = request.form.get("option_d", "").strip()
    correct_option = request.form.get("correct_option", "").strip().upper()
    explanation = request.form.get("explanation", "").strip()
    difficulty = request.form.get("difficulty", "Medium")
    marks = request.form.get("marks", type=int) or 4

    if not all([subject_id, topic_id, question_text, option_a, option_b, option_c, option_d]):
        return False, "Please fill in the question, subject, topic and all 4 options."
    if correct_option not in OPTION_KEYS:
        return False, "Please select which option (A/B/C/D) is correct."
    if difficulty not in DIFFICULTIES:
        difficulty = "Medium"

    topic = query_db("SELECT * FROM topics WHERE id = ?", (topic_id,), one=True)
    if not topic or topic["subject_id"] != subject_id:
        return False, "Selected topic does not belong to the selected subject."

    if question_id:
        execute_db(
            """
            UPDATE questions
            SET subject_id=?, topic_id=?, question_text=?, option_a=?, option_b=?,
                option_c=?, option_d=?, correct_option=?, explanation=?, difficulty=?, marks=?
            WHERE id=?
            """,
            (subject_id, topic_id, question_text, option_a, option_b, option_c, option_d,
             correct_option, explanation, difficulty, marks, question_id),
        )
    else:
        execute_db(
            """
            INSERT INTO questions
                (subject_id, topic_id, question_text, option_a, option_b, option_c, option_d,
                 correct_option, explanation, difficulty, marks, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (subject_id, topic_id, question_text, option_a, option_b, option_c, option_d,
             correct_option, explanation, difficulty, marks, now_iso()),
        )
    return True, None


@app.route("/admin/questions/<int:question_id>/delete", methods=["POST"])
@admin_required
def admin_question_delete(question_id):
    execute_db("DELETE FROM questions WHERE id = ?", (question_id,))
    flash("Question deleted.", "info")
    return redirect(url_for("admin_questions"))


# ---------------------------------------------------------------------------
# Admin — Quizzes
# ---------------------------------------------------------------------------
@app.route("/admin/quizzes")
@admin_required
def admin_quizzes():
    quizzes = query_db(
        """
        SELECT z.*, s.name AS subject_name, t.name AS topic_name,
               (SELECT COUNT(*) FROM quiz_questions qq WHERE qq.quiz_id = z.id) AS question_count
        FROM quizzes z
        LEFT JOIN subjects s ON s.id = z.subject_id
        LEFT JOIN topics t ON t.id = z.topic_id
        ORDER BY z.id DESC
        """
    )
    return render_template(
        "admin_quizzes.html", admin_name=session.get("admin_name"), quizzes=quizzes
    )


@app.route("/admin/quizzes/add", methods=["GET", "POST"])
@admin_required
def admin_quiz_add():
    if request.method == "POST":
        ok, err, quiz_id = _save_quiz_from_form()
        if ok:
            flash("Quiz created. Now add questions to it.", "success")
            return redirect(url_for("admin_quiz_builder", quiz_id=quiz_id))
        flash(err, "danger")

    subjects = query_db("SELECT * FROM subjects ORDER BY name")
    subject_id = request.form.get("subject_id", type=int)
    topics = query_db(
        "SELECT * FROM topics WHERE subject_id = ? ORDER BY name", (subject_id,)
    ) if subject_id else []
    return render_template(
        "admin_quiz_form.html",
        admin_name=session.get("admin_name"),
        subjects=subjects,
        topics=topics,
        quiz=None,
        form=request.form,
    )


@app.route("/admin/quizzes/<int:quiz_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_quiz_edit(quiz_id):
    quiz = query_db("SELECT * FROM quizzes WHERE id = ?", (quiz_id,), one=True)
    if not quiz:
        abort(404)

    if request.method == "POST":
        ok, err, _ = _save_quiz_from_form(quiz_id=quiz_id)
        if ok:
            flash("Quiz updated.", "success")
            return redirect(url_for("admin_quizzes"))
        flash(err, "danger")

    subjects = query_db("SELECT * FROM subjects ORDER BY name")
    subject_id = request.form.get("subject_id", type=int) or quiz["subject_id"]
    topics = query_db(
        "SELECT * FROM topics WHERE subject_id = ? ORDER BY name", (subject_id,)
    ) if subject_id else []
    return render_template(
        "admin_quiz_form.html",
        admin_name=session.get("admin_name"),
        subjects=subjects,
        topics=topics,
        quiz=quiz,
        form=request.form if request.method == "POST" else dict(quiz),
    )


def _save_quiz_from_form(quiz_id=None):
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    subject_id = request.form.get("subject_id", type=int) or None
    topic_id = request.form.get("topic_id", type=int) or None
    is_mock = 1 if request.form.get("is_mock") == "on" else 0
    duration_minutes = request.form.get("duration_minutes", type=int) or 30

    if not title:
        return False, "Quiz title is required.", None
    if duration_minutes < 1:
        return False, "Duration must be at least 1 minute.", None
    if is_mock:
        topic_id = None  # mock tests span a whole subject / the full syllabus

    if quiz_id:
        execute_db(
            """
            UPDATE quizzes
            SET title=?, description=?, subject_id=?, topic_id=?, is_mock=?, duration_minutes=?
            WHERE id=?
            """,
            (title, description, subject_id, topic_id, is_mock, duration_minutes, quiz_id),
        )
        return True, None, quiz_id
    else:
        new_id = execute_db(
            """
            INSERT INTO quizzes
                (title, description, subject_id, topic_id, is_mock, duration_minutes, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, description, subject_id, topic_id, is_mock, duration_minutes,
             session.get("admin_id"), now_iso()),
        )
        return True, None, new_id


@app.route("/admin/quizzes/<int:quiz_id>/delete", methods=["POST"])
@admin_required
def admin_quiz_delete(quiz_id):
    execute_db("DELETE FROM quizzes WHERE id = ?", (quiz_id,))
    flash("Quiz deleted.", "info")
    return redirect(url_for("admin_quizzes"))


@app.route("/admin/quizzes/<int:quiz_id>/builder")
@admin_required
def admin_quiz_builder(quiz_id):
    quiz = query_db("SELECT * FROM quizzes WHERE id = ?", (quiz_id,), one=True)
    if not quiz:
        abort(404)

    current_questions = query_db(
        """
        SELECT q.*, qq.id AS link_id
        FROM quiz_questions qq JOIN questions q ON q.id = qq.question_id
        WHERE qq.quiz_id = ?
        ORDER BY qq.position, qq.id
        """,
        (quiz_id,),
    )
    current_ids = {q["id"] for q in current_questions}

    filter_subject = request.args.get("subject_id", type=int) or quiz["subject_id"]
    filter_topic = request.args.get("topic_id", type=int) or quiz["topic_id"]

    sql = ("SELECT q.*, s.name AS subject_name, t.name AS topic_name FROM questions q "
           "JOIN subjects s ON s.id=q.subject_id JOIN topics t ON t.id=q.topic_id WHERE 1=1")
    args = []
    if filter_subject:
        sql += " AND q.subject_id = ?"
        args.append(filter_subject)
    if filter_topic:
        sql += " AND q.topic_id = ?"
        args.append(filter_topic)
    sql += " ORDER BY q.id DESC"
    available_questions = [q for q in query_db(sql, tuple(args)) if q["id"] not in current_ids]

    subjects = query_db("SELECT * FROM subjects ORDER BY name")
    topics = query_db(
        "SELECT * FROM topics WHERE subject_id = ? ORDER BY name", (filter_subject,)
    ) if filter_subject else query_db("SELECT * FROM topics ORDER BY name")

    total_marks = sum(q["marks"] for q in current_questions)

    return render_template(
        "admin_quiz_builder.html",
        admin_name=session.get("admin_name"),
        quiz=quiz,
        current_questions=current_questions,
        available_questions=available_questions,
        subjects=subjects,
        topics=topics,
        selected_subject=filter_subject,
        selected_topic=filter_topic,
        total_marks=total_marks,
    )


@app.route("/admin/quizzes/<int:quiz_id>/builder/add", methods=["POST"])
@admin_required
def admin_quiz_builder_add(quiz_id):
    question_id = request.form.get("question_id", type=int)
    if question_id:
        pos = query_db(
            "SELECT COALESCE(MAX(position), 0) + 1 AS p FROM quiz_questions WHERE quiz_id = ?",
            (quiz_id,), one=True
        )["p"]
        try:
            execute_db(
                "INSERT INTO quiz_questions (quiz_id, question_id, position) VALUES (?, ?, ?)",
                (quiz_id, question_id, pos),
            )
        except sqlite3.IntegrityError:
            pass
    return redirect(url_for("admin_quiz_builder", quiz_id=quiz_id))


@app.route("/admin/quizzes/<int:quiz_id>/builder/remove", methods=["POST"])
@admin_required
def admin_quiz_builder_remove(quiz_id):
    question_id = request.form.get("question_id", type=int)
    execute_db(
        "DELETE FROM quiz_questions WHERE quiz_id = ? AND question_id = ?",
        (quiz_id, question_id),
    )
    return redirect(url_for("admin_quiz_builder", quiz_id=quiz_id))


# ---------------------------------------------------------------------------
# Admin — Results
# ---------------------------------------------------------------------------
@app.route("/admin/results")
@admin_required
def admin_results():
    attempts = query_db(
        """
        SELECT a.id, a.score, a.total_marks, a.submitted_at, a.started_at,
               u.full_name, u.email, q.title AS quiz_title
        FROM attempts a
        JOIN users u ON u.id = a.user_id
        JOIN quizzes q ON q.id = a.quiz_id
        WHERE a.status = 'submitted'
        ORDER BY a.submitted_at DESC
        """
    )
    return render_template(
        "admin_results.html", admin_name=session.get("admin_name"), attempts=attempts
    )


@app.route("/admin/results/<int:attempt_id>")
@admin_required
def admin_result_detail(attempt_id):
    attempt = query_db(
        """
        SELECT a.*, u.full_name, u.email, q.title AS quiz_title
        FROM attempts a
        JOIN users u ON u.id = a.user_id
        JOIN quizzes q ON q.id = a.quiz_id
        WHERE a.id = ?
        """,
        (attempt_id,), one=True,
    )
    if not attempt:
        abort(404)

    answers = query_db(
        """
        SELECT aa.*, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d,
               q.correct_option, q.explanation, q.marks
        FROM attempt_answers aa JOIN questions q ON q.id = aa.question_id
        WHERE aa.attempt_id = ?
        ORDER BY aa.id
        """,
        (attempt_id,),
    )
    return render_template(
        "admin_attempt_detail.html",
        admin_name=session.get("admin_name"),
        attempt=attempt,
        answers=answers,
    )


# ---------------------------------------------------------------------------
# Student — JEE preparation browsing
# ---------------------------------------------------------------------------
@app.route("/jee")
@login_required
def jee_home():
    subjects = query_db("SELECT * FROM subjects ORDER BY id")
    subject_stats = []
    for s in subjects:
        topic_count = query_db(
            "SELECT COUNT(*) c FROM topics WHERE subject_id = ?", (s["id"],), one=True
        )["c"]
        question_count = query_db(
            "SELECT COUNT(*) c FROM questions WHERE subject_id = ?", (s["id"],), one=True
        )["c"]
        subject_stats.append({"subject": s, "topics": topic_count, "questions": question_count})

    mock_tests = query_db("SELECT * FROM quizzes WHERE is_mock = 1 ORDER BY id DESC")
    return render_template("jee_home.html", subject_stats=subject_stats, mock_tests=mock_tests)


@app.route("/jee/subject/<int:subject_id>")
@login_required
def jee_subject(subject_id):
    subject = query_db("SELECT * FROM subjects WHERE id = ?", (subject_id,), one=True)
    if not subject:
        abort(404)

    topics = query_db("SELECT * FROM topics WHERE subject_id = ? ORDER BY name", (subject_id,))
    topic_stats = []
    for t in topics:
        quiz_count = query_db(
            "SELECT COUNT(*) c FROM quizzes WHERE topic_id = ?", (t["id"],), one=True
        )["c"]
        question_count = query_db(
            "SELECT COUNT(*) c FROM questions WHERE topic_id = ?", (t["id"],), one=True
        )["c"]
        topic_stats.append({"topic": t, "quizzes": quiz_count, "questions": question_count})

    subject_quizzes = query_db(
        "SELECT * FROM quizzes WHERE subject_id = ? AND topic_id IS NULL AND is_mock = 0 ORDER BY id DESC",
        (subject_id,),
    )

    return render_template(
        "jee_subject.html", subject=subject, topic_stats=topic_stats, subject_quizzes=subject_quizzes
    )


@app.route("/jee/topic/<int:topic_id>")
@login_required
def jee_topic(topic_id):
    topic = query_db(
        "SELECT t.*, s.name AS subject_name, s.id AS subject_id FROM topics t "
        "JOIN subjects s ON s.id = t.subject_id WHERE t.id = ?",
        (topic_id,), one=True,
    )
    if not topic:
        abort(404)

    quizzes = query_db(
        """
        SELECT z.*, (SELECT COUNT(*) FROM quiz_questions qq WHERE qq.quiz_id = z.id) AS question_count
        FROM quizzes z WHERE z.topic_id = ? ORDER BY z.id DESC
        """,
        (topic_id,),
    )
    return render_template("jee_topic.html", topic=topic, quizzes=quizzes)


@app.route("/jee/mock-tests")
@login_required
def jee_mock_tests():
    mock_tests = query_db(
        """
        SELECT z.*, (SELECT COUNT(*) FROM quiz_questions qq WHERE qq.quiz_id = z.id) AS question_count
        FROM quizzes z WHERE z.is_mock = 1 ORDER BY z.id DESC
        """
    )
    return render_template("jee_mock_tests.html", mock_tests=mock_tests)


@app.route("/my-results")
@login_required
def my_results():
    attempts = query_db(
        """
        SELECT a.id, a.score, a.total_marks, a.submitted_at, q.title
        FROM attempts a JOIN quizzes q ON q.id = a.quiz_id
        WHERE a.user_id = ? AND a.status = 'submitted'
        ORDER BY a.submitted_at DESC
        """,
        (session["user_id"],),
    )
    return render_template("my_results.html", attempts=attempts)


# ---------------------------------------------------------------------------
# Student — Taking a quiz
# ---------------------------------------------------------------------------
@app.route("/quiz/<int:quiz_id>/start", methods=["POST"])
@login_required
def quiz_start(quiz_id):
    quiz = query_db("SELECT * FROM quizzes WHERE id = ?", (quiz_id,), one=True)
    if not quiz:
        abort(404)

    question_count = query_db(
        "SELECT COUNT(*) c FROM quiz_questions WHERE quiz_id = ?", (quiz_id,), one=True
    )["c"]
    if question_count == 0:
        flash("This quiz has no questions yet. Please try another one.", "warning")
        return redirect(url_for("jee_home"))

    # Reuse an attempt already in progress for this quiz instead of starting a duplicate.
    existing = query_db(
        "SELECT * FROM attempts WHERE user_id = ? AND quiz_id = ? AND status = 'in_progress'",
        (session["user_id"], quiz_id), one=True,
    )
    if existing:
        return redirect(url_for("quiz_attempt", attempt_id=existing["id"]))

    attempt_id = execute_db(
        "INSERT INTO attempts (user_id, quiz_id, started_at, status) VALUES (?, ?, ?, 'in_progress')",
        (session["user_id"], quiz_id, now_iso()),
    )
    return redirect(url_for("quiz_attempt", attempt_id=attempt_id))


def _get_owned_attempt(attempt_id):
    attempt = query_db("SELECT * FROM attempts WHERE id = ?", (attempt_id,), one=True)
    if not attempt or attempt["user_id"] != session.get("user_id"):
        abort(404)
    return attempt


@app.route("/quiz/attempt/<int:attempt_id>")
@login_required
def quiz_attempt(attempt_id):
    attempt = _get_owned_attempt(attempt_id)
    if attempt["status"] == "submitted":
        return redirect(url_for("quiz_result", attempt_id=attempt_id))

    quiz = query_db("SELECT * FROM quizzes WHERE id = ?", (attempt["quiz_id"],), one=True)
    questions = query_db(
        """
        SELECT q.* FROM quiz_questions qq JOIN questions q ON q.id = qq.question_id
        WHERE qq.quiz_id = ? ORDER BY qq.position, qq.id
        """,
        (quiz["id"],),
    )

    saved = {
        row["question_id"]: row["selected_option"]
        for row in query_db(
            "SELECT question_id, selected_option FROM attempt_answers WHERE attempt_id = ?",
            (attempt_id,),
        )
    }

    started = datetime.fromisoformat(attempt["started_at"])
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    remaining = max(0, math.floor(quiz["duration_minutes"] * 60 - elapsed))

    return render_template(
        "quiz_attempt.html",
        attempt=attempt,
        quiz=quiz,
        questions=questions,
        saved=saved,
        remaining_seconds=remaining,
        option_keys=OPTION_KEYS,
    )


@app.route("/quiz/attempt/<int:attempt_id>/submit", methods=["POST"])
@login_required
def quiz_submit(attempt_id):
    attempt = _get_owned_attempt(attempt_id)
    if attempt["status"] == "submitted":
        return redirect(url_for("quiz_result", attempt_id=attempt_id))

    # Persist whatever was selected on the final screen before grading.
    for key, value in request.form.items():
        if key.startswith("answer_"):
            question_id = int(key.replace("answer_", ""))
            selected = value if value in OPTION_KEYS else None
            existing = query_db(
                "SELECT id FROM attempt_answers WHERE attempt_id = ? AND question_id = ?",
                (attempt_id, question_id), one=True,
            )
            if existing:
                execute_db(
                    "UPDATE attempt_answers SET selected_option = ? WHERE id = ?",
                    (selected, existing["id"]),
                )
            else:
                execute_db(
                    "INSERT INTO attempt_answers (attempt_id, question_id, selected_option) VALUES (?, ?, ?)",
                    (attempt_id, question_id, selected),
                )

    questions = query_db(
        """
        SELECT q.* FROM quiz_questions qq JOIN questions q ON q.id = qq.question_id
        WHERE qq.quiz_id = ?
        """,
        (attempt["quiz_id"],),
    )
    answers = {
        row["question_id"]: row["selected_option"]
        for row in query_db(
            "SELECT question_id, selected_option FROM attempt_answers WHERE attempt_id = ?",
            (attempt_id,),
        )
    }

    total_marks = 0
    score = 0
    for q in questions:
        total_marks += q["marks"]
        selected = answers.get(q["id"])
        is_correct = 1 if selected == q["correct_option"] else 0
        marks_awarded = q["marks"] if is_correct else 0
        score += marks_awarded
        if q["id"] in answers:
            execute_db(
                "UPDATE attempt_answers SET is_correct = ?, marks_awarded = ? "
                "WHERE attempt_id = ? AND question_id = ?",
                (is_correct, marks_awarded, attempt_id, q["id"]),
            )
        else:
            execute_db(
                "INSERT INTO attempt_answers "
                "(attempt_id, question_id, selected_option, is_correct, marks_awarded) "
                "VALUES (?, ?, NULL, 0, 0)",
                (attempt_id, q["id"]),
            )

    execute_db(
        "UPDATE attempts SET status='submitted', submitted_at=?, score=?, total_marks=? WHERE id=?",
        (now_iso(), score, total_marks, attempt_id),
    )
    return redirect(url_for("quiz_result", attempt_id=attempt_id))


@app.route("/quiz/attempt/<int:attempt_id>/result")
@login_required
def quiz_result(attempt_id):
    attempt = _get_owned_attempt(attempt_id)
    if attempt["status"] != "submitted":
        return redirect(url_for("quiz_attempt", attempt_id=attempt_id))

    quiz = query_db("SELECT * FROM quizzes WHERE id = ?", (attempt["quiz_id"],), one=True)
    answers = query_db(
        """
        SELECT aa.*, q.question_text, q.option_a, q.option_b, q.option_c, q.option_d,
               q.correct_option, q.explanation, q.marks, q.difficulty
        FROM attempt_answers aa JOIN questions q ON q.id = aa.question_id
        WHERE aa.attempt_id = ? ORDER BY aa.id
        """,
        (attempt_id,),
    )
    correct_count = sum(1 for a in answers if a["is_correct"])
    percentage = round((attempt["score"] / attempt["total_marks"] * 100), 1) if attempt["total_marks"] else 0

    return render_template(
        "quiz_result.html",
        attempt=attempt,
        quiz=quiz,
        answers=answers,
        correct_count=correct_count,
        total_count=len(answers),
        percentage=percentage,
    )


# ---------------------------------------------------------------------------
# Student — PDF certificate for a submitted attempt
# ---------------------------------------------------------------------------
@app.route("/quiz/attempt/<int:attempt_id>/certificate")
@login_required
def quiz_certificate(attempt_id):
    # Only the owner of the attempt can download it (404 otherwise).
    attempt = _get_owned_attempt(attempt_id)
    if attempt["status"] != "submitted" or attempt["score"] is None or not attempt["total_marks"]:
        flash("A certificate is available only after the quiz has been submitted.", "warning")
        return redirect(url_for("quiz_attempt", attempt_id=attempt_id))

    user = query_db("SELECT full_name FROM users WHERE id = ?", (attempt["user_id"],), one=True)
    quiz = query_db(
        """
        SELECT qz.title, s.name AS subject_name, t.name AS topic_name
        FROM quizzes qz
        LEFT JOIN subjects s ON s.id = qz.subject_id
        LEFT JOIN topics t ON t.id = qz.topic_id
        WHERE qz.id = ?
        """,
        (attempt["quiz_id"],), one=True,
    )
    if not user or not quiz:
        abort(404)

    from certificate import build_certificate_pdf
    pdf_bytes = build_certificate_pdf(
        student_name=user["full_name"],
        quiz_title=quiz["title"],
        subject=quiz["subject_name"],
        chapter=quiz["topic_name"],
        score=attempt["score"],
        total_marks=attempt["total_marks"],
        completed_at=attempt["submitted_at"],
    )
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="QuizNest-Certificate-{attempt_id}.pdf"',
            "Cache-Control": "private, no-store",
        },
    )


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
