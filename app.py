import os
import sqlite3
from flask import Flask, render_template, request, redirect, flash, session, g, send_from_directory
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
    for s in ["Mathematics","English","Science","Biology","Physics","Chemistry"]:
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

# --- LOGO ROUTE - WORKS WITH YOUR NAME ---
@app.route('/IMG_2053.jpeg')
@app.route('/static/IMG_2053.jpeg')
def serve_logo():
    if os.path.exists("static/IMG_2053.jpeg"):
        return send_from_directory("static", "IMG_2053.jpeg")
    if os.path.exists("IMG_2053.jpeg"):
        return send_from_directory(".", "IMG_2053.jpeg")
    if os.path.exists("static/logo.png"):
        return send_from_directory("static", "logo.png")
    return "Logo not found", 404

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","").strip()
        con = get_db()
        user = con.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p)).fetchone
