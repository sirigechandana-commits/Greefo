from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "greefo_secret"

# ---------- INIT DATABASE ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        profile_pic TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT,
        message TEXT,
        time TEXT,
        mood TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS replies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER,
        username TEXT,
        reply TEXT,
        time TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- HOME ----------
@app.route("/")
def home():
    return redirect(url_for("login"))

# ---------- SIGNUP ----------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
            (username, password, "default.png")
        )

        conn.commit()
        conn.close()

        return redirect(url_for("login"))

    return render_template("signup.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["user"] = request.form["username"]
        return redirect(url_for("mood"))
    return render_template("login.html")

# ---------- MOOD ----------
@app.route("/mood")
def mood():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("mood.html")

# ---------- WALL FUNCTION ----------
def handle_wall(mood_name, template_name):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":
        message = request.form["message"]
        user = session["user"]
        time = datetime.now().strftime("%Y-%m-%d %H:%M")

        cur.execute(
            "INSERT INTO posts (user, message, time, mood) VALUES (?, ?, ?, ?)",
            (user, message, time, mood_name)
        )
        conn.commit()

    cur.execute("SELECT * FROM posts WHERE mood=? ORDER BY id DESC", (mood_name,))
    posts = cur.fetchall()

    cur.execute("SELECT * FROM replies ORDER BY id ASC")
    replies = cur.fetchall()

    cur.execute("SELECT username, profile_pic FROM users")
    user_pics = dict(cur.fetchall())

    conn.close()

    return render_template(template_name, messages=posts, replies=replies, user_pics=user_pics)

# ---------- ROUTES ----------
@app.route("/happy", methods=["GET", "POST"])
def happy():
    return handle_wall("happy", "happy.html")

@app.route("/sad", methods=["GET", "POST"])
def sad():
    return handle_wall("sad", "sad.html")

@app.route("/talk", methods=["GET", "POST"])
def talk():
    return handle_wall("talk", "talk.html")

@app.route("/chill", methods=["GET", "POST"])
def chill():
    return handle_wall("chill", "chill.html")

# ---------- DELETE ----------
@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM posts WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer)

@app.route("/reply/<int:post_id>", methods=["POST"])
def reply(post_id):
    reply_text = request.form["reply"]
    username = session["user"]
    time = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO replies (post_id, username, reply, time) VALUES (?, ?, ?, ?)",
        (post_id, username, reply_text, time)
    )
    conn.commit()
    conn.close()

    return redirect(request.referrer)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)