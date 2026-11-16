import os, sqlite3
from flask import Flask, render_template, request, redirect, flash, session, g, send_from_directory

app = Flask(__name__)
app.secret_key = "zafika-key-2026"
DATABASE = "zafika.db"

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# init - safe
try:
    con = sqlite3.connect(DATABASE)
    con.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS pupils (id INTEGER PRIMARY KEY, full_name TEXT, grade TEXT)")
    if not con.execute("SELECT id FROM users WHERE username='admin'").fetchone():
        con.execute("INSERT INTO users VALUES (NULL,'admin','admin123','admin')")
        con.execute("INSERT INTO users VALUES (NULL,'teacher','teacher123','teacher')")
    con.commit()
    con.close()
except Exception as e:
    print("DB init error", e)

@app.route("/")
def home():
    return redirect("/login")

@app.route("/IMG_2053.jpeg")
@app.route("/static/IMG_2053.jpeg")
def logo():
    if os.path.exists("static/IMG_2053.jpeg"):
        return send_from_directory("static","IMG_2053.jpeg")
    if os.path.exists("IMG_2053.jpeg"):
        return send_from_directory(".","IMG_2053.jpeg")
    return "", 204

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username","").strip()
        p = request.form.get("password","").strip()
        try:
            con = get_db()
            user = con.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p)).fetchone()
            if user:
                session["user_id"]=user["id"]
                session["username"]=user["username"]
                session["role"]=user["role"]
                if user["role"]=="admin":
                    return redirect("/admin/panel")
                return redirect("/teacher/upload")
        except Exception as e:
            print(e)
        flash("Wrong login","error")
    try:
        return render_template("login.html")
    except Exception as e:
        return f"<h1>Login</h1><p>Template error: {e}</p><form method=POST><input name=username><input name=password type=password><button>Login</button></form>"

@app.route("/admin/panel", methods=["GET","POST"])
def admin_panel():
    if "user_id" not in session:
        return redirect("/login")
    con = get_db()
    if request.method == "POST":
        tn = request.form.get("teacher_username") or request.form.get("username")
        tp = request.form.get("teacher_password") or request.form.get("password")
        if tn and tp:
            try:
                con.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)",(tn.strip(),tp.strip(),"teacher"))
                con.commit()
                flash("Teacher "+tn+" created","success")
            except:
                flash("Teacher exists","error")
            return redirect("/admin/panel")
    teachers = con.execute("SELECT * FROM users WHERE role='teacher'").fetchall()
    return render_template("admin_panel.html", teachers=teachers, pupils=[])

@app.route("/teacher/upload")
def t_upload():
    return "<h1>Teacher Upload</h1><a href=/admin/panel>Admin Panel</a> | <a href=/login>Login</a>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
