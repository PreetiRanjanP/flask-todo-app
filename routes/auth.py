# routes/auth.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import db, User

auth = Blueprint('auth', __name__)

# ── Register ─────────────────────────────────────────────
@auth.route('/register', methods=['GET', 'POST'])
def register():
    # If already logged in, go to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('tasks.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        # ── Validation ──────────────────────────────────
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('register.html')

        if len(username) < 3:
            flash('Username must be at least 3 characters.', 'danger')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'warning')
            return redirect(url_for('auth.login'))

        if User.query.filter_by(username=username).first():
            flash('Username already taken. Choose another.', 'warning')
            return render_template('register.html')

        # ── Create user ─────────────────────────────────
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
        new_user  = User(username=username, email=email, password=hashed_pw)

        db.session.add(new_user)
        db.session.commit()

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


# ── Login ────────────────────────────────────────────────
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('tasks.dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        # Check user exists and password is correct
        if not user or not check_password_hash(user.password, password):
            flash('Invalid email or password. Try again.', 'danger')
            return render_template('login.html')

        login_user(user, remember=remember)
        flash(f'Welcome back, {user.username}!', 'success')

        # Redirect to page they were trying to visit, or dashboard
        next_page = request.args.get('next')
        return redirect(next_page or url_for('tasks.dashboard'))

    return render_template('login.html')


# ── Logout ───────────────────────────────────────────────
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


# ── Profile ──────────────────────────────────────────────
@auth.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)