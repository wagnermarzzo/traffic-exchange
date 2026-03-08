import psycopg2
import time
from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "troia_secret"

ADMIN_USER = "Troia"
ADMIN_PASS = "88691553"

DATABASE_URL = "postgresql://trafego_user:GgcNTPBOIucenU5kVj98quHFlv1SqKjj@dpg-d6mrvrp4tr6s738ljfgg-a/trafego"

def get_db():
    return psycopg2.connect(DATABASE_URL)

def init_db():

    conn = get_db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT,
        password TEXT,
        credits INTEGER DEFAULT 0,
        total_views INTEGER DEFAULT 0,
        last_visit INTEGER DEFAULT 0
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS sites(
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        url TEXT,
        views INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        c = conn.cursor()

        c.execute(
            "INSERT INTO users(username,password) VALUES (%s,%s)",
            (username,password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["admin"] = True
            return redirect("/admin")

        conn = get_db()
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username,password)
        )

        user = c.fetchone()

        conn.close()

        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    c.execute(
        "SELECT credits,total_views FROM users WHERE id=%s",
        (session["user_id"],)
    )

    user = c.fetchone()

    c.execute(
        "SELECT * FROM sites WHERE user_id=%s",
        (session["user_id"],)
    )

    sites = c.fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        credits=user[0],
        views=user[1],
        sites=sites
    )

@app.route("/buycredits")
def buycredits():

    if "user_id" not in session:
        return redirect("/login")

    return render_template("buycredits.html")

@app.route("/addsite", methods=["POST"])
def addsite():

    if "user_id" not in session:
        return redirect("/login")

    url = request.form["url"]

    conn = get_db()
    c = conn.cursor()

    c.execute(
        "INSERT INTO sites(user_id,url) VALUES (%s,%s)",
        (session["user_id"],url)
    )

    conn.commit()
    conn.close()

    return redirect("/dashboard")

@app.route("/surf")
def surf():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT id,url FROM sites ORDER BY RANDOM() LIMIT 1")

    site = c.fetchone()

    conn.close()

    if not site:
        return "Nenhum site cadastrado"

    url = site[1]

    if "youtube.com/watch?v=" in url:
        video = url.split("v=")[1]
        url = f"https://www.youtube.com/embed/{video}"

    site = (site[0], url)

    return render_template("surf.html", site=site)

@app.route("/visit/<int:site_id>")
def visit(site_id):

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    now = int(time.time())

    c.execute(
        "UPDATE users SET credits=credits+1,total_views=total_views+1,last_visit=%s WHERE id=%s",
        (now,session["user_id"])
    )

    c.execute(
        "UPDATE sites SET views=views+1 WHERE id=%s",
        (site_id,)
    )

    conn.commit()
    conn.close()

    return redirect("/surf")

@app.route("/admin")
def admin():

    if "admin" not in session:
        return redirect("/login")

    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT * FROM users")
    users = c.fetchall()

    conn.close()

    return render_template("admin.html", users=users)

@app.route("/admin/addcredits/<int:user_id>", methods=["POST"])
def addcredits(user_id):

    amount = request.form["amount"]

    conn = get_db()
    c = conn.cursor()

    c.execute(
        "UPDATE users SET credits = credits + %s WHERE id=%s",
        (amount,user_id)
    )

    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/admin/ban/<int:user_id>")
def ban(user_id):

    conn = get_db()
    c = conn.cursor()

    c.execute("DELETE FROM users WHERE id=%s", (user_id,))

    conn.commit()
    conn.close()

    return redirect("/admin")

if __name__ == "__main__":
    app.run()
