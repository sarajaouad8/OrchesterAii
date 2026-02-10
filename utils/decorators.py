from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    """Decorator: user must be logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def manager_required(f):
    """Decorator: user must be a logged-in manager."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'manager':
            flash('Access denied. Manager privileges required.', 'error')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function


def employee_required(f):
    """Decorator: user must be a logged-in employee."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if session.get('role') != 'employee':
            flash('Access denied. Employee access only.', 'error')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function
