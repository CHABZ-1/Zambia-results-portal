from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "mkushi2026"
UPLOAD_FOLDER = "static"
ALLOWED = {"png","jpg","jpeg"}
app.config["UPLOAD_FOLDER"]=UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    con=sqlite3.connect("mkushi.db"); c=con.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT, fullname TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS pupils (id INTEGER PRIMARY KEY, name TEXT, class TEXT, house TEXT, parent_id INTEGER)")
    c.execute("CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY, pupil_id INTEGER, subject TEXT, score INTEGER, term TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY, pupil_id INTEGER, date TEXT, status TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS discipline (id INTEGER PRIMARY KEY, pupil_id INTEGER, note TEXT, date TEXT, type TEXT)")
    try:
        c.execute("INSERT INTO users VALUES (NULL,'admin','admin123','admin','Board Admin')")
        c.execute("INSERT INTO users VALUES (NULL,'teacher1','teach123','teacher','Mr. Banda')")
        c.execute("INSERT INTO users VALUES (NULL,'parent1','parent123','parent','John Phiri Parent')")
        c.execute("INSERT INTO users VALUES (NULL,'pupil1','pupil123','pupil','John Phiri Jr')")
        c.execute("INSERT INTO pupils VALUES (NULL,'John Phiri Jr','Grade 11','Chankamo',3)")
        con.commit()
    except: pass
    con.close()

init_db()

@app.route("/")
def home():
    return redirect("/login")

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
    logo_exists = os.path.exists("static/logo.png")
    if role=="parent":
        c.execute("SELECT * FROM pupils WHERE parent_id=?",(uid,)); pupils=c.fetchall()
        data=[]
        for pup in pupils:
            c.execute("SELECT * FROM results WHERE pupil_id=?",(pup[0],)); res=c.fetchall()
            c.execute("SELECT * FROM attendance WHERE pupil_id=?",(pup[0],)); att=c.fetchall()
            c.execute("SELECT * FROM discipline WHERE pupil_id=?",(pup[0],)); disc=c.fetchall()
            data.append({"pupil":pup,"results":res,"attendance":att,"discipline":disc})
        con.close(); return render_template("parent_dashboard.html", data=data, logo_exists=logo_exists)
    elif role=="pupil":
        c.execute("SELECT * FROM pupils WHERE id=1"); pup=c.fetchone()
        c.execute("SELECT * FROM results WHERE pupil_id=1"); res=c.fetchall()
        c.execute("SELECT * FROM attendance WHERE pupil_id=1"); att=c.fetchall()
        c.execute("SELECT * FROM discipline WHERE pupil_id=1"); disc=c.fetchall()
        con.close(); return render_template("pupil_dashboard.html", pupil=pup, results=res, attendance=att, discipline=disc, logo_exists=logo_exists)
    elif role=="teacher":
        c.execute("SELECT * FROM pupils"); pupils=c.fetchall(); con.close()
        return render_template("teacher_dashboard.html", pupils=pupils, logo_exists=logo_exists)
    else:
        c.execute("SELECT * FROM pupils"); pupils=c.fetchall(); con.close()
        return render_template("admin_dashboard.html", pupils=pupils, logo_exists=logo_exists)

@app.route("/upload_logo", methods=["POST"])
def upload_logo():
    if session.get("role")!="admin": return "Not allowed", 403
    if "logo" not in request.files: return redirect("/dashboard")
    file=request.files["logo"]
    if file.filename=="": return redirect("/dashboard")
    # Always save as logo.png so all pages see it
    file.save(os.path.join(app.config["UPLOAD_FOLDER"],"logo.png"))
    return redirect("/dashboard")

@app.route("/logout")
def logout():
    session.clear(); return redirect("/login")

if __name__=="__main__":
    app.run(debug=True)
