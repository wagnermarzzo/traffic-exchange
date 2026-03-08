import sqlite3
import random
import time
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "troia_secret"

ADMIN_USER = "Troia"
ADMIN_PASS = "88691553"

# -------------------------
# DATABASE
# -------------------------

def init_db():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        credits INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS sites(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        url TEXT,
        views INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS visits(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        site_id INTEGER,
        timestamp INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -------------------------
# HOME
# -------------------------

@app.route("/")
def index():
    return render_template("index.html")

# -------------------------
# REGISTER
# -------------------------

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("INSERT INTO users(username,password) VALUES (?,?)",(username,password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# -------------------------
# LOGIN
# -------------------------

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username,password))
        user = c.fetchone()

        conn.close()

        if user:
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect("/dashboard")

    return render_template("login.html")

# -------------------------
# DASHBOARD
# -------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT credits FROM users WHERE id=?", (session["user_id"],))
    credits = c.fetchone()[0]

    c.execute("SELECT * FROM sites WHERE user_id=?", (session["user_id"],))
    sites = c.fetchall()

    conn.close()

    return render_template("dashboard.html",credits=credits,sites=sites)

# -------------------------
# ADD SITE
# -------------------------

@app.route("/addsite", methods=["POST"])
def addsite():

    url = request.form["url"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "INSERT INTO sites(user_id,url) VALUES (?,?)",
        (session["user_id"],url)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# -------------------------
# SURF
# -------------------------

@app.route("/surf")
def surf():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id,url FROM sites")
    sites = c.fetchall()

    if len(sites) == 0:
        return "Nenhum site"

    site = random.choice(sites)

    conn.close()

    return render_template("surf.html",site=site)

# -------------------------
# VISIT CREDIT
# -------------------------

@app.route("/visit/<int:site_id>")
def visit(site_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE users SET credits = credits + 1 WHERE id=?", (session["user_id"],))

    c.execute("UPDATE sites SET views = views + 1 WHERE id=?", (site_id,))

    c.execute(
        "INSERT INTO visits(user_id,site_id,timestamp) VALUES (?,?,?)",
        (session["user_id"],site_id,int(time.time()))
    )

    conn.commit()
    conn.close()

    return redirect("/surf")

# -------------------------
# BUY CREDITS (PIX)
# -------------------------

@app.route("/buy")
def buy():
    return render_template("buy.html")

# -------------------------
# ADMIN PANEL
# -------------------------

@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users")
    users = c.fetchall()

    c.execute("SELECT COUNT(*) FROM visits")
    visits = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM sites")
    sites = c.fetchone()[0]

    conn.close()

    return render_template("admin.html",users=users,visits=visits,sites=sites)

# -------------------------
# ADMIN CREDIT EDIT
# -------------------------

@app.route("/addcredit/<int:user_id>")
def addcredit(user_id):

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE users SET credits = credits + 50 WHERE id=?", (user_id,))

    conn.commit()
    conn.close()

    return redirect("/admin")

# -------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
