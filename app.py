from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "greefo_secret"

# -------- CREATE DATABASE --------
conn = sqlite3.connect("database.db")
cur = conn.cursor()

# USERS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    profile_pic TEXT DEFAULT 'avatar.jpg'
)
""")

try:
    cur.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT")
    print("✅ profile_pic column added")
except Exception as e:
    # Column already exists or table just created
    pass

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

        if not username or not password:
            return render_template("signup.html", error="Username and password are required.")

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        # Check if user already exists
        cur.execute("SELECT id FROM users WHERE username=?", (username,))
        if cur.fetchone():
            conn.close()
            return render_template("signup.html", error="Username already exists. Try another.")

        cur.execute(
            "INSERT INTO users (username, password, profile_pic) VALUES (?, ?, ?)",
            (username, password, "avatar.jpg")
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
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=?", (username,))
        user_data = cursor.fetchone()

        if user_data and user_data[0] == password:
            session["user"] = username
            cursor.execute(
                "INSERT INTO login_activity (username, action) VALUES (?, ?)",
                (username, "login")
            )
            conn.commit()
            conn.close()
            return redirect(url_for("mood"))
        
        conn.close()
        return render_template("login.html", error="Invalid username or password.")

    return render_template("login.html")

@app.route("/admin")
def admin():
    if session.get("user") != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Get all posts
    cursor.execute("SELECT id, user, message, time, mood FROM posts ORDER BY id DESC")
    messages = cursor.fetchall()

    # Get login activity
    cursor.execute("SELECT id, username, action, time FROM login_activity ORDER BY time DESC LIMIT 50")
    activity = cursor.fetchall()
    
    # Get all users (except admin)
    cursor.execute("SELECT id, username, profile_pic FROM users WHERE username != 'admin' ORDER BY id DESC")
    raw_users = cursor.fetchall()
    users = [(u[0], u[1], 'avatar.jpg' if not u[2] or u[2] == 'default.png' else u[2]) for u in raw_users]

    # Calculate Stats
    cursor.execute("SELECT COUNT(*) FROM posts")
    total_posts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM login_activity WHERE action='login'")
    total_logins = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM private_messages")
    total_msgs = cursor.fetchone()[0]

    stats = {
        "total_posts": total_posts,
        "total_users": total_users,
        "total_logins": total_logins,
        "total_msgs": total_msgs
    }

    conn.close()

    return render_template("admin.html", messages=messages, activity=activity, users=users, stats=stats) 

@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
def admin_delete_user(user_id):
    if session.get("user") != "admin":
        return redirect(url_for("login"))
    
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    
    # Get username first to delete their posts/replies if desired
    cur.execute("SELECT username FROM users WHERE id=?", (user_id,))
    user = cur.fetchone()
    
    if user:
        username = user[0]
        cur.execute("DELETE FROM users WHERE id=?", (user_id,))
        cur.execute("DELETE FROM posts WHERE user=?", (username,))
        cur.execute("DELETE FROM replies WHERE username=?", (username,))
        cur.execute("DELETE FROM private_messages WHERE sender=? OR receiver=?", (username, username))
        conn.commit()
        
    conn.close()
    return redirect(url_for("admin"))

@app.route("/admin/clear_posts/<username>", methods=["POST"])
def admin_clear_posts(username):
    if session.get("user") != "admin":
        return redirect(url_for("login"))
    
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM posts WHERE user=?", (username,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

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
        results = cur.fetchall()
        user_pics = {u: (p if p and p != 'default.png' else 'avatar.jpg') for u, p in results}
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
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
