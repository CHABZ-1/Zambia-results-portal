import os
import sqlite3
from flask import Flask, render_template, request, redirect, flash, session, g
from functools import wraps

app = Flask(__name__)
app.secret_key = "zafika-2026-key"
DATABASE = "zafika.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exc):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS pupils (id INTEGER PRIMARY KEY, full_name TEXT, grade TEXT, parent_phone TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS subjects (id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
    con.execute("CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY, pupil_id INTEGER, subject_id INTEGER, term TEXT, score INTEGER, comment TEXT, is_published INTEGER DEFAULT 0)")
    cur = con.execute("SELECT id FROM users WHERE username='admin'").fetchone()
    if not cur:
        con.execute("INSERT INTO users (username,password,role) VALUES ('admin','admin123','admin')")
        con.execute("INSERT INTO users (username,password,role) VALUES ('teacher','teacher123','teacher')")
    for s in ["Mathematics","English","Science","Biology"]:
        try:
            con.execute("INSERT INTO subjects (name) VALUES (?)", (s,))
        except:
            pass
    con.commit()
    con.close()

init_db()

def login_required(roles=None):
    def deco(f):
        @wraps(f)
        def wrap(*a, **kw):
            if "user_id" not in session:
                return redirect("/login")
            if roles and session.get("role") not in roles:
                return redirect("/login")
            return f(*a, **kw)
        return wrap
    return deco

@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","").strip()
        con = get_db()
        user = con.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)).fetchone()
        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            if user["role"] == "admin":
                return redirect("/admin/panel")
            return redirect("/teacher/upload")
        flash("Wrong login","error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/teacher/upload", methods=["GET","POST"])
@login_required(roles=["admin","teacher"])
def teacher_upload():
    con = get_db()
    grade = request.values.get("grade","Grade 10A")
    term = request.values.get("term","Term2")
    subjects = con.execute("SELECT * FROM subjects").fetchall()
    pupils = con.execute("SELECT * FROM pupils WHERE grade=?", (grade,)).fetchall()
    if request.method == "POST":
        grade = request.form.get("grade")
        term = request.form.get("term")
        sid = request.form.get("subject_id")
        for pu in pupils:
            sc = request.form.get("score_"+str(pu["id"]))
            if sc and sc.strip() != "":
                con.execute("INSERT OR REPLACE INTO results (pupil_id, subject_id, term, score) VALUES (?,?,?,?)", (pu["id"], sid, term, int(sc)))
        con.commit()
        flash("Saved","success")
        return redirect("/teacher/upload?grade="+grade+"&term="+term)
    return render_template("teacher_upload.html", grade=grade, term=term, subjects=subjects, pupils=pupils)

@app.route("/teacher/publish")
@login_required(roles=["admin","teacher"])
def teacher_publish():
    con = get_db()
    grade = request.values.get("grade","Grade 10A")
    term = request.values.get("term","Term2")
    progress = con.execute("SELECT s.name, COUNT(r.id) as count FROM subjects s LEFT JOIN results r ON r.subject_id=s.id AND r.term=? GROUP BY s.id", (term,)).fetchall()
    return render_template("teacher_publish.html", grade=grade, term=term, progress=progress, total_pupils=10)

@app.route("/teacher/publish-all", methods=["POST"])
@login_required(roles=["admin","teacher"])
def teacher_publish_all():
    grade = request.form.get("grade")
    term = request.form.get("term")
    con = get_db()
    con.execute("UPDATE results SET is_published=1 WHERE term=?", (term,))
    con.commit()
    flash("Published "+grade+" "+term,"success")
    return redirect("/teacher/publish?grade="+grade+"&term="+term)

@app.route("/admin/panel", methods=["GET","POST"])
@login_required(roles=["admin"])
def admin_panel():
    con = get_db()
    if request.method == "POST":
        tn = request.form.get("teacher_username") or request.form.get("username")
        tp = request.form.get("teacher_password") or request.form.get("password")
        if tn and tp:
            try:
                con.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)", (tn.strip(), tp.strip(), "teacher"))
                con.commit()
                flash("Teacher "+tn+" created","success")
            except:
                flash("Teacher exists","error")
            return redirect("/admin/panel")
        pn = request.form.get("pupil_name")
        pg = request.form.get("grade")
        if pn and pg:
            con.execute("INSERT INTO pupils (full_name,grade,parent_phone) VALUES (?,?,?)", (pn, pg, request.form.get("parent_phone")))
            con.commit()
            flash("Pupil added","success")
            return redirect("/admin/panel")
    teachers = con.execute("SELECT * FROM users WHERE role='teacher'").fetchall()
    pupils = con.execute("SELECT * FROM pupils").fetchall()
    return render_template("admin_panel.html", teachers=teachers, pupils=pupils)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
