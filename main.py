import sqlite3
import time
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "troia_secret"

ADMIN_USER = "Troia"
ADMIN_PASS = "88691553"

# -------------------
# DATABASE
# -------------------

def init_db():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        credits INTEGER DEFAULT 0,
        total_views INTEGER DEFAULT 0,
        last_visit INTEGER DEFAULT 0
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

# -------------------
# HOME
# -------------------

@app.route("/")
def index():
    return render_template("index.html")

# -------------------
# REGISTER
# -------------------

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO users(username,password) VALUES (?,?)",
            (username,password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# -------------------
# LOGIN
# -------------------

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USER and password == ADMIN_PASS:
            session.clear()
            session["admin"] = True
            return redirect("/admin")

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username,password)
        )

        user = c.fetchone()
        conn.close()

        if user:
            session.clear()
            session["user_id"] = user[0]
            return redirect("/dashboard")

    return render_template("login.html")

# -------------------
# LOGOUT
# -------------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# -------------------
# DASHBOARD
# -------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    user = c.execute(
        "SELECT credits,total_views FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    sites = c.execute(
        "SELECT * FROM sites WHERE user_id=?",
        (session["user_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        credits=user["credits"],
        views=user["total_views"],
        sites=sites
    )

# -------------------
# ADD SITE
# -------------------

@app.route("/addsite", methods=["POST"])
def addsite():

    if "user_id" not in session:
        return redirect("/login")

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

# -------------------
# AUTOSURF
# -------------------

@app.route("/surf")
def surf():

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT id,url FROM sites ORDER BY views ASC LIMIT 1")
    site = c.fetchone()

    conn.close()

    if not site:
        return "Nenhum site cadastrado"

    return render_template("surf.html", site=site)

# -------------------
# VISIT
# -------------------

@app.route("/visit/<int:site_id>")
def visit(site_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    user = c.execute(
        "SELECT last_visit FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()

    now = int(time.time())

    if user and now - user[0] < 10:
        conn.close()
        return redirect("/surf")

    c.execute(
        "UPDATE users SET credits=credits+1,total_views=total_views+1,last_visit=? WHERE id=?",
        (now,session["user_id"])
    )

    c.execute(
        "UPDATE sites SET views=views+1 WHERE id=?",
        (site_id,)
    )

    c.execute(
        "INSERT INTO visits(user_id,site_id,timestamp) VALUES (?,?,?)",
        (session["user_id"],site_id,now)
    )

    conn.commit()
    conn.close()

    return redirect("/surf")

# -------------------
# BUY CREDITS
# -------------------

@app.route("/buy")
def buy():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("buy.html")

# -------------------
# ANALYTICS
# -------------------

@app.route("/analytics")
def analytics():

    if "admin" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    visits = c.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
    users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    sites = c.execute("SELECT COUNT(*) FROM sites").fetchone()[0]

    conn.close()

    return render_template(
        "analytics.html",
        visits=visits,
        users=users,
        sites=sites
    )

# -------------------
# ADMIN PANEL
# -------------------

@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    users = c.execute("SELECT * FROM users").fetchall()

    conn.close()

    return render_template("admin.html", users=users)

# -------------------
# ADMIN ADD CREDITS
# -------------------

@app.route("/admin/addcredits/<int:user_id>", methods=["POST"])
def addcredits(user_id):

    if "admin" not in session:
        return redirect("/login")

    amount = request.form["amount"]

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute(
        "UPDATE users SET credits = credits + ? WHERE id=?",
        (amount,user_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

# -------------------
# ADMIN BAN
# -------------------

@app.route("/admin/ban/<int:user_id>")
def ban(user_id):

    if "admin" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("DELETE FROM users WHERE id=?", (user_id,))

    conn.commit()
    conn.close()

    return redirect("/admin")

# -------------------

if __name__ == "__main__":
    app.run()
