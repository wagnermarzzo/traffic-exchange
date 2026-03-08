import sqlite3
import random
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "troia_secret_key"

ADMIN_USER = "Troia"
ADMIN_PASS = "88691553"

# -----------------------
# BANCO DE DADOS
# -----------------------

def init_db():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        credits INTEGER DEFAULT 10
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS sites(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        url TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------
# HOME
# -----------------------

@app.route("/")
def index():
    return render_template("index.html")

# -----------------------
# REGISTRO
# -----------------------

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("INSERT INTO users (username,password) VALUES (?,?)",(username,password))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# -----------------------
# LOGIN
# -----------------------

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # LOGIN ADMIN
        if username == ADMIN_USER and password == ADMIN_PASS:

            session["admin"] = True
            return redirect("/admin")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=? AND password=?",(username,password))
        user = c.fetchone()

        conn.close()

        if user:

            session["user_id"] = user[0]
            return redirect("/dashboard")

    return render_template("login.html")

# -----------------------
# DASHBOARD USUARIO
# -----------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT credits FROM users WHERE id=?",(user_id,))
    credits = c.fetchone()[0]

    c.execute("SELECT url FROM sites WHERE user_id=?",(user_id,))
    sites = c.fetchall()

    conn.close()

    return render_template("dashboard.html",credits=credits,sites=sites)

# -----------------------
# ADICIONAR SITE
# -----------------------

@app.route("/add", methods=["GET","POST"])
def add_site():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        url = request.form["url"]
        user_id = session["user_id"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("INSERT INTO sites (user_id,url) VALUES (?,?)",(user_id,url))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("add.html")

# -----------------------
# SURF
# -----------------------

@app.route("/surf")
def surf():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id,url FROM sites")
    sites = c.fetchall()

    conn.close()

    if len(sites) == 0:
        return "Nenhum site disponível"

    site = random.choice(sites)

    return render_template("surf.html",site=site[1],site_id=site[0])

# -----------------------
# GANHAR CREDITOS
# -----------------------

@app.route("/reward/<site_id>")
def reward(site_id):

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("UPDATE users SET credits = credits + 1 WHERE id=?",(user_id,))

    conn.commit()
    conn.close()

    return redirect("/surf")

# -----------------------
# PAINEL ADMIN
# -----------------------
