import os, secrets, sqlite3
from flask import Flask, render_template, request, redirect, session, url_for, g

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mkushi-2026-secret-change-this")

# --- DB (SQLite locally, Postgres on Render if DATABASE_URL set) ---
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    if DATABASE_URL:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    else:
        conn = sqlite3.connect("mkushi.db")
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Use compatible SQL for both
    c.execute('''CREATE TABLE IF NOT EXISTS users
    (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, name TEXT, exam_no TEXT, phone TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS results
    (id INTEGER PRIMARY KEY, exam_no TEXT UNIQUE, pupil_name TEXT, grade TEXT, subjects TEXT, gpa REAL, verification_code TEXT UNIQUE, created_by TEXT)''')
    conn.commit()
    # Default admin - CHANGE PASSWORD AFTER FIRST LOGIN
    try:
        c.execute("INSERT INTO users (username,password,role,name) VALUES (?,?,?,?)", ("admin","admin123","admin","Admin"))
        conn.commit()
    except: pass
    conn.close()

init_db()

# --- Helpers ---
def q_one(sql, params=()):
    conn = get_db(); cur = conn.cursor()
    # Fix ? placeholders for postgres
    if DATABASE_URL: sql = sql.replace("?", "%s")
    cur.execute(sql, params); r = cur.fetchone(); conn.close(); return r

def q_all(sql, params=()):
    conn = get_db(); cur = conn.cursor()
    if DATABASE_URL: sql = sql.replace("?", "%s")
    cur.execute(sql, params); r = cur.fetchall(); conn.close(); return r

def execute(sql, params=()):
    conn = get_db(); cur = conn.cursor()
    if DATABASE_URL: sql = sql.replace("?", "%s")
    cur.execute(sql, params); conn.commit
