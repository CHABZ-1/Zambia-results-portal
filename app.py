from flask import Flask, render_template, request, redirect, session, abort
import sqlite3, os, secrets
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'mkushi-2026-secure-key-change-this'

DB = 'mkushi.db'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
    (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS pupils
    (id INTEGER PRIMARY KEY, exam_no TEXT UNIQUE, full_name TEXT, grade TEXT, class_sec TEXT, parent_phone TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS results
    (id INTEGER PRIMARY KEY, exam_no TEXT UNIQUE, subjects TEXT, gpa REAL, verification_code TEXT UNIQUE, created_by TEXT)''')
    # Create default admin if not exists
    cur = conn.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        conn.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",
                     ('admin', generate_password_hash('Admin@123'), 'admin'))
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home(): return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        if role in ['admin','teacher']:
            u = request.form.get('username')
            p = request.form.get('password')
            conn = get_db()
            user = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
            conn.close()
            if user and check_password_hash(user['password'], p):
                session['user'] = u
                session['role'] = user['role']
                return redirect('/dashboard')
            return "Wrong password"
        elif role == 'parent':
            exam_no = request.form.get('child_name').strip() # We use this field for exam_no now
            grade = request.form.get('grade','').strip()
            conn = get_db()
            pupil = conn.execute("SELECT * FROM pupils WHERE exam_no=?", (exam_no,)).fetchone()
            conn.close()
            if pupil:
                session['exam_no'] = exam_no
                return redirect(f'/result/{exam_no}')
            return "Exam Number not found. Contact school."
        elif role == 'pupil':
            exam_no = request.form.get('child_name').strip()
            conn = get_db()
            pupil = conn.execute("SELECT * FROM pupils WHERE exam_no=?", (exam_no,)).fetchone()
            conn.close()
            if pupil:
                session['exam_no'] = exam_no
                return redirect(f'/result/{exam_no}')
            return "Exam Number not found"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    conn = get_db()
    pupils = conn.execute("SELECT * FROM pupils").fetchall()
    results = conn.execute("SELECT pupils.full_name, pupils.exam_no, pupils.grade, results.gpa, results.verification_code FROM pupils LEFT JOIN results ON pupils.exam_no = results.exam_no").fetchall()
    conn.close()
    return render_template('dashboard.html', pupils=pupils, results=results, user=session['user'])

@app.route('/add_pupil', methods=['POST'])
def add_pupil():
    if 'user' not in session: return redirect('/login')
    exam_no = request.form.get('exam_no').upper().strip()
    name = request.form.get('full_name')
    grade = request.form.get('grade')
    sec = request.form.get('class_sec')
    phone = request.form.get('parent_phone')
    conn = get_db()
    try:
        conn.execute("INSERT INTO pupils (exam_no,full_name,grade,class_sec,parent_phone) VALUES (?,?,?,?,?)",
                     (exam_no,name,grade,sec,phone))
        conn.commit()
    except: pass
    conn.close()
    return redirect('/dashboard')

@app.route('/add_result', methods=['POST'])
def add_result():
    if 'user' not in session: return redirect('/login')
    exam_no = request.form.get('exam_no').upper().strip()
    subjects = request.form.get('subjects')
    gpa = request.form.get('gpa')
    code = secrets.token_hex(3).upper() # e.g A7F9K2 - anti-forgery
    conn = get_db()
    try:
        conn.execute("INSERT OR REPLACE INTO results (exam_no,subjects,gpa,verification_code,created_by) VALUES (?,?,?,?,?)",
                     (exam_no,subjects,gpa,code,session['user']))
        conn.commit()
    except Exception as e:
        print(e)
    conn.close()
    return redirect('/dashboard')

@app.route('/result/<exam_no>')
def result_page(exam_no):
    conn = get_db()
    pupil = conn.execute("SELECT * FROM pupils WHERE exam_no=?", (exam_no,)).fetchone()
    res = conn.execute("SELECT * FROM results WHERE exam_no=?", (exam_no,)).fetchone()
    conn.close()
    if not pupil: abort(404)
    return render_template('result.html', pupil=pupil, result=res)

@app.route('/verify/<code>')
def verify(code):
    conn = get_db()
    r = conn.execute("SELECT pupils.full_name, pupils.exam_no, results.gpa, results.verification_code FROM results JOIN pupils ON results.exam_no = pupils.exam_no WHERE verification_code=?", (code,)).fetchone()
    conn.close()
    if r:
        return f"<div style='font-family:Arial;padding:30px;text-align:center'><h2 style='color:green'>✓ VALID DOCUMENT</h2><p>Exam No: {r['exam_no']}<br>Name: {r['full_name']}<br>GPA: {r['gpa']}<br>Code: {r['verification_code']}<br><b>Verified by Mkushi Boarding Secondary School Board</b></p></div>"
    return "<h2 style='color:red;text-align:center;padding:30px'>✗ INVALID / FORGED DOCUMENT</h2>", 404

@app.route('/sitemap.xml')
def sitemap():
    return """<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://m-results-portal.onrender.com/login</loc></url><url><loc>https://m-results-portal.onrender.com/verify</loc></url></urlset>""", 200, {'Content-Type':'application/xml'}

if __name__ == '__main__':
    app.run(debug=True)
