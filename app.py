import os, json
from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = "mkushi-boarding-2026"
F = "data.json"
def load():
    try: return json.load(open(F))
    except: return {"users": {"admin": {"p": generate_password_hash("admin123"), "r": "admin", "name": "Admin"}}, "pupils": [], "results": {}}
def save(d): json.dump(d, open(F, "w"))
DB = load()
SUBJECTS = {
 "Form 1": ["English Language","Mathematics","Biology","Chemistry","Physics","Geography","History","Civic Education","Religious Studies","Zambian Language","Computer Studies","Agriculture Science"],
 "Form 2": ["English Language","Mathematics","Biology","Chemistry","Physics","Geography","History","Civic Education","Religious Studies","Zambian Language","Computer Studies","Agriculture Science"],
 "Form 3": ["English Language","Mathematics","Biology","Chemistry","Physics","Geography","History","Civic Education","Religious Studies","Zambian Language","Computer Studies"],
 "Form 4": ["English Language","Mathematics","Biology","Chemistry","Physics","Geography","History","Civic Education","Religious Studies","Zambian Language","Computer Studies"],
 "Form 5": ["Biology","Chemistry","Physics","Mathematics","English Language","Geography","History","Economics","Accounting","Computer Science"],
 "Form 6": ["Biology","Chemistry","Physics","Mathematics","English Language","Geography","History","Economics","Accounting","Computer Science"],
 "Grade 10": ["English","Mathematics","Biology","Science","Geography","History","Civic Education","Religious Education","Zambian Language","Computer Studies"],
 "Grade 11": ["English","Mathematics","Biology","Science","Geography","History","Civic Education","Religious Education","Zambian Language","Computer Studies"],
 "Grade 12": ["English","Mathematics","Biology","Science","Geography","History","Civic Education","Religious Education","Zambian Language","Computer Studies"],
}
def grade(m):
    try: m=int(m)
    except: return "-"
    if m>=75: return "A"
    if m>=65: return "B"
    if m>=50: return "C"
    if m>=40: return "D"
    if m>=30: return "E"
    return "F"
B = """<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mkushi Boarding Secondary School</title>
<style>body{margin:0;font-family:Arial;background:#ECEEEB;color:#1A1A1A}.h{background:#0B3D2E;color:#fff;padding:14px 20px;border-bottom:3px solid #C9A227}.h b{font-size:16px}.h i{color:#C9A227;font-size:12px}.w{max-width:900px;margin:20px auto;padding:0 12px}.c{background:#fff;border-radius:8px;border:1px solid #D9D9D9;padding:24px}h2{margin:0 0 6px}.s{color:#666;font-size:13px;margin:0 0 18px}label{display:block;font-size:11px;font-weight:700;margin:12px 0 5px;text-transform:uppercase;color:#444}input,select,textarea{width:100%;padding:10px;border:1px solid #CFCFCF;border-radius:6px;font-size:14px}.btn{width:100%;padding:13px;background:#0B3D2E;color:#fff;border:none;border-radius:6px;font-size:15px;font-weight:700;margin-top:16px;cursor:pointer}.btn2{background:#C9A227;color:#0B3D2E}a{color:#0B3D2E;font-weight:700;text-decoration:none}.al{background:#FDECEC;border:1px solid #F5C6C6;padding:12px;border-radius:6px;font-size:13px}.ok{background:#EAF5EC;border:1px solid #B9D9BE;padding:12px;border-radius:6px;font-size:13px}table{width:100%;border-collapse:collapse;font-size:13px;margin-top:12px}th{background:#0B3D2E;color:#fff;text-align:left;padding:9px}td{padding:8px;border-bottom:1px solid #E5E5E5;vertical-align:top}.f{text-align:center;color:#777;font-size:12px;margin:20px 0;line-height:1.6}.grid{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}.small{font-size:12px;color:#666}.mark{width:70px!important}.com{width:140px!important}.calc{background:#FFF8E1;padding:10px;border-radius:6px;font-size:13px;margin-top:12px}.top{display:flex;justify-content:space-between;font-size:13px;margin-bottom:12px}</style></head><body>
<div class="h"><b>MKUSHI BOARDING SECONDARY SCHOOL</b><br><i>Discipline & Hardwork Lead to Prosperity</i></div>
<div class="w"><div class="c">{{c|safe}}</div><div class="f">Mkushi Boarding Secondary School &bull; 2023 Curriculum (3-6-6-3)<br><a href="/verify">Parent / Pupil Result Check</a> &bull; <a href="/login">Staff Login</a></div></div></body></html>"""
@app.route('/')
def home(): return redirect('/login')
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = DB["users"].get(request.form['username'].strip())
        if u and check_password_hash(u['p'], request.form['password']) and u['r'] == request.form['role']:
            session['user'] = request.form['username'].strip(); session['role'] = u['r']; session['name'] = u.get('name','')
            return redirect('/admin' if u['r']=='admin' else '/teacher')
        return render_template_string(B, c="<div class='al'>Invalid credentials.</div><p><a href='/login'>Try Again</a></p>")
    return render_template_string(B, c="""<h2>Staff Portal</h2><p class='s'>Admin & Teachers only. Parents use Result Check below.</p>
    <form method='POST'><label>Username</label><input name='username' required><label>Password</label><input name='password' type='password' required>
    <label>User Type</label><select name='role'><option value='teacher'>Teacher</option><option value='admin'>Administrator</option></select>
    <button class='btn'>Sign In</button></form><p style='margin-top:14px'><a href='/verify'>Parent / Pupil: Check Term Result &rarr;</a></p>""")
# ---- ADMIN: Register Teachers + Roster ----
@app.route('/admin', methods=['GET','POST'])
def admin():
    if session.get('role') != 'admin': return redirect('/login')
    m=""
    if request.method=='POST':
        a=request.form.get('action')
        if a=='teacher':
            if request.form['u'] in DB["users"]: m="<div class='al'>Username exists.</div>"
            else: DB["users"][request.form['u']]={"p": generate_password_hash(request.form['p']), "r":"teacher", "name": request.form['name'], "subject": request.form.get('subject','')}; save(DB); m="<div class='ok'>Teacher registered.</div>"
        elif a=='pupil':
            DB["pupils"].append({"n": request.form['n'].strip(), "name": request.form['name'].strip().title(), "cls": request.form['cls'], "stream": request.form.get('stream','A'), "sex": request.form.get('sex','M'), "guardian": request.form.get('guardian','')}); save(DB); m="<div class='ok'>Pupil added to roster.</div>"
        elif a=='del_pupil':
            DB["pupils"]=[p for p in DB["pupils"] if p['n']!=request.form['n']]; save(DB); m="<div class='ok'>Pupil removed.</div>"
    teachers="".join([f"<tr><td>{v.get('name','')}</td><td>{k}</td><td>{v.get('subject','')}</td><td>{v['r']}</td></tr>" for k,v in DB["users"].items()])
    pupils="".join([f"<tr><td>{p['n']}</td><td>{p['name']}</td><td>{p['cls']} {p['stream']}</td><td>{p['sex']}</td></tr>" for p in DB["pupils"]])
    import json as js
    opts="".join([f"<option>{k}</option>" for k in SUBJECTS.keys()])
    return render_template_string(B, c=f"""<div class='top'><b>ADMIN - {session.get('name')}</b><a href='/logout'>Sign Out</a></div><h2>Administration</h2><p class='s'>Register teachers & manage pupil roster.</p>{m}
    <h3>1. Register Teacher</h3><form method='POST'><input type='hidden' name='action' value='teacher'>
    <label>Full Name</label><input name='name' required><label>Username</label><input name='u' required><label>Password</label><input name='p' type='password' required>
    <label>Subject / Responsibility</label><input name='subject' placeholder='e.g. Mathematics - Form 1'>
    <button class='btn'>Register Teacher</button></form>
    <table><tr><th>Name</th><th>Username</th><th>Subject</th><th>Role</th></tr>{teachers}</table><hr>
    <h3>2. Add Pupil to Roster</h3><form method='POST'><input type='hidden' name='action' value='pupil'>
    <div class='grid'><div><label>Pupil Number</label><input name='n' required></div><div><label>Full Name</label><input name='name' required></div></div>
    <div class='grid'><div><label>Class</label><select name='cls'>{opts}</select></div><div><label>Stream</label><select name='stream'><option>A</option><option>B</option><option>C</option><option>D</option></select></div></div>
    <div class='grid'><div><label>Sex</label><select name='sex'><option>M</option><option>F</option></select></div><div><label>Guardian Phone (optional)</label><input name='guardian'></div></div>
    <button class='btn btn2'>Add Pupil to Roster</button></form>
    <h3>Roster - All Pupils ({len(DB["pupils"])})</h3><table><tr><th>Pupil No</th><th>Name</th><th>Class</th><th>Sex</th></tr>{pupils if pupils else '<tr><td colspan=4>No pupils yet. Add above.</td></tr>'}</table>""")
# ---- TEACHER: Enter Results by Class ----
@app.route('/teacher', methods=['GET','POST'])
def teacher():
    if session.get('role') not in ('teacher','admin'): return redirect('/login')
    cls = request.args.get('cls','Form 1') if request.method=='GET' else request.form.get('cls','Form 1')
    term = request.args.get('term','Term 1') if request.method=='GET' else request.form.get('term','Term 1')
    year = request.args.get('year','2026') if request.method=='GET' else request.form.get('year','2026')
    m=""
    if request.method=='POST' and request.form.get('action')=='save':
        for p in [x for x in DB["pupils"] if x['cls']==cls]:
            key = f"{p['n']}|{cls}|{term}|{year}"
            subs={}
            total=0; cnt=0
            for s in SUBJECTS[cls]:
                mk = request.form.get(f"m_{p['n']}_{s}", '')
                cm = request.form.get(f"c_{p['n']}_{s}", '')
                subs[s] = {"mark": mk, "comment": cm}
                if mk and mk.isdigit(): total+=int(mk); cnt+=1
            avg = round(total/cnt,1) if cnt else 0
            DB["results"][key] = {"n": p['n'], "name": p['name'], "cls": cls, "t": term, "y": year, "subs": subs, "total": total, "avg": avg, "teacher": session.get('name')}
        save(DB); m="<div class='ok'>Results saved for "+cls+" - "+term+" "+year+". Totals & averages auto-calculated.</div>"
    roster = [p for p in DB["pupils"] if p['cls']==cls]
    # Build entry table
    rows=""
    for p in roster:
        key=f"{p['n']}|{cls}|{term}|{year}"
        old=DB["results"].get(key, {"subs": {}})
        sub_rows="".join([f"<tr><td>{s}</td><td><input class='mark' name='m_{p['n']}_{s}' type='number' min='0' max='100' value='{old['subs'].get(s,{}).get('mark','')}' oninput='calc(\"{p['n']}\")'></td><td><span id='g_{p['n']}_{s}'>{grade(old['subs'].get(s,{}).get('mark',''))}</span></td><td><input class='com' name='c_{p['n']}_{s}' placeholder='e.g. Good effort' value='{old['subs'].get(s,{}).get('comment','')}'></td></tr>" for s in SUBJECTS[cls]])
        rows+=f"<tr><td colspan=4 style='background:#0B3D2E;color:#fff'><b>{p['n']} - {p['name']}</b></td></tr><tr><td colspan=4><table><tr><th>Subject</th><th>Mark %</th><th>Grade</th><th>Teacher Comment (per subject)</th></tr>{sub_rows}</table><div class='calc' id='calc_{p['n']}'>Total: - | Average: - | Grade auto-calculates as you type</div></td></tr>"
    import json as js
    opts="".join([f"<option {'selected' if k==cls else ''}>{k}</option>" for k in SUBJECTS.keys()])
    # JS for live calc
    js_calc = "function calc(n){ var inputs=document.querySelectorAll('input[name^=\"m_'+n+'_\"]'); var t=0,c=0; inputs.forEach(function(i){ if(i.value!==''){ t+=parseInt(i.value); c++; } }); var avg=c? (t/c).toFixed(1):0; document.getElementById('calc_'+n).innerHTML='Total: '+t+' | Average: '+avg+'% | Subjects entered: '+c; inputs.forEach(function(i){ var s=i.name.replace('m_'+n+'_',''); var g=document.getElementById('g_'+n+'_'+s); if(g){ var v=parseInt(i.value); g.innerText = isNaN(v)?'-': v>=75?'A': v>=65?'B': v>=50?'C': v>=40?'D': v>=30?'E':'F'; } }); }"
    return render_template_string(B, c=f"""<div class='top'><b>TEACHER - {session.get('name')} ({session.get('user')})</b><a href='/logout'>Sign Out</a></div><h2>Enter Term Results</h2><p class='s'>Pick class + term. Roster loads automatically. Marks calculate instantly.</p>{m}
    <form method='GET'><div class='grid'><div><label>Class</label><select name='cls'>{opts}</select></div><div><label>Term</label><select name='term'><option {'selected' if term=='Term 1' else ''}>Term 1</option><option {'selected' if term=='Term 2' else ''}>Term 2</option><option {'selected' if term=='Term 3' else ''}>Term 3</option></select></div></div><label>Year</label><input name='year' value='{year}'><button class='btn'>Load Roster for {cls}</button></form>
    <p class='small'>Roster for {cls}: {len(roster)} pupils | Term: {term} {year} | Grading: A 75+, B 65-74, C 50-64, D 40-49, E 30-39, F below 30</p>
    <form method='POST'><input type='hidden' name='action' value='save'><input type='hidden' name='cls' value='{cls}'><input type='hidden' name='term' value='{term}'><input type='hidden' name='year' value='{year}'>
    <table><tr><th>Pupil</th></tr>{rows if rows else '<tr><td>No pupils in this class. Admin must add roster first.</td></tr>'}</table>
    <button class='btn'>Save All Results for {cls} - {term} {year}</button></form>
    <script>{js_calc}</script>""")
# ---- PARENT: Auto knows class ----
@app.route('/verify', methods=['GET','POST'])
def verify():
    if request.method=='POST':
        n=request.form['n'].strip(); t=request.form['term']; y=request.form['year'].strip()
        # Find any result for this pupil + term + year, no need to pick class - system knows it
        found=None
        for k,v in DB["results"].items():
            if v['n']==n and v['t']==t and v['y']==y: found=v; break
        pupil=next((p for p in DB["pupils"] if p['n']==n), None)
        if not found:
            return render_template_string(B, c=f"<div class='al'>No result found for Pupil {n}, {t} {y}. Check number or contact school.</div><p><a href='/verify'>Search Again</a></p>")
        # Position: rank by average in same class+term
        same=[v for v in DB["results"].values() if v['cls']==found['cls'] and v['t']==t and v['y']==y]
        same_sorted=sorted(same, key=lambda x: x.get('avg',0), reverse=True)
        pos=next((i+1 for i,v in enumerate(same_sorted) if v['n']==n), "-")
        rows="".join([f"<tr><td>{s}</td><td>{d['mark'] if d['mark'] else '-'}</td><td>{grade(d['mark'])}</td><td>{d['comment'] if d['comment'] else '-'}</td></tr>" for s,d in found['subs'].items()])
        return render_template_string(B, c=f"""<h2>{found['cls']} - {t} Result - {y}</h2><p class='s'>Mkushi Boarding Secondary School - Term Report</p>
        <table><tr><th>Pupil</th><td>{found['name']}</td></tr><tr><th>Pupil Number</th><td>{n}</td></tr><tr><th>Class</th><td>{found['cls']} {pupil['stream'] if pupil else ''}</td></tr><tr><th>Term</th><td>{t} {y}</td></tr><tr><th>Total</th><td>{found['total']}</td></tr><tr><th>Average</th><td><b>{found['avg']}%</b></td></tr><tr><th>Position in Class</th><td><b>{pos} / {len(same)}</b> (auto-calculated)</td></tr></table>
        <h3 style='margin-top:16px'>Subjects & Teacher Comments</h3><table><tr><th>Subject</th><th>Mark %</th><th>Grade</th><th>Teacher Comment</th></tr>{rows}</table>
        <button class='btn' onclick='window.print()'>Print Term Report</button><p style='text-align:center;margin-top:14px'><a href='/verify'>Check Another Pupil</a></p>""")
    return render_template_string(B, c="""<h2>Check Term Result</h2><p class='s'>For parents & pupils. System will automatically find the class.</p>
    <form method='POST'><label>Pupil Number</label><input name='n' placeholder='e.g. MBS/2026/001' required>
    <label>Term</label><select name='term'><option>Term 1</option><option>Term 2</option><option>Term 3</option></select>
    <label>Year</label><input name='year' placeholder='2026' required>
    <button class='btn'>View Result</button></form><p class='small' style='margin-top:14px'>You do NOT need to know the class - the system knows it from the roster.</p>""")
@app.route('/logout')
def logout(): session.clear(); return redirect('/login')
if __name__=='__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
