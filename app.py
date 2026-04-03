from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sqlalchemy import text

# Flask App Configuration

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# XAMPP MySQL configuration using root with no password
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/hunger_app'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Database Models

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    hunger_entries = db.relationship('HungerEntry', backref='user', lazy=True)

class HungerEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# Routes

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Use SQLAlchemy 2.x compatible get
    user = db.session.get(User, session['user_id'])
    
    entries = HungerEntry.query.filter_by(user_id=user.id).order_by(HungerEntry.timestamp).all()
    chart_path = None
    if entries:
        chart_path = create_hunger_chart(user.username, entries)
    
    return render_template('index.html', user=user, entries=entries, chart_path=chart_path)


# User Authentication

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            return "Username already exists"
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))


# Hunger Tracking

@app.route('/add', methods=['POST'])
def add_hunger():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    level = int(request.form['level'])
    entry = HungerEntry(level=level, user_id=session['user_id'])
    db.session.add(entry)
    db.session.commit()
    return redirect(url_for('index'))


# Helper Function: Create Chart

def create_hunger_chart(username, entries):
    levels = [e.level for e in entries]
    timestamps = [e.timestamp for e in entries]
    plt.figure(figsize=(6,3))
    plt.plot(timestamps, levels, marker='o')
    plt.title(f'Hunger Over Time for {username}')
    plt.xlabel('Time')
    plt.ylabel('Hunger Level')
    plt.tight_layout()

    chart_dir = 'static/charts'
    os.makedirs(chart_dir, exist_ok=True)
    chart_path = os.path.join(chart_dir, f'{username}_hunger.png')
    plt.savefig(chart_path)
    plt.close()
    return chart_path

# Initialize Database (Run Once)

@app.before_request
def create_tables():
    db.create_all()


# Test DB connection on startup

try:
    with app.app_context():
        result = db.session.execute(text('SELECT 1'))
        print("DB connection OK:", result.scalar())
except Exception as e:
    print("DB connection failed:", e)

# Run App

if __name__ == '__main__':
    app.run(debug=True)