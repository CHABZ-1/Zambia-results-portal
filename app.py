import os
import csv
import io
import sqlite3
from datetime import datetime, timedelta
from functools import wraps

import bcrypt
from flask import (
    Flask,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
    flash,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mkushi-boarding-zafika-secret-2026")
DB_PATH = os.environ.get("DATABASE_PATH", "zafika_mkushi.db")
SCHOOL_NAME = "Mkushi Boarding Secondary School"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def compute_grade_letter(score: int) -> str:
    if score >= 75:
        return "A"
    if score >= 60:
        return "B"
    if score >= 50:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def normalize_phone(raw: str) -> str:
    digits = "".join(ch for ch in raw if ch.isdigit() or ch == "+")
    if digits.startswith("+260") and len(digits) >= 13:
        return "0" + digits[4:]
    if digits.startswith("260") and len(digits) >= 12:
        return "0" + digits[3:]
    return digits.replace("+", "")


def send_sms(phone: str, message: str, pupil_id=None):
    """
    Demo SMS Gateway: saves to sms_log table with status 'sent' and prints to console.
    No daily limit.

    REAL INTEGRATION (Africa's Talking / Zamtel API):
    # import africastalking
    # africastalking.initialize(os.environ["AT_USERNAME"], os.environ["AT_API_KEY"])
    # africastalking.SMS.send(message, [phone])
    """
    db = get_db()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    status = "sent" if phone and len(phone) >= 9 else "failed"
    print(f"[MKUSHI SMS GATEWAY] To: {phone} | Status: {status} | Message: {message}")
    db.execute(
        "INSERT INTO sms_log (to_phone, message, pupil_id, status, time) VALUES (?, ?, ?, ?, ?)",
        (phone, message, pupil_id, status, now),
    )
    db.commit()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS pupils (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            grade TEXT NOT NULL,
            parent_name TEXT NOT NULL,
            parent_phone TEXT NOT NULL,
            parent_phone_last4 TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pupil_id INTEGER NOT NULL,
            term TEXT NOT NULL,
            subject_id INTEGER NOT NULL,
            score INTEGER NOT NULL,
            grade_letter TEXT NOT NULL,
            teacher_comment TEXT NOT NULL DEFAULT '',
            teacher_suggestion TEXT NOT NULL DEFAULT '',
            published INTEGER NOT NULL DEFAULT 0,
            published_by TEXT,
            published_at TEXT,
            date TEXT NOT NULL,
            UNIQUE(pupil_id, term, subject_id)
        );
        CREATE TABLE IF NOT EXISTS term_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pupil_id INTEGER NOT NULL,
            term TEXT NOT NULL,
            general_comment TEXT NOT NULL DEFAULT '',
            updated_by TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(pupil_id, term)
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'teacher',
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TEXT
        );
        CREATE TABLE IF NOT EXISTS sms_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            to_phone TEXT NOT NULL,
            message TEXT NOT NULL,
            pupil_id INTEGER,
            status TEXT NOT NULL,
            time TEXT NOT NULL
        );
        """
    )

    if db.execute("SELECT COUNT(*) FROM users WHERE username='MKBSS'").fetchone()[0] == 0:
        pw_hash = bcrypt.hashpw(b"MKBSS/100", bcrypt.gensalt()).decode("utf-8")
        db.execute(
            "INSERT INTO users (username, password_hash, role, failed_attempts) VALUES (?, ?, 'admin', 0)",
            ("MKBSS", pw_hash),
        )

    if db.execute("SELECT COUNT(*) FROM subjects").fetchone()[0] == 0:
        for subj in ["Mathematics", "English", "Science", "Social Studies"]:
            db.execute("INSERT INTO subjects (name) VALUES (?)", (subj,))

    db.commit()
    db.close()


def login_required(role):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if session.get("role") != role:
                return redirect(url_for("login", role=role))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


@app.route("/")
def index():
    return render_template("index.html", school_name=SCHOOL_NAME)


@app.route("/login", methods=["GET", "POST"])
def login():
    active_role = request.args.get("role", "parent")
    db = get_db()
    grades = [r["grade"] for r in db.execute("SELECT DISTINCT grade FROM pupils ORDER BY grade").fetchall()]

    if request.method == "POST":
        role = request.form.get("role", "parent")
        active_role = role

        if role in ("teacher", "admin"):
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").encode("utf-8")
            user = db.execute(
                "SELECT * FROM users WHERE LOWER(username) = LOWER(?) AND role = ?",
                (username, role),
            ).fetchone()
            if not user:
                flash(f"Invalid {role} credentials.", "danger")
                return render_template("login.html", active_role=active_role, grades=grades, school_name=SCHOOL_NAME)

            if user["failed_attempts"] >= 5 and user["locked_until"]:
                locked_until = datetime.fromisoformat(user["locked_until"])
                if datetime.utcnow() < locked_until:
                    flash("Account locked due to 5 failed attempts. Try again in 15 minutes.", "danger")
                    return render_template("login.html", active_role=active_role, grades=grades, school_name=SCHOOL_NAME)
                db.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (user["id"],))
                db.commit()

            if not bcrypt.checkpw(password, user["password_hash"].encode("utf-8")):
                fails = user["failed_attempts"] + 1
                lock_ts = (datetime.utcnow() + timedelta(minutes=15)).isoformat() if fails >= 5 else None
                db.execute("UPDATE users SET failed_attempts = ?, locked_until = ? WHERE id = ?", (fails, lock_ts, user["id"]))
                db.commit()
                flash(
                    "Too many failed attempts (5/5). Account locked."
                    if fails >= 5
                    else f"Invalid password. {5 - fails} attempt(s) remaining.",
                    "danger",
                )
                return render_template("login.html", active_role=active_role, grades=grades, school_name=SCHOOL_NAME)

            db.execute("UPDATE users SET failed_attempts = 0, locked_until = NULL WHERE id = ?", (user["id"],))
            db.commit()
            session.clear()
            session["role"] = role
            session["username"] = user["username"]
            return redirect(url_for("admin_panel" if role == "admin" else "teacher_dashboard"))

        if role == "parent":
            child_name = request.form.get("child_name", "").strip()
            grade = request.form.get("grade", "").strip()
            phone = normalize_phone(request.form.get("parent_phone", "").strip())
            pupil = db.execute(
                "SELECT * FROM pupils WHERE LOWER(TRIM(full_name)) = LOWER(?) AND LOWER(TRIM(grade)) = LOWER(?)",
                (child_name, grade),
            ).fetchone()
            if not pupil or normalize_phone(pupil["parent_phone"]) != phone:
                flash("No matching pupil found for that name, grade, and parent phone.", "danger")
                return render_template("login.html", active_role="parent", grades=grades, school_name=SCHOOL_NAME)
            session.clear()
            session["role"] = "parent"
            session["pupil_id"] = pupil["id"]
            session["parent_phone"] = pupil["parent_phone"]
            return redirect(url_for("parent_dashboard"))

        if role == "pupil":
            child_name = request.form.get("child_name", "").strip()
            grade_level = request.form.get("grade_level", "").strip()
            class_sec = request.form.get("class_section", "").strip()
            full_grade = f"{grade_level}{class_sec}"
            pupil = db.execute(
                "SELECT * FROM pupils WHERE LOWER(TRIM(full_name)) = LOWER(?) AND LOWER(TRIM(grade)) = LOWER(?)",
                (child_name, full_grade),
            ).fetchone()
            if not pupil:
                flash("No pupil record found for that name, grade, and class.", "danger")
                return render_template("login.html", active_role="pupil", grades=grades, school_name=SCHOOL_NAME)
            session.clear()
            session["role"] = "pupil"
            session["pupil_id"] = pupil["id"]
            return redirect(url_for("pupil_dashboard"))

    return render_template("login.html", active_role=active_role, grades=grades, school_name=SCHOOL_NAME)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/parent/dashboard")
@login_required("parent")
def parent_dashboard():
    db = get_db()
    pupil_id = session["pupil_id"]
    pupil = db.execute("SELECT * FROM pupils WHERE id = ?", (pupil_id,)).fetchone()
    results = db.execute(
        """SELECT r.*, s.name AS subject_name
           FROM results r JOIN subjects s ON s.id = r.subject_id
           WHERE r.pupil_id = ? AND r.published = 1
           ORDER BY r.term, s.name""",
        (pupil_id,),
    ).fetchall()
    latest_sms = db.execute(
        "SELECT * FROM sms_log WHERE pupil_id = ? AND status = 'sent' ORDER BY id DESC LIMIT 1",
        (pupil_id,),
    ).fetchone()
    return render_template("parent_dashboard.html", pupil=pupil, results=results, latest_sms=latest_sms, school_name=SCHOOL_NAME)


@app.route("/pupil/dashboard")
@login_required("pupil")
def pupil_dashboard():
    db = get_db()
    pupil_id = session["pupil_id"]
    pupil = db.execute("SELECT id, full_name, grade FROM pupils WHERE id = ?", (pupil_id,)).fetchone()
    results = db.execute(
        """SELECT r.*, s.name AS subject_name
           FROM results r JOIN subjects s ON s.id = r.subject_id
           WHERE r.pupil_id = ? AND r.published = 1
           ORDER BY r.term, s.name""",
        (pupil_id,),
    ).fetchall()
    has_grade_a = any(r["grade_letter"] == "A" for r in results)
    return render_template("pupil_dashboard.html", pupil=pupil, results=results, has_grade_a=has_grade_a, school_name=SCHOOL_NAME)


@app.route("/teacher/dashboard")
@login_required("teacher")
def teacher_dashboard():
    db = get_db()
    total_pupils = db.execute("SELECT COUNT(*) FROM pupils").fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM results WHERE published = 0").fetchone()[0]
    today = datetime.utcnow().strftime("%Y-%m-%d")
    sms_today = db.execute("SELECT COUNT(*) FROM sms_log WHERE status='sent' AND substr(time,1,10)=?", (today,)).fetchone()[0]
    return render_template("teacher_dashboard.html", total_pupils=total_pupils, pending=pending, sms_today=sms_today, school_name=SCHOOL_NAME)


@app.route("/teacher/pupils", methods=["GET", "POST"])
@login_required("teacher")
def teacher_pupils():
    db = get_db()
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        grade = request.form.get("grade", "").strip()
        parent_name = request.form.get("parent_name", "").strip()
        parent_phone = normalize_phone(request.form.get("parent_phone", "").strip())
        if full_name and grade and parent_name and len(parent_phone) >= 9:
            db.execute(
                "INSERT INTO pupils (full_name, grade, parent_name, parent_phone, parent_phone_last4) VALUES (?, ?, ?, ?, ?)",
                (full_name, grade, parent_name, parent_phone, parent_phone[-4:]),
            )
            db.commit()
            flash(f"Added {full_name} ({grade}).", "success")
    q = request.args.get("q", "").strip()
    pupils = db.execute(
        "SELECT * FROM pupils WHERE LOWER(full_name) LIKE LOWER(?) ORDER BY grade, full_name",
        (f"%{q}%",),
    ).fetchall()
    return render_template("teacher_pupils.html", pupils=pupils, q=q, school_name=SCHOOL_NAME)


@app.route("/teacher/pupil/<int:pupil_id>", methods=["GET", "POST"])
@login_required("teacher")
def teacher_pupil_detail(pupil_id):
    db = get_db()
    if request.method == "POST":
        term = request.form.get("term")
        comment = request.form.get("general_comment", "").strip()
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        db.execute(
            """INSERT INTO term_comments (pupil_id, term, general_comment, updated_by, updated_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(pupil_id, term) DO UPDATE SET general_comment=excluded.general_comment, updated_at=excluded.updated_at""",
            (pupil_id, term, comment, session.get("username", "teacher"), now),
        )
        db.commit()
        flash(f"Saved general comment for {term}.", "success")
    pupil = db.execute("SELECT * FROM pupils WHERE id = ?", (pupil_id,)).fetchone()
    results = db.execute(
        "SELECT r.*, s.name AS subject_name FROM results r JOIN subjects s ON s.id = r.subject_id WHERE r.pupil_id = ? ORDER BY r.term, s.name",
        (pupil_id,),
    ).fetchall()
    return render_template("teacher_pupil_detail.html", pupil=pupil, results=results, school_name=SCHOOL_NAME)


@app.route("/teacher/upload", methods=["GET", "POST"])
@login_required("teacher")
def teacher_upload():
    db = get_db()
    grade = request.values.get("grade", "Grade 10A")
    term = request.values.get("term", "Term2")
    subject_id = int(request.values.get("subject_id", 1))
    subjects = db.execute("SELECT * FROM subjects ORDER BY id").fetchall()
    pupils = db.execute("SELECT * FROM pupils WHERE grade = ? ORDER BY full_name", (grade,)).fetchall()

    if request.method == "POST":
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        csv_file = request.files.get("csv_file")
        if csv_file and csv_file.filename:
            stream = io.StringIO(csv_file.stream.read().decode("utf-8"))
            reader = csv.reader(stream)
            pupil_map = {p["full_name"].strip().lower(): p["id"] for p in pupils}
            saved = 0
            for idx, row in enumerate(reader):
                if len(row) < 2:
                    continue
                if idx == 0 and row[0].strip().lower() == "name":
                    continue
                pid = pupil_map.get(row[0].strip().lower())
                if not pid:
                    continue
                score = max(0, min(100, int(float(row[1]))))
                comment = row[2].strip() if len(row) > 2 else ""
                suggestion = row[3].strip() if len(row) > 3 else "Practice 20 minutes daily at home."
                db.execute(
                    """INSERT INTO results (pupil_id, term, subject_id, score, grade_letter, teacher_comment, teacher_suggestion, published, date)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
                       ON CONFLICT(pupil_id, term, subject_id) DO UPDATE SET
                       score=excluded.score, grade_letter=excluded.grade_letter, teacher_comment=excluded.teacher_comment,
                       teacher_suggestion=excluded.teacher_suggestion, published=0, date=excluded.date""",
                    (pid, term, subject_id, score, compute_grade_letter(score), comment, suggestion, now),
                )
                saved += 1
            db.commit()
            flash(f"Imported {saved} CSV draft results.", "success")
        else:
            saved = 0
            for p in pupils:
                raw_score = request.form.get(f"score_{p['id']}", "").strip()
                if not raw_score:
                    continue
                score = max(0, min(100, int(raw_score)))
                comment = request.form.get(f"comment_{p['id']}", "").strip()
                suggestion = request.form.get(f"suggestion_{p['id']}", "").strip()
                db.execute(
                    """INSERT INTO results (pupil_id, term, subject_id, score, grade_letter, teacher_comment, teacher_suggestion, published, date)
                       VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?)
                       ON CONFLICT(pupil_id, term, subject_id) DO UPDATE SET
                       score=excluded.score, grade_letter=excluded.grade_letter, teacher_comment=excluded.teacher_comment,
                       teacher_suggestion=excluded.teacher_suggestion, published=0, date=excluded.date""",
                    (p["id"], term, subject_id, score, compute_grade_letter(score), comment, suggestion, now),
                )
                saved += 1
            db.commit()
            flash(f"Saved {saved} draft results.", "success")

    return render_template("teacher_upload.html", grade=grade, term=term, subject_id=subject_id, subjects=subjects, pupils=pupils, school_name=SCHOOL_NAME)


@app.route("/teacher/publish", methods=["GET", "POST"])
@login_required("teacher")
def teacher_publish():
    db = get_db()
    term = request.values.get("term", "Term2")
    grade = request.values.get("grade", "Grade 10A")

    if request.method == "POST":
        ids = [int(i) for i in request.form.getlist("result_ids")]
        if ids:
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            placeholders = ",".join("?" for _ in ids)
            rows = db.execute(
                f"""SELECT r.*, p.full_name, p.grade, p.parent_name, p.parent_phone, s.name AS subject_name
                    FROM results r JOIN pupils p ON p.id=r.pupil_id JOIN subjects s ON s.id=r.subject_id
                    WHERE r.id IN ({placeholders})""",
                ids,
            ).fetchall()
            db.execute(
                f"UPDATE results SET published=1, published_by=?, published_at=? WHERE id IN ({placeholders})",
                [session.get("username", "teacher"), now, *ids],
            )
            db.commit()

            by_pupil = {}
            for r in rows:
                by_pupil.setdefault(r["pupil_id"], []).append(r)
            for pid, p_rows in by_pupil.items():
                first = p_rows[0]
                msg = (
                    f"Hello {first['parent_name']}, results for {first['full_name']} {first['grade']} {first['term']} are ready. "
                    f"Math: {first['score']}%, Comment: {first['teacher_comment']}. Check: https://your-school.com - {SCHOOL_NAME}"
                )
                send_sms(first["parent_phone"], msg, pid)
            flash(f"Published {len(rows)} results, SMS sent to {len(by_pupil)} parents", "success")

    results = db.execute(
        """SELECT r.*, p.full_name, p.parent_phone, s.name AS subject_name
           FROM results r JOIN pupils p ON p.id=r.pupil_id JOIN subjects s ON s.id=r.subject_id
           WHERE r.term=? AND p.grade=? ORDER BY r.published, p.full_name""",
        (term, grade),
    ).fetchall()
    return render_template("teacher_publish.html", term=term, grade=grade, results=results, school_name=SCHOOL_NAME)


@app.route("/admin/panel", methods=["GET", "POST"])
@login_required("admin")
def admin_panel():
    db = get_db()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "add_teacher":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if username and len(password) >= 4:
                exists = db.execute("SELECT id FROM users WHERE LOWER(username)=LOWER(?)", (username,)).fetchone()
                if exists:
                    flash("Username already exists.", "danger")
                else:
                    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                    db.execute("INSERT INTO users (username, password_hash, role, failed_attempts) VALUES (?, ?, 'teacher', 0)", (username, pw_hash))
                    db.commit()
                    flash(f"Created teacher account {username}.", "success")
        elif action == "add_pupil":
            full_name = request.form.get("full_name", "").strip()
            grade = request.form.get("grade", "").strip()
            parent_name = request.form.get("parent_name", "").strip()
            parent_phone = normalize_phone(request.form.get("parent_phone", "").strip())
            if full_name and grade and parent_name and len(parent_phone) >= 9:
                db.execute(
                    "INSERT INTO pupils (full_name, grade, parent_name, parent_phone, parent_phone_last4) VALUES (?, ?, ?, ?, ?)",
                    (full_name, grade, parent_name, parent_phone, parent_phone[-4:]),
                )
                db.commit()
                flash(f"Added {full_name} ({grade}).", "success")
    teachers = db.execute("SELECT id, username, failed_attempts FROM users WHERE role='teacher' ORDER BY id DESC").fetchall()
    pupils = db.execute("SELECT * FROM pupils ORDER BY grade, full_name").fetchall()
    return render_template("admin_panel.html", teachers=teachers, pupils=pupils, school_name=SCHOOL_NAME)


@app.route("/teacher/sms-log")
@login_required("teacher")
def teacher_sms_log():
    db = get_db()
    q = request.args.get("q", "").strip()
    logs = db.execute(
        "SELECT * FROM sms_log WHERE to_phone LIKE ? OR LOWER(message) LIKE LOWER(?) ORDER BY id DESC LIMIT 200",
        (f"%{q}%", f"%{q}%"),
    ).fetchall()
    return render_template("teacher_sms_log.html", logs=logs, q=q, school_name=SCHOOL_NAME)


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.run(host="0.0.0.0", port=port, debug=False)
@app.route("/teacher/publish", methods=["GET","POST"])
...
    return render_template("teacher_publish.html", results=results, ...)
