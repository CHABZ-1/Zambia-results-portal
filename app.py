import os, time, json
from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "mkushi-boarding-2026"
app.config['PERMANENT_SESSION_LIFETIME'] = 1800

DATA_FILE = "data.json"
def load():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE) as f: return json.load(f)
        except: pass
    return {"users": {}, "results": [], "attempts": {}}
def save(d):
    with open(DATA_FILE, "w") as f: json.dump(d, f)
DB = load()
if "admin" not in DB["users"]:
    DB["users"]["admin"] = {"password": generate_password_hash("admin123"), "role": "admin", "full_name": "School Administrator"}
    save(DB)

BASE = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mkushi Boarding Secondary School | Student Portal</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box} body{margin:0;font-family:'Inter',Arial,sans-serif;background:#ECEEEB;color:#1A1A1A}
.header{background:#0B3D2E;color:#fff;padding:14px 20px;display:flex;align-items:center;gap:14px;border-bottom:3px solid #C9A227}
.header .crest{width:52px;height:52px;background:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#0B3D2E;font-weight:700;font-size:22px;flex-shrink:0}
.header h1{margin:0;font-size:16px;line-height:1.3;letter-spacing:.3px} .header p{margin:2px 0 0;color:#C9A227;font-size:12px;font-style:italic}
.wrap{max-width:480px;margin:28px auto;padding:0 14px}
.card{background:#fff;border-radius:8px;border:1px solid #D9D9D9;padding:28px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
h2{margin:0 0 6px;font-size:20px} .sub{color:#666;font-size:13px;margin:0 0 20px}
label{display:block;font-size:12px;font-weight:600;margin:14px 0 6px;text-transform:uppercase;letter-spacing:.5px;color:#444}
input,select{width:100%;padding:12px;border:1px solid #CFCFCF;border-radius:6px;font-size:15px;background:#fff}
input:focus,select:focus{outline:2px solid #0B3D2E;border-color:#0B3D2E}
.btn{width:100%;padding:13px;background:#0B3D2E;color:#fff;border:none;border-radius:6px;font-size:15px;font-weight:600;cursor:pointer;margin-top:18px}
.btn:hover{background:#083024} .btn-gold{background:#C9A227;color:#0B3D2E}
a{color:#0B3D2E;font-weight:600;text-decoration:none} a:hover{text-decoration:underline}
.alert{background:#FDECEC;border:1px solid #F5C6C6;color:#7A1F1F;padding:12px;border-radius:6px;font-size:13px;margin-bottom:14px}
.success{background:#EAF5EC;border:1px solid #B9D9BE;color:#0B3D2E;padding:12px;border-radius:6px;font-size:13px;margin-bottom:14px}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:14px} th{background:#0B3D2E;color:#fff;text-align:left;padding:10px} td{padding:10px;border-bottom:1px solid #E5E5E5}
.topbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;font-size:13px}
.badge{background:#0B3D2E;color:#fff;padding:4px 10px;border-radius:20px;font-size:11px;letter-spacing:.5px}
.footer{text-align:center;color:#777;font-size:12px;margin:22px 0;line-height:1.6}
.small{font-size:12px;color:#666;line-height:1.6}
hr{border:none;border-top:1px solid #E5E5E5;margin:20px 0}
@media print{ .no-print{display:none} body{background:#fff} .card{box-shadow:none;border:none} }
</style></head><body>
<div class="header"><div class="crest">M</div><div><h1>MKUSHI BOARDING SECONDARY SCHOOL</h1><p>Discipline & Hardwork Lead to Prosperity</p></div></div>
<div class="wrap"><div class="card">{{content|safe}}</div>
<div class="footer">Mkushi Boarding Secondary School &bull; Central Province, Zambia<br>Discipline &bull; Hardwork &bull; Prosperity<br><a href="/verify">Verify Results</a> &bull; <a href="/login">Portal Login</a></div></div>
</body></html>"""

def is_locked(ip):
    a = DB["attempts"].get(ip, {"count":0,"until":0})
    return time.time() < a.get("until",0)
def fail_login(ip):
    a = DB["attempts"].get(ip, {"count":0,"until":0})
    a["count"] += 1
    if a["count"] >= 5:
        a["until"] = time.time() + 900
        a["count"] = 0
    DB["attempts"][ip] = a; save(DB)

@app.route('/')
def home(): return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    ip = request.remote_addr
    if is_locked(ip):
        return render_template_string(BASE, content="<div class='alert'>Too many failed attempts. Account locked for 15 minutes for security. Contact the school administrator.</div><p class='small'><a href='/verify'>Go to Result Verification</a></p>")
    if request.method == 'POST':
        u = DB["users"].get(request.form['username'].strip())
        if u and check_password_hash(u['password'], request.form['password']) and u['role'] == request.form['role']:
            session.permanent = True; session['user'] = request.form['username'].strip(); session['role'] = u['role']
            DB["attempts"].pop(ip, None); save(DB)
            return redirect('/admin' if u['role']=='admin' else '/dashboard')
        fail_login(ip)
        return render_template_string(BASE, content="<div class='alert'>Invalid credentials or incorrect user type. Please check and try again. For assistance, contact the school office.</div><p class='small'><a href='/login'>Try Again</a></p>")
    return render_template_string(BASE, content="""
    <h2>Student & Staff Portal</h2><p class='sub'>Sign in to access your account. This portal is for authorised users only.</p>
    <form method='POST'>
    <label>Username</label><input name='username' autocomplete='username' required>
    <label>Password</label><input name='password' type='password' autocomplete='current-password' required>
    <label>User Type</label><select name='role'><option value='student'>Student</option><option value='admin'>Administrator</option></select>
    <button class='btn'>Sign In</button></form>
    <hr><p class='small'>Forgot your password? Contact the school administrator to reset it. Do not share your login details.</p>
    <p class='small' style='margin-top:12px'><a href='/verify'>Verify Examination Results &rarr;</a></p>""")

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    return render_template_string(BASE, content=f"""
    <div class='topbar'><span class='badge'>STUDENT</span><a href='/logout'>Sign Out</a></div>
    <h2>Welcome, {session.get('user')}</h2><p class='sub'>Mkushi Boarding Secondary School</p>
    <p class='small'>Check your official examination result using your Examination Number and Year.</p>
    <a href='/verify'><button class='btn'>Check My Results</button></a>
    <p class='small' style='margin-top:16px'>If your details are incorrect, report to the Examinations Office immediately.</p>""")

@app.route('/admin', methods=['GET','POST'])
def admin():
    if session.get('role') != 'admin': return redirect('/login')
    msg=""
    if request.method == 'POST':
        form = request.form
        if form.get('action') == 'add_result':
            DB["results"].append({"exam_number": form['exam_number'].strip(), "name": form['name'].strip().title(), "grade": form['grade'], "year": form['year'], "english": form['english'], "maths": form['maths'], "science": form['science'], "status": form['status']})
            save(DB); msg="<div class='success'>Result added successfully.</div>"
        elif form.get('action') == 'add_user':
            if form['new_user'] in DB["users"]: msg="<div class='alert'>Username already exists.</div>"
            elif len(form['new_pass']) < 8: msg="<div class='alert'>Password must be at least 8 characters.</div>"
            else:
                DB["users"][form['new_user']] = {"password": generate_password_hash(form['new_pass']), "role": "student", "full_name": form['new_user']}
                save(DB); msg="<div class='success'>Student account created.</div>"
        elif form.get('action') == 'reset_pass':
            if form['reset_user'] in DB["users"]:
                DB["users"][form['reset_user']]['password'] = generate_password_hash(form['reset_pass']); save(DB); msg="<div class='success'>Password reset.</div>"
    rows="".join([f"<tr><td>{r['exam_number']}</td><td>{r['name']}</td><td>{r['grade']} / {r['year']}</td><td>{r['status']}</td></tr>" for r in reversed(DB["results"][-50:])])
    return render_template_string(BASE, content=f"""
    <div class='topbar'><span class='badge'>ADMINISTRATOR</span><a href='/logout'>Sign Out</a></div>
    <h2>Administration</h2><p class='sub'>Manage results and student accounts. Logged in as {session.get('user')}</p>{msg}
    <h3 style='font-size:15px'>Add Examination Result</h3>
    <form method='POST'><input type='hidden' name='action' value='add_result'>
    <label>Examination Number</label><input name='exam_number' placeholder='e.g. 260101001' required>
    <label>Candidate Name</label><input name='name' required>
    <label>Grade</label><select name='grade'><option>7</option><option>9</option><option>12</option></select>
    <label>Examination Year</label><input name='year' placeholder='2026' required>
    <label>English</label><input name='english' placeholder='1 - 6'>
    <label>Mathematics</label><input name='maths' placeholder='1 - 6'>
    <label>Science</label><input name='science' placeholder='1 - 6'>
    <label>Overall Status</label><select name='status'><option>Pass</option><option>Merit</option><option>Distinction</option><option>Fail</option></select>
    <button class='btn'>Save Result</button></form><hr>
    <h3 style='font-size:15px'>Create Student Account</h3>
    <form method='POST'><input type='hidden' name='action' value='add_user'>
    <label>Username</label><input name='new_user' required>
    <label>Temporary Password (min 8 characters)</label><input name='new_pass' type='password' required>
    <button class='btn btn-gold'>Create Account</button></form><hr>
    <h3 style='font-size:15px'>Reset Student Password</h3>
    <form method='POST'><input type='hidden' name='action' value='reset_pass'>
    <label>Username</label><input name='reset_user' required>
    <label>New Password</label><input name='reset_pass' type='password' required>
    <button class='btn'>Reset Password</button></form><hr>
    <h3 style='font-size:15px'>Recent Results ({len(DB["results"])})</h3>
    <table><tr><th>Exam No</th><th>Name</th><th>Grade / Year</th><th>Status</th></tr>{rows if rows else '<tr><td colspan=4>No results yet.</td></tr>'}</table>""")

@app.route('/verify', methods=['GET','POST'])
def verify():
    if request.method == 'POST':
        r = next((x for x in DB["results"] if x['exam_number']==request.form['exam_number'].strip() and x['year']==request.form['year'].strip()), None)
        if not r:
            return render_template_string(BASE, content="<div class='alert'>No matching record found. Check your
