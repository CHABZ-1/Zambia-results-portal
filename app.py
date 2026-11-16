from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3, os

app = Flask(__name__)
app.secret_key = "mkushi-boarding-secret-2024"
DB = "mkushi.db"

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users 
    (id INTEGER PRIMARY KEY, username TEXT UNIQUE, email TEXT, password TEXT, role TEXT)''')
    # Create default users if not exist
    cur = conn.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        conn.execute("INSERT INTO users (username,email,password,role) VALUES (?,?,?,?)",
        ("admin","chabotamichelo17@gmail.com",generate_password_hash("admin123"),"admin"))
        conn.execute("INSERT INTO users (username,email,password,role) VALUES (?,?,?,?)",
        ("teacher1","teacher@test.com",generate_password_hash("teacher123"),"teacher"))
        conn.execute("INSERT INTO users (username,email,password,role) VALUES (?,?,?,?)",
        ("parent1","parent@test.com",generate_password_hash("parent123"),"parent"))
        conn.execute("INSERT INTO users (username,email,password,role) VALUES (?,?,?,?)",
        ("pupil1","pupil@test.com",generate_password_hash("pupil123"),"pupil"))
        conn.commit()
    conn.close()

init_db()

@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        role = request.form.get("role","admin")
        # For admin/teacher - username/password
        if role in ["admin","teacher"]:
            username = request.form.get("username")
            password = request.form.get("password")
            conn=get_db()
            user=conn.execute("SELECT * FROM users WHERE username=? AND role=?",(username,role)).fetchone()
            conn.close()
            if user and check_password_hash(user["password"], password):
                session["username"]=user["username"]
                session["role"]=user["role"]
                if role=="admin": return redirect("/admin")
                else: return redirect("/teacher")
            flash("Invalid username or password","danger")
        else:
            # For parent/pupil - simple demo login
            child_name=request.form.get("child_name")
            if child_name:
                session["username"]=child_name
                session["role"]=role
                if role=="parent": return redirect("/parent")
                else: return redirect("/pupil")
            flash("Please enter child name","danger")
    return render_template("login.html")

@app.route("/admin")
def admin():
    if session.get("role")!="admin": return redirect("/")
    conn=get_db()
    users=conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return render_template("admin_dashboard.html", users=users)

@app.route("/add_user", methods=["POST"])
def add_user():
    if session.get("role")!="admin": return redirect("/")
    username=request.form.get("username")
    email=request.form.get("email")
    password=request.form.get("password")
    role=request.form.get("role","teacher")
    if username and password:
        try:
            conn=get_db()
            conn.execute("INSERT INTO users (username,email,password,role) VALUES (?,?,?,?)",
            (username,email,generate_password_hash(password),role))
            conn.commit()
            conn.close()
            flash(f"{role} {username} added successfully!","success")
        except:
            flash("Username already exists","danger")
    return redirect("/admin")

@app.route("/reset_password", methods=["POST"])
def reset_password():
    if session.get("role")!="admin": return redirect("/")
    username=request.form.get("username")
    new_password=request.form.get("new_password")
    if username and new_password:
        conn=get_db()
        conn.execute("UPDATE users SET password=? WHERE username=?",
        (generate_password_hash(new_password), username))
        conn.commit()
        conn.close()
        flash(f"Password reset for {username}","success")
    return redirect("/admin")

@app.route("/change_password", methods=["POST"])
def change_password():
    username=session.get("username")
    new_password=request.form.get("new_password")
    if username and new_password:
        conn=get_db()
        conn.execute("UPDATE users SET password=? WHERE username=?",
        (generate_password_hash(new_password), username))
        conn.commit()
        conn.close()
        flash("Password changed","success")
    return redirect("/admin")

@app.route("/teacher")
def teacher():
    if session.get("role") not in ["teacher","admin"]: return redirect("/")
    return render_template("teacher.html")

@app.route("/parent")
def parent():
    if session.get("role") not in ["parent","admin"]: return redirect("/")
    return render_template("parent.html")

@app.route("/pupil")
def pupil():
    if session.get("role") not in ["pupil","admin"]: return redirect("/")
    return render_template("pupil.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__=="__main__":
    app.run(debug=True)
