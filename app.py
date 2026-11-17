import os
from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mkushi-2026-change-this-123")

# No database - just memory
USERS = {"admin": {"password": generate_password_hash("admin123"), "role": "admin"}}
RESULTS = []

BASE = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Zambia Results Portal</title>
<style>
body{font-family:Arial;background:#f2f2f2;margin:0;padding:20px}
.card{background:white;max-width:500px;margin:auto;padding:20px;border-radius:10px;box-shadow:0 2px 10px #ccc}
input,select{width:100%;padding:12px;margin:8px 0;box-sizing:border-box}
button{width:100%;padding:12px;background:#006400;color:white;border:none;border-radius:5px;font-size:16px}
a{color:#006400} table{width:100%;border-collapse:collapse} td,th{border:1px solid #ddd;padding:8px}
h2{text-align:center;color:#006400}
</style></head><body><div class="card">{{content|safe}}</div></body></html>
"""

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = USERS.get(request.form['username'])
        if u and check_password_hash(u['password'], request.form['password']):
            session['user'] = request.form['username']
            session['role'] = u['role']
            return redirect('/admin' if u['role']=='admin' else '/student')
        return render_template_string(BASE, content="<h2>Login Failed</h2><p>Wrong username/password</p><a href='/login'>Try again</a>")
    return render_template_string(BASE, content="""
    <h2>🇿🇲 Zambia Results Portal</h2>
    <form method="POST">
    <input name="username" placeholder="Username" required>
    <input name="password" type="password" placeholder="Password" required>
    <button>Login</button></form>
    <p>Default Admin: <b>admin / admin123</b></p>
    <p><a href='/verify'>Check Result Without Login →</a></p>
    <p><a href='/register'>Create Student Account</a></p>""")

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        if request.form['username'] in USERS:
            return "Username taken <a href='/register'>Back</a>"
        USERS[request.form['username']] = {"password": generate_password_hash(request.form['password']), "role": "student"}
        return redirect('/login')
    return render_template_string(BASE, content="""
    <h2>Create Account</h2><form method="POST">
    <input name="username" placeholder="Choose Username" required>
    <input name="password" type="password" placeholder="Choose Password" required>
    <button>Register</button></form><a href='/login'>Back to Login</a>""")

@app.route('/admin', methods=['GET','POST'])
def admin():
    if session.get('role') != 'admin':
        return redirect('/login')
    if request.method == 'POST':
        RESULTS.append({
            "exam_number": request.form['exam_number'], "name": request.form['name'],
            "school": request.form['school'], "grade": request.form['grade'],
            "year": request.form['year'], "english": request.form['english'],
            "maths": request.form['maths'], "science": request.form['science'],
            "status": request.form['status']})
        return redirect('/admin')
    rows = "".join([f"<tr><td>{r['exam_number']}</td><td>{r['name']}</td><td>{r['school']}</td><td>{r['grade']}</td><td>{r['status']}</td></tr>" for r in RESULTS])
    return render_template_string(BASE, content=f"""
    <h2>Admin Dashboard</h2><p>Logged in as {session.get('user')} | <a href='/logout'>Logout</a></p>
    <h3>Add Result</h3><form method="POST">
    <input name="exam_number" placeholder="Exam Number e.g 123456/001" required>
    <input name="name" placeholder="Full Name" required>
    <input name="school" placeholder="School" required>
    <select name="grade"><option>7</option><option>9</option><option>12</option></select>
    <input name="year" placeholder="Year e.g 2026" required>
    <input name="english" placeholder="English Grade e.g 1-6">
    <input name="maths" placeholder="Maths Grade">
    <input name="science" placeholder="Science Grade">
    <select name="status"><option>Pass</option><option>Fail</option><option>Merit</option></select>
    <button>Add Result</button></form>
    <h3>All Results ({len(RESULTS)})</h3>
    <table><tr><th>Exam No</th><th>Name</th><th>School</th><th>Grade</th><th>Status</th></tr>{rows}</table>""")

@app.route('/student')
def student():
    if 'user' not in session:
        return redirect('/login')
    return render_template_string(BASE, content=f"""
    <h2>Welcome, {session.get('user')}</h2>
    <p>Use Verify to check your result.</p>
    <a href='/verify'><button>Check My Result</button></a><br><br>
    <a href='/logout'>Logout</a>""")

@app.route('/verify', methods=['GET','POST'])
def verify():
    if request.method == 'POST':
        r = next((x for x in RESULTS if x['exam_number'] == request.form['exam_number']), None)
        if not r:
            return render_template_string(BASE, content="<h2>Not Found</h2><p>No result for that exam number.</p><a href='/verify'>Try Again</a>")
        return render_template_string(BASE, content=f"""
        <h2>Result Found ✅</h2>
        <p><b>Name:</b> {r['name']}</p>
        <p><b>School:</b> {r['school']}</p>
        <p><b>Grade:</b> {r['grade']} | <b>Year:</b> {r['year']}</p>
        <p><b>English:</b> {r['english']} | <b>Maths:</b> {r['maths']} | <b>Science:</b> {r['science']}</p>
        <p><b>Status:</b> {r['status']}</p>
        <a href='/verify'>Check Another</a> | <a href='/login'>Login</a>""")
    return render_template_string(BASE, content="""
    <h2>Verify Result</h2><form method="POST">
    <input name="exam_number" placeholder="Enter Exam Number" required>
    <button>Check Result</button></form><a href='/login'>Back</a>""")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
