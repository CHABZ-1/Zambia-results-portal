import os, json
from flask import Flask, request, redirect, session, render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
app = Flask(__name__)
app.secret_key = "mkushi-boarding-2026"
F = "data.json"
def load():
    try: return json.load(open(F))
    except: return {"users": {"admin": {"p": generate_password_hash("admin123"), "r": "admin", "name": "School Admin"}}, "pupils": [], "results": {}}
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
ALL_SUBJS = sorted(set(sum(SUBJECTS.values(), [])))
ALL_CLASSES = list(SUBJECTS.keys())
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
<style>body{margin:0;font-family:Arial;background:#ECEEEB;color:#1A1A1A}.h{background:#0B3D2E;color:#fff;padding:14px 20px;border-bottom:3px solid #C9A227}.h b{font-size:16px}.h i{color:#C9A227;font-size:12px}.w{max-width:900px;margin:20px auto;padding:0 12px}.c{background:#fff;border-radius:8px;border:1px solid #D9D9D9;padding:24px}h2{margin:0 0 6px}.s{color:#666;font-size:13px;margin:0 0 18px}label{display:block;font-size:11px;font-weight:700;margin:12px 0 5px;text-transform:uppercase;color:#444}input,select{width:100%;padding:10px;border:1px solid #CFCFCF;border-radius:6px;font-size:14px}.btn{width:100%;padding:13px;background:#0B3D2E;color:#fff;border:none;border-radius:6px;font-size:15px;font-weight:700;margin-top:16px;cursor:pointer}.btn2{background:#C9A227;color:#0B3D2E}a{color:#0B3D2E;font-weight:700;text-decoration:none}.al{background:#FDECEC;border:1px solid #F5C6C6;padding:12px;border-radius:6px;font-size:13px}.ok{background:#EAF5EC;border:1px solid #B9D9BE;padding:12px;border-radius:6px;font-size:13px}table{width:100%;border-collapse:collapse;font-size:13px;margin-top:12px}th{background:#0B3D2E;color:#fff;text-align:left;padding:9px}td{padding:8px;border-bottom:1px solid #E5E5E5;vertical-align:top}.f{text-align:center;color:#777;font-size:12px;margin:20px 0;line-height:1.6}.grid{display:grid;grid-template-columns:1fr 1fr;gap:0 12px}.small{font-size:12px;color:#666}.mark{width:70px!important}.com{width:160px!important}.calc{background:#FFF8E1;padding:10px;border-radius:6px;font-size:13px;margin-top:10px}.top{display:flex;justify-content:space-between;font-size:13px;margin-bottom:12px}.chk{display:flex;flex-wrap:wrap;gap:8px}.chk label{text-transform:none;font-weight:400;font-size:13px;display:flex;align-items:center;gap:5px;margin:0}.chk input{width:auto}</style></head><body>
<div class="h"><b>MKUSHI BOARDING SECONDARY SCHOOL</b><br><i>Discipline & Hardwork Lead to Prosperity</i></div>
<div class="w"><div class="c">{{c|safe}}</div><div class="f">Mkushi Boarding Secondary School &bull; Central Province, Zambia &bull; 2023 Curriculum (3-6-6-3)<br><a href="/parent">Parent / Pupil Login</a> &bull; <a href="/login">Staff Login</a></div></div></body></html>"""
@app.route('/')
def home(): return redirect('/parent')
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        u=DB["users"].get(request.form['username'].strip())
        if u and check_password_hash(u['p'], request.form['password']) and u['r']==request.form['role']:
            session['user']=request.form['username'].strip(); session['role']=u['r']; session['name']=u.get('name','')
            return redirect('/admin' if u['r']=='admin' else '/teacher')
        return render_template_string(B, c="<div class='al'>Invalid credentials.</div><p><a href='/login'>Try Again</a></p>")
    return render_template_string(B, c="""<h2>Staff Login</h2><p class='s'>Admin & Teachers only. Parents use Parent Login.</p>
    <form method='POST'><label>Username</label><input name='username' required><label>Password</label><input name='password' type='password' required>
    <label>Role</label><select name='role'><option value='teacher'>Teacher</option><option value='admin'>Administrator</option></select>
    <button class='btn'>Sign In</button></form><p style='margin-top:14px'><a href='/parent'>Parent / Pupil Login - Exam Number Only &rarr;</a></p>""")
@app.route('/admin', methods=['GET','POST'])
def admin():
    if session.get('role')!='admin': return redirect('/login')
    m=""
    if request.method=='POST':
        a=request.form.get('action')
        if a=='teacher':
            if request.form['u'] in DB["users"]: m="<div class='al'>Username exists.</div>"
            else:
                classes=request.form.getlist('classes')
                DB["users"][request.form['u']]={"p": generate_password_hash(request.form['p']), "r":"teacher", "name": request.form['name'], "subject": request.form['subject'], "classes": classes}; save(DB); m="<div class='ok'>Teacher "+request.form['name']+" registered for "+request.form['subject']+" - "+", ".join(classes)+"</div>"
        elif a=='pupil':
            DB["pupils"].append({"n": request.form['n'].strip(), "name": request.form['name'].strip().title(), "cls": request.form['cls'], "stream": request.form.get('stream','A'), "sex": request.form.get('sex','M')}); save(DB); m="<div class='ok'>Pupil added to roster.</div>"
        elif a=='del_teacher':
            if request.form['u']!='admin': DB["users"].pop(request.form['u'],None); save(DB); m="<div class='ok'>Teacher removed.</div>"
        elif a=='del_pupil':
            DB["pupils"]=[p for p in DB["pupils"] if p['n']!=request.form['n']]; save(DB); m="<div class='ok'>Pupil removed.</div>"
    teachers="".join([f"<tr><td>{v.get('name','')}</td><td>{k}</td><td>{v.get('subject','-')} - {', '.join(v.get('classes',[]))}</td><td>{v['r']}</td><td><form method='POST' style='display:inline'><input type='hidden' name='action' value='del_teacher'><input type='hidden' name='u' value='{k}'><button style='color:red;border:none;background:none;cursor:pointer'>Remove</button></form></td></tr>" for k,v in DB["users"].items() if v['r']=='teacher'])
    pupils="".join([f"<tr><td>{p['n']}</td><td>{p['name']}</td><td>{p['cls']} {p['stream']}</td><td>{p['sex']}</td><td><form method='POST' style='display:inline'><input type='hidden' name='action' value='del_pupil'><input type='hidden' name='n' value='{p['n']}'><button style='color:red;border:none;background:none;cursor:pointer'>Remove</button></form></td></tr>" for p in DB["pupils"]])
    cls_opts="".join([f"<option>{c}</option>" for c in ALL_CLASSES])
    subj_opts="".join([f"<option>{s}</option>" for s in ALL_SUBJS])
    chk="".join([f"<label><input type='checkbox' name='classes' value='{c}'> {c}</label>" for c in ALL_CLASSES])
    return render_template_string(B, c=f"""<div class='top'><b>ADMIN - {session.get('name')}</b><a href='/logout'>Sign Out</a></div><h2>Administration</h2><p class='s'>Admin manages system only. Admin does NOT enter marks.</p>{m}
    <h3>1. Register Teacher</h3><form method='POST'><input type='hidden' name='action' value='teacher'>
    <label>Teacher Full Name</label><input name='name' required><label>Username</label><input name='u' required><label>Password</label><input name='p' type='password' required>
    <label>Assigned Subject (ONE subject)</label><select name='subject'>{subj_opts}</select>
    <label>Assigned Classes (tick all classes they teach)</label><div class='chk'>{chk}</div>
    <button class='btn'>Register Teacher</button></form>
    <h3>Teachers ({len([v for v in DB['users'].values() if v['r']=='teacher'])})</h3><table><tr><th>Name</th><th>Username</th><th>Subject - Classes</th><th>Role</th><th></th></tr>{teachers if teachers else '<tr><td colspan=5>No teachers yet.</td></tr>'}</table><hr>
    <h3>2. Add Pupil to Roster</h3><form method='POST'><input type='hidden' name='action' value='pupil'>
    <div class='grid'><div><label>Pupil / Exam Number</label><input name='n' placeholder='e.g. MBS/2026/001' required></div><div><label>Full Name</label><input name='name' required></div></div>
    <div class='grid'><div><label>Class</label><select name='cls'>{cls_opts}</select></div><div><label>Stream</label><select name='stream'><option>A</option><option>B</option><option>C</option><option>D</option></select></div></div>
    <label>Sex</label><select name='sex'><option>M</option><option>F</option></select>
    <button class='btn btn2'>Add Pupil to Roster</button></form>
    <h3>Roster - All Pupils ({len(DB['pupils'])})</h3><table><tr><th>Pupil No</th><th>Name</th><th>Class</th><th>Sex</th><th></th></tr>{pupils if pupils else '<tr><td colspan=5>No pupils yet.</td></tr>'}</table>""")
@app.route('/teacher', methods=['GET','POST'])
def teacher():
    if session.get('role')!='teacher': return redirect('/admin' if session.get('role')=='admin' else '/login')
    me=DB["users"][session['user']]
    my_subj=me.get('subject','Mathematics'); my_classes=me.get('classes',["Form 1"])
    cls=request.args.get('cls', my_classes[0]) if request.method=='GET' else request.form.get('cls', my_classes[0])
    if cls not in my_classes: cls=my_classes[0]
    term=request.args.get('term','Term 1') if request.method=='GET' else request.form.get('term','Term 1')
    year=request.args.get('year','2026') if request.method=='GET' else request.form.get('year','2026')
    m=""
    if request.method=='POST' and request.form.get('action')=='save':
        for p in [x for x in DB["pupils"] if x['cls']==cls]:
            key=f"{p['n']}|{cls}|{term}|{year}"
            old=DB["results"].get(key, {"subs": {}})
            subs=dict(old.get("subs", {}))
            subs[my_subj]={"mark": request.form.get(f"m_{p['n']}", ''), "comment": request.form.get(f"c_{p['n']}", '')}
            vals=[int(d['mark']) for d in subs.values() if d.get('mark') and str(d['mark']).isdigit()]
            total=sum(vals); avg=round(total/len(vals),1) if vals else 0
            DB["results"][key]={"n": p['n'], "name": p['name'], "cls": cls, "t": term, "y": year, "subs": subs, "total": total, "avg": avg, "teacher": session.get('name')}
        save(DB); m=f"<div class='ok'>{my_subj} results saved for {cls} - {term} {year}. Total & Average auto-calculated.</div>"
    roster=[p for p in DB["pupils"] if p['cls']==cls]
    rows=""
    for p in roster:
        key=f"{p['n']}|{cls}|{term}|{year}"; old=DB["results"].get(key, {"subs": {}}); d=old['subs'].get(my_subj, {"mark":"","comment":""})
        rows+=f"<tr><td>{p['n']}<br><b>{p['name']}</b></td><td><input class='mark' name='m_{p['n']}' type='number' min='0' max='100' value='{d['mark']}' oninput='calc(\"{p['n']}\")'></td><td><span id='g_{p['n']}'>{grade(d['mark'])}</span></td><td><input class='com' name='c_{p['n']}' placeholder='e.g. Good effort, work on...' value='{d['comment']}'></td><td><div class='calc' id='calc_{p['n']}'>Total: - | Avg: -</div></td></tr>"
    cls_opts="".join([f"<option {'selected' if c==cls else ''}>{c}</option>" for c in my_classes])
    js_calc="function calc(n){ var i=document.querySelector('input[name=\"m_'+n+'\"]'); var v=parseInt(i.value); document.getElementById('g_'+n).innerText=isNaN(v)?'-':v>=75?'A':v>=65?'B':v>=50?'C':v>=40?'D':v>=30?'E':'F'; document.getElementById('calc_'+n).innerText='This subject: '+i.value+'% | Grade: '+document.getElementById('g_'+n).innerText; }"
    return render_template_string(B, c=f"""<div class='top'><b>TEACHER - {session.get('name')}</b><a href='/logout'>Sign Out</a></div><h2>Enter Results - {my_subj}</h2><p class='s'>You are assigned to <b>{my_subj}</b> for <b>{', '.join(my_classes)}</b> only. You cannot enter other subjects or classes.</p>{m}
    <form method='GET'><div class='grid'><div><label>My Class</label><select name='cls'>{cls_opts}</select></div><div><label>Term</label><select name='term'><option {'selected' if term=='Term 1' else ''}>Term 1</option><option {'selected' if term=='Term 2' else ''}>Term 2</option><option {'selected' if term=='Term 3' else ''}>Term 3</option></select></div></div><label>Year</label><input name='year' value='{year}'><button class='btn'>Load Roster for {cls}</button></form>
    <p class='small'>Roster: {cls} - {len(roster)} pupils | Term: {term} {year} | Grading: A 75+, B 65-74, C 50-64, D 40-49, E 30-39, F below 30</p>
    <form method='POST'><input type='hidden' name='action' value='save'><input type='hidden' name='cls' value='{cls}'><input type='hidden' name='term' value='{term}'><input type='hidden' name='year' value='{year}'>
    <table><tr><th>Pupil</th><th>Mark %</th><th>Grade</th><th>Teacher Comment for {my_subj}</th><th>Auto Calc</th></tr>{rows if rows else '<tr><td colspan=5>No pupils in this class. Admin must add roster first.</td></tr>'}</table>
    <button class='btn'>Save {my_subj} Results for {cls} - {term} {year}</button></form><script>{js_calc}</script>""")
@app.route('/parent', methods=['GET','POST'])
def parent():
    if request.method=='POST':
        n=request.form['n'].strip()
        pupil=next((p for p in DB["pupils"] if p['n']==n), None)
        if not pupil: return render_template_string(B, c=f"<div class='al'>Pupil Number {n} not found. Check the number or contact school office.</div><p><a href='/parent'>Try Again</a></p>")
        my=[v for v in DB["results"].values() if v['n']==n]
        if not my: return render_template_string(B, c=f"<div class='ok'>Welcome, {pupil['name']} ({pupil['cls']} {pupil['stream']}).<br><br>No results published yet. Contact class teacher.</div><p><a href='/parent'>Check Another Pupil</a></p>")
        my=sorted(my, key=lambda x: (x['y'], x['t']))
        blocks=""
        for v in my:
            same=[x for x in DB["results"].values() if x['cls']==v['cls'] and x['t']==v['t'] and x['y']==v['y']]
            same_sorted=sorted(same, key=lambda x: x.get('avg',0), reverse=True)
            pos=next((i+1 for i,x in enumerate(same_sorted) if x['n']==n), "-")
            rows="".join([f"<tr><td>{s}</td><td>{d['mark'] if d['mark'] else '-'}</td><td>{grade(d['mark'])}</td><td>{d['comment'] if d['comment'] else '-'}</td></tr>" for s,d in v['subs'].items()])
            blocks+=f"""<hr><h3>{v['cls']} - {v['t']} {v['y']}</h3><table><tr><th>Total</th><td>{v['total']}</td></tr><tr><th>Average</th><td><b>{v['avg']}%</b></td></tr><tr><th>Position</th><td><b>{pos} / {len(same)}</b> (auto-calculated)</td></tr></table><table><tr><th>Subject</th><th>Mark %</th><th>Grade</th><th>Teacher Comment</th></tr>{rows}</table>"""
        return render_template_string(B, c=f"""<h2>Parent Portal - {pupil['name']}</h2><p class='s'>Pupil Number: {n} | Class: {pupil['cls']} {pupil['stream']} | Mkushi Boarding Secondary School</p><p class='small'>Showing all published term results. No password needed - Exam Number is your login.</p>{blocks}<button class='btn' onclick='window.print()'>Print All Term Reports</button><p style='text-align:center;margin-top:14px'><a href='/parent'>Check Another Pupil</a> | <a href='/login'>Staff Login</a></p>""")
    return render_template_string(B, c="""<h2>Parent / Pupil Login</h2><p class='s'>No password needed. Your child's Exam Number is your login.</p>
    <form method='POST'><label>Pupil / Exam Number</label><input name='n' placeholder='e.g. MBS/2026/001' required>
    <button class='btn'>View My Child's Results</button></form>
    <p class='small' style='margin-top:14px'>Keep this number private - anyone with it can see the results, just like a password.</p><p style='margin-top:14px'><a href='/login'>Staff Login (Teachers & Admin) &rarr;</a></p>""")
@app.route('/verify')
def verify_old(): return redirect('/parent')
@app.route('/logout')
def logout(): session.clear(); return redirect('/parent')
if __name__=='__main__': app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
