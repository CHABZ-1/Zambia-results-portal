from flask import Flask, render_template, request, redirect, session
import sqlite3, os, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "mkushi2026-final"
os.makedirs("static", exist_ok=True)

SENDER_EMAIL = "chabotamichelo17@gmail.com"
SENDER_PASSWORD = os.getenv("EMAIL_PASSWORD", "PUT-APP-PASSWORD-HERE")

def send_email(to_email, subject, body_html):
    try:
        if "PUT-APP" in SENDER_PASSWORD:
            print("Email not configured")
            return False
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body_html, "html"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {to_email}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def init_db():
    con=sqlite3.connect("mkushi.db")
    c=con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, fullname TEXT, email TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS pupils (id INTEGER PRIMARY KEY, name TEXT, class TEXT, house TEXT, parent_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY, pupil_id INTEGER, subject TEXT, score INTEGER, term TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY, pupil_id INTEGER, date TEXT, status TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS discipline (id INTEGER PRIMARY KEY, pupil_id INTEGER, note TEXT, date TEXT, type TEXT)")
    try:
        c.execute("INSERT INTO users VALUES (NULL,'admin','admin123','admin','Board Admin','chabotamichelo17@gmail.com')")
        c.execute("INSERT INTO users VALUES (NULL,'teacher1','teach123','teacher','Mr. Banda','teacher@test.com')")
        c.execute("INSERT INTO users VALUES (NULL,'parent1','parent123','parent','John Phiri Parent','parent@test.com')")
        c.execute("INSERT INTO users VALUES (NULL,'pupil1','pupil123','pupil','John Phiri Jr','pupil@test.com')")
        c.execute("INSERT INTO pupils VALUES (NULL,'John Phiri Jr','Grade 11','Chankamo',3)")
        con.commit()
    except: pass
    con.close()

init_db()

@app.route("/")
def home(): return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form["username"]; p=request.form["password"]; r=request.form["role"]
        con=sqlite3.connect("mkushi.db"); c=con.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=? AND role=?",(u,p,r))
        user=c.fetchone(); con.close()
        if user:
            session["username"]=user[1]; session["role"]=user[3]; session["user_id"]=user[0]; session["fullname"]=user[4]
            return redirect("/dashboard")
        return render_template("login.html", error="Invalid login")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session: return redirect("/login")
    role=session["role"]; uid=session["user_id"]
    con=sqlite3.connect("mkushi.db"); c=con.cursor()
    if role=="parent":
        c.execute("SELECT * FROM pupils WHERE parent_id=?",(uid,)); pupils=c.fetchall()
        data=[]
        for pup in pupils:
            c.execute("SELECT * FROM results WHERE pupil_id=?",(pup[0],)); res=c.fetchall()
            c.execute("SELECT * FROM attendance WHERE pupil_id=?",(pup[0],)); att=c.fetchall()
            c.execute("SELECT * FROM discipline WHERE pupil_id=?",(pup[0],)); disc=c.fetchall()
            data.append({"pupil":pup,"results":res,"attendance":att,"discipline":disc})
        con.close(); return render_template("parent_dashboard.html", data=data)
    elif role=="pupil":
        c.execute("SELECT * FROM pupils WHERE id=1"); pup=c.fetchone()
        c.execute("SELECT * FROM results WHERE pupil_id=1"); res=c.fetchall()
        c.execute("SELECT * FROM attendance WHERE pupil_id=1"); att=c.fetchall()
        c.execute("SELECT * FROM discipline WHERE pupil_id=1"); disc=c.fetchall()
        con.close(); return render_template("pupil_dashboard.html", pupil=pup, results=res, attendance=att, discipline=disc)
    elif role=="teacher":
        c.execute("SELECT * FROM pupils"); pupils=c.fetchall(); con.close()
        return render_template("teacher_dashboard.html", pupils=pupils)
    else:
        c.execute("SELECT * FROM pupils"); pupils=c.fetchall()
        c.execute("SELECT * FROM users"); users=c.fetchall()
        con.close()
        return render_template("admin_dashboard.html", pupils=pupils, users=users)

@app.route("/upload_logo", methods=["POST"])
def upload_logo():
    if session.get("role")!="admin": return "Admin only", 403
    file=request.files.get("logo")
    if file and file.filename!="":
        file.save(os.path.join("static","logo.png"))
    return redirect("/dashboard")

@app.route("/change_password", methods=["GET","POST"])
def change_password():
    if "username" not in session: return redirect("/login")
    if request.method=="POST":
        old=request.form["old"]; new=request.form["new"]
        con=sqlite3.connect("mkushi.db"); c=con.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?",(session["username"], old))
        if c.fetchone():
            c.execute("UPDATE users SET password=? WHERE username=?",(new, session["username"]))
            con.commit(); con.close()
            return "<h3>Password changed!</h3><a href='/dashboard'>Back</a>"
        con.close()
        return "<h3>Old password wrong</h3><a href='/change_password'>Try again</a>"
    return render_template("change_password.html")

@app.route("/admin/reset/<int:user_id>", methods=["POST"])
def admin_reset(user_id):
    if session.get("role")!="admin": return "Admin only", 403
    new_pass=request.form["new_password"]
    con=sqlite3.connect("mkushi.db"); c=con.cursor()
    c.execute("SELECT username,fullname,email FROM users WHERE id=?",(user_id,))
    u=c.fetchone()
    c.execute("UPDATE users SET password=? WHERE id=?",(new_pass, user_id))
    con.commit(); con.close()
    if u and u[2]:
        body=f"<h3>Hello {u[1]}</h3><p>Password reset by Admin.</p><p>Username: {u[0]}<br>New Password: {new_pass}</p><p>Login: https://zambia-results-portal.onrender.com</p>"
        send_email(u[2], "Mkushi Portal - Password Reset", body)
    return redirect("/dashboard")

@app.route("/forgot", methods=["GET","POST"])
def forgot():
    if request.method=="POST":
        username=request.form["username"]
        con=sqlite3.connect("mkushi.db"); c=con.cursor()
        c.execute("SELECT email,fullname FROM users WHERE username=?",(username,))
        user=c.fetchone(); con.close()
        if user and user[0]:
            body=f"<h3>Hello {user[1]}</h3><p>You requested password reset. Contact Admin: chabotamichelo17@gmail.com</p>"
            send_email(user[0], "Mkushi Portal - Forgot Password", body)
            return f"Email sent to {user[0]}! <a href='/login'>Login</a>"
        return "User not found <a href='/forgot'>Try again</a>"
    return render_template("forgot.html")

@app.route("/logout")
def logout(): session.clear(); return redirect("/login")

if __name__=="__main__": app.run(debug=True)
