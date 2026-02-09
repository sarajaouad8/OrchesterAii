from flask import Blueprint, request, render_template, redirect, url_for, flash, session
from models import db
from models.user import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')  # 'manager' or 'employee'

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if user.role != role:
                flash('Incorrect role selected for this account.', 'error')
            else:
                # Store user info in session
                session['user_id'] = user.id
                session['username'] = user.username
                session['role'] = user.role

                flash(f'Welcome back, {user.username}!', 'success')

                # Redirect based on role
                if user.role == 'manager':
                    return redirect(url_for('main.home'))  # TODO: manager dashboard
                else:
                    return redirect(url_for('main.home'))  # TODO: employee dashboard
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('main.home'))
