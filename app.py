from flask import Flask, render_template, request, redirect, jsonify
from models import db, User, HungerLog
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import time
import os
from sqlalchemy import text

# --- App Setup ---
app = Flask(__name__)

from dotenv import load_dotenv
load_dotenv()

# --- Secure Config (Railway-ready) ---
db_url = os.getenv("DATABASE_URL")

if db_url and db_url.startswith("mysql://"):
    db_url = db_url.replace("mysql://", "mysql+pymysql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback_secret_key")

db.init_app(app)

# Test connection
# Test DB connection
try:
    with app.app_context():
        result = db.session.execute(text('SELECT 1'))
        print("DB connection OK:", result.scalar())
except Exception as e:
    print("DB connection failed:", e)

# --- Login Manager ---
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# --- Load User ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Initialize DB ---
with app.app_context():
    db.create_all()

# --- Hunger Logic ---
def update_hunger(user):
    now = time.time()
    elapsed = now - (user.last_updated or now)
    increment = int(elapsed / 5)
    user.hunger = min(100, user.hunger + increment)
    user.last_updated = now
    db.session.commit()

# --- Routes ---
@app.route("/")
@login_required
def index():
    update_hunger(current_user)
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if User.query.filter_by(username=username).first():
            return "Username already exists!"

        hashed_password = generate_password_hash(password)

        user = User(
            username=username,
            password=hashed_password,
            last_updated=time.time(),
            hunger=0
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect("/")
        else:
            return "Invalid username or password!"

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

# --- API Endpoints ---
@app.route("/api/hunger")
@login_required
def get_hunger():
    update_hunger(current_user)
    return jsonify({"hunger": current_user.hunger})

@app.route("/api/eat", methods=["POST"])
@login_required
def eat():
    update_hunger(current_user)

    current_user.hunger = max(0, current_user.hunger - 20)

    log = HungerLog(
        user_id=current_user.id,
        hunger=current_user.hunger
    )

    db.session.add(log)
    db.session.commit()

    return jsonify({"hunger": current_user.hunger})

@app.route("/api/history")
@login_required
def history():
    logs = HungerLog.query.filter_by(user_id=current_user.id)\
        .order_by(HungerLog.timestamp.asc()).all()

    data = [
        {
            "time": l.timestamp.strftime("%H:%M:%S"),
            "hunger": l.hunger
        }
        for l in logs
    ]

    return jsonify(data)

# --- Run App (Railway compatible) ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)