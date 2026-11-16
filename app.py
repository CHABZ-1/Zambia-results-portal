import os, sqlite3
from flask import Flask, render_template, request, redirect, flash, session, g
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "zafika-2026-secret")
DATABASE = "zafika.db"
SCHOOL_NAME = "Zafika"

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
    con.execute("CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY, pupil_id INTEGER, subject_id INTEGER, term TEXT, score INTEGER, comment TEXT, is_published INTEGER DEFAULT 0, updated_at TEXT, UNIQUE(pupil_id, term, subject_id))")
    cur = con.execute("SELECT id FROM users WHERE username=?", ("admin",)).fetchone()
    if not cur:
        con.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)", ("admin","admin123","admin"))
        con.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)", ("teacher","teacher123","teacher"))
    for sub in ["Mathematics","Physics","Chemistry","Biology","English","Geography","History","RE"]:
        try: con.execute("INSERT INTO subjects (name) VALUES (?)", (sub,))
        except: pass
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
                flash("Not allowed","error")
                return redirect("/login")
            return f(*a, **kw)
        return wrap
    return deco

@app.route("/")
def home():
    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","").strip()
        role = request.form.get("role","teacher")  # from tabs
        con = get_db()
        user = con.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password)).fetchone()
        # allow any username as pupil/parent for demo - check pupils table too
        if user:
            session["user_id"]=user["id"]
            session["username"]=user["username"]
            session["role"]=user["role"]
            if user["role"]=="admin":
                return redirect("/admin/panel")
            return redirect("/teacher/upload")
        # pupil/parent login via pupil name
        pupil = con.execute("SELECT * FROM pupils WHERE full_name LIKE ?", (f"%{username}%",)).fetchone()
        if pupil and role in ["pupil","parent"]:
            session["user_id"]=pupil["id"]
            session["username"]=pupil["full_name"]
            session["role"]=role
            return redirect("/check-results")
        flash("Wrong username or password","error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/check-results")
def check_results():
    return "Results page - login as pupil/parent works"

@app.route("/teacher/upload", methods=["GET","POST"])
@login_required(roles=["admin","teacher"])
def teacher_upload():
    con=get_db()
    grade=request.values.get("grade","Grade 10A")
    term=request.values.get("term","Term2")
    subject_id=request.values.get("subject_id","1")
    try: subject_id=int(subject_id)
    except: subject_id=1
    subjects=con.execute("SELECT * FROM subjects ORDER BY name").fetchall()
    pupils=con.execute("SELECT * FROM pupils WHERE grade=? ORDER BY full_name", (grade,)).fetchall()
    if request.method=="POST":
        grade=request.form.get("grade")
        term=request.form.get("term")
        subject_id=int(request.form.get("subject_id"))
        pupils_post=con.execute("SELECT * FROM pupils WHERE grade=?", (grade,)).fetchall()
        for pu in pupils_post:
            score=request.form.get(f"score_{pu['id']}")
            comment=request.form.get(f"comment_{pu['id']}")
            if score and score.strip()!="":
                try:
                    con.execute("INSERT INTO results (pupil_id, subject_id, term, score, comment, is_published, updated_at) VALUES (?,?,?,?,?,0,?) ON CONFLICT(pupil_id, term, subject_id) DO UPDATE SET score=excluded.score, comment=excluded.comment, updated_at=excluded.updated_at", (pu["id"], subject_id, term, int(score), comment, datetime.now().isoformat()))
                except Exception as e: print(e)
        con.commit()
        flash(f"Saved draft for {grade} {term}","success")
        return redirect(f"/teacher/upload?grade={grade}&term={term}&subject_id={subject_id}")
    return render_template("teacher_upload.html", grade=grade, term=term, subject_id=subject_id, subjects=subjects, pupils=pupils)

@app.route("/teacher/publish", methods=["GET","POST"])
@login_required(roles=["admin","teacher"])
def teacher_publish():
    con=get_db()
    grade=request.values.get("grade","Grade 10A")
    term=request.values.get("term","Term2")
    progress=con.execute("SELECT s.id, s.name, COUNT(r.id) as count FROM subjects s LEFT JOIN results r ON r.subject_id=s.id AND r.term=? AND r.pupil_id IN (SELECT id FROM pupils WHERE grade=?) GROUP BY s.id ORDER BY s.name", (term, grade)).fetchall()
    total_row=con.execute("SELECT COUNT(*) as c FROM pupils WHERE grade=?", (grade,)).fetchone()
    total_pupils=total_row["c"] if total_row else 0
    return render_template("teacher_publish.html", grade=grade, term=term, progress=progress, total_pupils=total_pupils)

@app.route("/teacher/publish-all", methods=["POST"])
@login_required(roles=["admin","teacher"])
def teacher_publish_all():
    grade=request.form.get("grade")
    term=request.form.get("term")
    is_last=request.form.get("is_last")
    if not is_last:
        flash("Tick I am LAST teacher","error")
        return redirect(f"/teacher/publish?grade={grade}&term={term}")
    con=get_db()
    con.execute("UPDATE results SET is_published=1, updated_at=? WHERE pupil_id IN (SELECT id FROM pupils WHERE grade=?) AND term=?", (datetime.now().isoformat(), grade, term))
    con.commit()
    flash(f"ALL {grade} {term} published - parents will see results together","success")
    return redirect(f"/teacher/publish?grade={grade}&term={term}")

@app.route("/teacher/pupils", methods=["GET","POST"])
@login_required(roles=["admin","teacher"])
def teacher_pupils():
    con=get_db()
    if request.method=="POST":
        con.execute("INSERT INTO pupils (full_name, grade, parent_phone) VALUES (?,?,?)", (request.form.get("full_name"), request.form.get("grade"), request.form.get("parent_phone")))
        con.commit()
    pupils=con.execute("SELECT * FROM pupils ORDER BY grade").fetchall()
    return render_template("teacher_pupils.html", pupils=pupils)

@app.route("/admin/panel")
@login_required(roles=["admin"])
def admin_panel():
    con=get_db()
    users=con.execute("SELECT * FROM users").fetchall()
    return render_template("admin_panel.html", users=users)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=10000)
