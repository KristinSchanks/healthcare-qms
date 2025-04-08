
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import os
import datetime

app = Flask(__name__)
app.secret_key = 'secure-qms-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///qms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, role='admin'):
        self.id = id
        self.role = role

users = {
    'admin': {'password': generate_password_hash('admin123'), 'role': 'admin'},
    'jane': {'password': generate_password_hash('viewer123'), 'role': 'viewer'}
}

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    submitted_by = db.Column(db.String(100))
    submitted_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(100))
    name = db.Column(db.String(200))
    detail = db.Column(db.Text)
    user = db.Column(db.String(100))
    submitted_on = db.Column(db.DateTime, default=datetime.datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id, users[user_id]['role'])
    return None

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and check_password_hash(users[username]['password'], password):
            user = User(username, users[username]['role'])
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@app.route('/feedback', methods=['GET', 'POST'])
@login_required
def feedback():
    if request.method == 'POST':
        entry = Feedback(content=request.form['feedback'], submitted_by=current_user.id)
        db.session.add(entry)
        db.session.commit()
        flash("Thank you for your feedback!", "success")
    entries = Feedback.query.order_by(Feedback.submitted_on.desc()).all()
    return render_template('feedback.html', feedback_entries=entries)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_record():
    if request.method == 'POST':
        new_record = Record(
            type=request.form['type'],
            name=request.form['name'],
            detail=request.form['detail'],
            user=current_user.id
        )
        db.session.add(new_record)
        db.session.commit()
        flash("Record added successfully.", "info")
        return redirect(url_for('dashboard'))
    return render_template('add_record.html')

@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '').lower()
    results = Record.query.filter(
        db.or_(
            Record.name.ilike(f'%{query}%'),
            Record.detail.ilike(f'%{query}%')
        )
    ).all()
    return render_template('search_results.html', query=query, results=results)

if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
