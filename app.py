from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "greefo_secret"

# -------- CREATE DATABASE --------
conn = sqlite3.connect("database.db")
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
    print("✅ profile_pic column added")
except Exception as e:
    print("⚠️", e)

# POSTS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    message TEXT,
    time TEXT,
    mood TEXT
)
""")

# REPLIES TABLE  ⭐ ADDED
cur.execute("""
CREATE TABLE IF NOT EXISTS replies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    username TEXT,
    reply TEXT,
    time TEXT
)
""")

# LOGIN ACTIVITY TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS login_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    action TEXT,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ⭐ PRIVATE CHAT TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS private_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    receiver TEXT,
    message TEXT,
    time TEXT
)
""")

conn.commit()
conn.close()

# -------- HOME --------
@app.route("/")
def home():
    return redirect(url_for("login"))

# -------- SIGNUP --------
users = {}

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

# -------- LOGIN --------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        session["user"] = username

        import sqlite3
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO login_activity (username, action) VALUES (?, ?)",
            (username, "login")
        )

        conn.commit()
        conn.close()

        return redirect(url_for("mood"))

    return render_template("login.html")

@app.route("/admin")
def admin():

    if session.get("user") != "admin":
        return "Access Denied"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM posts")
    messages = cursor.fetchall()

    cursor.execute("SELECT * FROM login_activity ORDER BY time DESC")
    activity = cursor.fetchall()

    conn.close()

    return render_template("admin.html", messages=messages, activity=activity) 

# -------- MOOD PAGE --------
@app.route("/mood")
def mood():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("mood.html")

# ⭐ FUNCTION TO HANDLE WALLS
def handle_wall(mood_name, template_name):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # POST MESSAGE
    if request.method == "POST":
        message = request.form["message"]
        user = session["user"]
        time = datetime.now().strftime("%Y-%m-%d %H:%M")

        cur.execute(
            "INSERT INTO posts (user, message, time, mood) VALUES (?, ?, ?, ?)",
            (user, message, time, mood_name)
        )
        conn.commit()


    # GET POSTS
    cur.execute("SELECT * FROM posts WHERE mood=? ORDER BY id DESC", (mood_name,))
    posts = cur.fetchall()

    # GET REPLIES
    cur.execute("SELECT * FROM replies ORDER BY id ASC")
    replies = cur.fetchall()

    # ⭐ GET USER PROFILE PICS
    try:
        cur.execute("SELECT username, profile_pic FROM users")
        user_pics = dict(cur.fetchall())
    except:
        user_pics = {}

    conn.close()

    return render_template(template_name, messages=posts, replies=replies, user_pics=user_pics)
# -------- HAPPY --------
@app.route("/happy", methods=["GET", "POST"])
def happy():
    return handle_wall("happy", "happy.html")

# -------- SAD --------
@app.route("/sad", methods=["GET", "POST"])
def sad():
    return handle_wall("sad", "sad.html")

# -------- TALK --------
@app.route("/talk", methods=["GET", "POST"])
def talk():
    return handle_wall("talk", "talk.html")

# -------- CHILL --------
@app.route("/chill", methods=["GET", "POST"])
def chill():
    return handle_wall("chill", "chill.html")

# -------- DELETE POST --------
@app.route("/delete_message/<int:id>", methods=["POST"])
def delete_message(id):

    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get the post owner
    cursor.execute("SELECT user FROM posts WHERE id=?", (id,))
    post = cursor.fetchone()

    if not post:
        conn.close()
        return "Post not found"

    post_owner = post[0]

    # Allow if admin OR owner
    if session["user"] != "admin" and session["user"] != post_owner:
        conn.close()
        return "Access Denied"

    cursor.execute("DELETE FROM posts WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(request.referrer or url_for("mood"))

# -------- REPLY --------
@app.route("/reply/<int:post_id>", methods=["POST"])
def reply(post_id):
    if "user" not in session:
        return redirect(url_for("login"))

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

# -------- LOGOUT --------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/chat/<username>", methods=["GET", "POST"])
def chat(username):

    if "user" not in session:
        return redirect(url_for("login"))

    sender = session["user"]
    receiver = username

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Send message
    if request.method == "POST":
        message = request.form["message"]
        time = datetime.now().strftime("%Y-%m-%d %H:%M")

        cur.execute(
            "INSERT INTO private_messages (sender, receiver, message, time) VALUES (?, ?, ?, ?)",
            (sender, receiver, message, time)
        )

        conn.commit()

    # Get chat messages
    cur.execute("""
        SELECT sender, message, time, id
        FROM private_messages
        WHERE (sender=? AND receiver=?)
        OR (sender=? AND receiver=?)
        ORDER BY id ASC
    """, (sender, receiver, receiver, sender))

    messages = cur.fetchall()

    conn.close()

    return render_template("chat.html", messages=messages, receiver=receiver)

@app.route("/delete_chat/<int:id>", methods=["POST"])
def delete_chat(id):

    if "user" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM private_messages WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return redirect(request.referrer)
    
# -------- RUN --------
if __name__ == "__main__":
    app.run(debug=True)
