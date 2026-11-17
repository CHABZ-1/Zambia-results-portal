import os, json
from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = "mkushi-boarding-2026"
F = "data.json"
def load():
    try:
        return json.load(open(F))
    except:
        return {"users": {"admin": {"p": generate_password_hash("admin123"), "r": "admin"}}, "results": []}
def save(d): json.dump(d, open(F, "w"))
DB = load()
B = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mkushi Boarding Secondary School</title>
<style>body{margin:0;font-family:Arial;background:#ECEEEB;color:#1A1A1A}.h{background:#0B3D2E;color:#fff;padding:14px 20px;border-bottom:3px solid #C9A227}.h b{font-size:16px}.h i{color:#C9A227;font-size:12px}.w{max-width:480px;margin:28px auto;padding:0 14px}.c{background:#fff;border-radius:8px;border:1px solid #D9D9D9;padding:28px}h2{margin:0 0 6px}.s{color:#666;font-size:13px;margin:0 0 20px}label{display:block;font-size:12px;font-weight:700;margin:14px 0 6px;text-transform:uppercase;color:#444}input,select{width:100%;padding:12px;border:1px solid #CFCFCF;border-radius:6px;font-size:15px}.btn{width:100%;padding:13px;background:#0B3D2E;color:#fff;border:none;border-radius:6px;font-size:15px;font-weight:700;margin-top:18px}a{color:#0B3D2E;font-weight:700;text-decoration:none}.al{background:#FDECEC;border:1px solid #F5C6C6;padding:12px;border-radius:6px;font-size:13px}.ok{background:#EAF5EC;border:1px solid #B9D9BE;padding:12px;border-radius:6px;font-size:13px}table{width:100%;border-collapse:collapse;font-size:13px;margin-top:14px}th{background:#0B3D2E;color:#fff;text-align:left;padding:10px}td{padding:10px;border-bottom:1px solid #E5E5E5}.f{text-align:center;color:#777;font-size:12px;margin:22px 0;line-height:1.6}</style></head><body>
<div class="h"><b>MKUSHI BOARDING SECONDARY SCHOOL</b><br><i>Discipline & Hardwork Lead to Prosperity</i></div>
<div class="w"><div class="c">{{c|safe}}</div><div class="f">Mkushi Boarding Secondary School &bull; Central Province, Zambia<br><a href="/verify">Verify Results</a> &bull; <a href="/login">Portal Login</a></div></div></body></html>"""
@app.route('/')
def home(): return redirect('/login')
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = DB["users"].get(request.form['username'].strip())
        if u and check_password_hash(u['p'], request.form['password']) and u['r'] == request.form['role']:
            session['user'] = request.form['username'].strip(); session['role'] = u['r']
            return redirect('/admin' if u['r'] == 'admin' else '/dashboard')
        return render_template_string(B, c="<div class='al'>Invalid credentials. Try again.</div><p><a href='/login'>Try Again</a></p>")
    return render_template_string(B, c="""<h2>Student & Staff Portal</h2><p class='s'>Sign in to access your account. Authorised users only.</p>
    <form method='POST'><label>Username</label><input name='username' required><label>Password</label><input name='password' type='password' required>
    <label>User Type</label><select name='role'><option value='student'>Student</option><option value='admin'>Administrator</option></select>
    <button class='btn'>Sign In</button></form><p class='s' style='margin-top:16px'>Forgot password? Contact the school administrator.</p><p><a href='/verify'>Verify Examination Results &rarr;</a></p>""")
@app.route('/dashboard')
def dash():
    if 'user' not in session: return redirect('/login')
    return render_template_string(B, c=f"<h2>Welcome, {session['user']}</h2><p class='s'>Mkushi Boarding Secondary School</p><a href='/verify'><button class='btn'>Check My Results</button></a><p style='text-align:center;margin-top:14px'><a href='/logout'>Sign Out</a></p>")
@app.route('/admin', methods=['GET','POST'])
def admin():
    if session.get('role') != 'admin': return redirect('/login')
    m = ""
    if request.method == 'POST':
        if request.form.get('action') == 'result':
            DB["results"].append({"n": request.form['exam_number'].strip(), "name": request.form['name'].strip().title(), "g": request.form['grade'], "y": request.form['year'], "e": request.form['english'], "ma": request.form['maths'], "s": request.form['science'], "st": request.form['status']}); save(DB); m = "<div class='ok'>Result added.</div>"
        else:
            if request.form['new_user'] in DB["users"]: m = "<div class='al'>Username exists.</div>"
            else: DB["users"][request.form['new_user']] = {"p": generate_password_hash(request.form['new_pass']), "r": "student"}; save(DB); m = "<div class='ok'>Student account created.</div>"
    rows = "".join([f"<tr><td>{r['n']}</td><td>{r['name']}</td><td>{r['g']} / {r['y']}</td><td>{r['st']}</td></tr>" for r in reversed(DB["results"][-50:])])
    return render_template_string(B, c=f"""<h2>Administration</h2><p class='s'>Logged in as {session['user']}</p>{m}
    <h3>Add Examination Result</h3><form method='POST'><input type='hidden' name='action' value='result'>
    <label>Examination Number</label><input name='exam_number' required><label>Candidate Name</label><input name='name' required>
    <label>Grade</label><select name='grade'><option>7</option><option>9</option><option>12</option></select>
    <label>Year</label><input name='year' placeholder='2026' required><label>English</label><input name='english'>
    <label>Mathematics</label><input name='maths'><label>Science</label><input name='science'>
    <label>Status</label><select name='status'><option>Pass</option><option>Merit</option><option>Distinction</option><option>Fail</option></select>
    <button class='btn'>Save Result</button></form><hr>
    <h3>Create Student Account</h3><form method='POST'><input type='hidden' name='action' value='user'>
    <label>Username</label><input name='new_user' required><label>Password (min 8)</label><input name='new_pass' type='password' required>
    <button class='btn'>Create Account</button></form><hr>
    <h3>Recent Results ({len(DB["results"])})</h3><table><tr><th>Exam No</th><th>Name</th><th>Grade / Year</th><th>Status</th></tr>{rows if rows else '<tr><td colspan=4>No results yet.</td></tr>'}</table>
    <p style='text-align:center;margin-top:14px'><a href='/logout'>Sign Out</a></p>""")
@app.route('/verify', methods=['GET','POST'])
def verify():
    if request.method == 'POST':
        r = next((x for x in DB["results"] if x['n'] == request.form['exam_number'].strip() and x['y'] == request.form['year'].strip()), None)
        if not r: return render_template_string(B, c="<div class='al'>No matching record found. Check Exam Number and Year.</div><p><a href='/verify'>Search Again</a></p>")
        return render_template_string(B, c=f"""<h2>Examination Result</h2><p class='s'>Mkushi Boarding Secondary School</p>
        <table><tr><th>Candidate</th><td>{r['name']}</td></tr><tr><th>Exam Number</th><td>{r['n']}</td></tr><tr><th>Grade</th><td>{r['g']}</td></tr><tr><th>Year</th><td>{r['y']}</td></tr><tr><th>English</th><td>{r['e']}</td></tr><tr><th>Mathematics</th><td>{r['ma']}</td></tr><tr><th>Science</th><td>{r['s']}</td></tr><tr><th>Overall</th><td><b>{r['st']}</b></td></tr></table>
        <button class='btn' onclick='window.print()'>Print Result Slip</button><p style='text-align:center;margin-top:14px'><a href='/verify'>Verify Another</a></p>""")
    return render_template_string(B, c="""<h2>Verify Examination Results</h2><p class='s'>Enter details exactly as on your examination slip.</p>
    <form method='POST'><label>Examination Number</label><input name='exam_number' required><label>Examination Year</label><input name='year' required>
    <button class='btn'>Verify Result</button></form>""")
@app.route('/logout')
def logout(): session.clear(); return redirect('/login')
if __name__ == '__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
