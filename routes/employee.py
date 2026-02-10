from flask import Blueprint, render_template, session
from utils.decorators import employee_required

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


@employee_bp.route('/dashboard')
@employee_required
def dashboard():
    return render_template('employee/dashboard.html')
