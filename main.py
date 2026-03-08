import sqlite3
import random
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# -----------------------------
# CRIAR BANCO DE DADOS
# -----------------------------
def init_db():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# -----------------------------
# PAGINA PRINCIPAL
# -----------------------------
@app.route("/")
def index():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM sites")
    sites = c.fetchall()

    conn.close()

    return render_template("index.html", sites=sites)

# -----------------------------
# ADICIONAR SITE
# -----------------------------
@app.route("/add", methods=["GET","POST"])
def add_site():

    if request.method == "POST":

        url = request.form["url"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()

        c.execute("INSERT INTO sites (url) VALUES (?)",(url,))
        conn.commit()

        conn.close()

        return redirect("/")

    return render_template("add.html")

# -----------------------------
# SURFAR SITES
# -----------------------------
@app.route("/surf")
def surf():

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT url FROM sites")
    sites = c.fetchall()

    conn.close()

    if len(sites) == 0:
        return "Nenhum site cadastrado"

    site = random.choice(sites)[0]

    return render_template("surf.html", site=site)


# -----------------------------
# RODAR SERVIDOR
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
