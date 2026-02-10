import os
import json
from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db
from models.user import User
from models.project import Project
from utils.decorators import manager_required

manager_bp = Blueprint('manager', __name__, url_prefix='/manager')

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ─────────────────────────────────────────────
# Dashboard / Overview
# ─────────────────────────────────────────────
@manager_bp.route('/dashboard')
@manager_required
def dashboard():
    # Get users
    employees = User.query.filter_by(role='employee').order_by(User.created_at.desc()).all()
    managers = User.query.filter_by(role='manager').all()
    
    # Get projects
    all_projects = Project.query.order_by(Project.created_at.desc()).all()
    pending_projects = Project.query.filter_by(status='pending').count()
    in_progress_projects = Project.query.filter_by(status='in_progress').count()
    completed_projects = Project.query.filter_by(status='completed').count()
    
    # Recent items
    recent_projects = all_projects[:5]
    recent_employees = employees[:5]

    stats = {
        'total_employees': len(employees),
        'total_managers': len(managers),
        'total_projects': len(all_projects),
        'pending_projects': pending_projects,
        'in_progress_projects': in_progress_projects,
        'completed_projects': completed_projects,
    }
    
    return render_template('manager/dashboard.html', 
                           stats=stats, 
                           recent_projects=recent_projects,
                           recent_employees=recent_employees,
                           now=datetime.now())


# ─────────────────────────────────────────────
# Employee Management — Add
# ─────────────────────────────────────────────
@manager_bp.route('/employees/add', methods=['POST'])
@manager_required
def add_employee():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip() or None
    password = request.form.get('password', '').strip()

    if not username or not password:
        flash('Username and password are required.', 'error')
        return redirect(url_for('manager.employees'))

    if User.query.filter_by(username=username).first():
        flash(f'Username "{username}" already exists.', 'error')
        return redirect(url_for('manager.employees'))

    if email and User.query.filter_by(email=email).first():
        flash(f'Email "{email}" already in use.', 'error')
        return redirect(url_for('manager.employees'))

    employee = User(username=username, email=email, role='employee')
    employee.set_password(password)
    db.session.add(employee)
    db.session.commit()

    flash(f'Employee "{username}" added successfully!', 'success')
    return redirect(url_for('manager.employees'))


# ─────────────────────────────────────────────
# Employee Management — Edit
# ─────────────────────────────────────────────
@manager_bp.route('/employees/edit/<int:employee_id>', methods=['POST'])
@manager_required
def edit_employee(employee_id):
    employee = User.query.get_or_404(employee_id)

    if employee.role != 'employee':
        flash('You can only edit employees.', 'error')
        return redirect(url_for('manager.employees'))

    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip() or None
    password = request.form.get('password', '').strip()

    if username and username != employee.username:
        if User.query.filter_by(username=username).first():
            flash(f'Username "{username}" already exists.', 'error')
            return redirect(url_for('manager.employees'))
        employee.username = username

    if email != employee.email:
        if email and User.query.filter_by(email=email).first():
            flash(f'Email "{email}" already in use.', 'error')
            return redirect(url_for('manager.employees'))
        employee.email = email

    if password:
        employee.set_password(password)

    db.session.commit()
    flash(f'Employee "{employee.username}" updated successfully!', 'success')
    return redirect(url_for('manager.employees'))


# ─────────────────────────────────────────────
# Employee Management — Delete
# ─────────────────────────────────────────────
@manager_bp.route('/employees/delete/<int:employee_id>', methods=['POST'])
@manager_required
def delete_employee(employee_id):
    employee = User.query.get_or_404(employee_id)

    if employee.role != 'employee':
        flash('You can only delete employees.', 'error')
        return redirect(url_for('manager.employees'))

    if employee.id == session.get('user_id'):
        flash('You cannot delete yourself.', 'error')
        return redirect(url_for('manager.employees'))

    db.session.delete(employee)
    db.session.commit()
    flash(f'Employee "{employee.username}" deleted.', 'success')
    return redirect(url_for('manager.employees'))


# ─────────────────────────────────────────────
# Document Upload
# ─────────────────────────────────────────────
@manager_bp.route('/upload', methods=['POST'])
@manager_required
def upload_document():
    if 'document' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('manager.dashboard'))

    file = request.files['document']
    doc_type = request.form.get('doc_type', 'cv')  # 'cv' or 'cdc'

    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('manager.dashboard'))

    if not allowed_file(file.filename):
        flash('Invalid file type. Only PDF and DOCX files are allowed.', 'error')
        return redirect(url_for('manager.dashboard'))

    # Create uploads directory if needed
    upload_folder = os.path.join(current_app.root_path, 'uploads', doc_type)
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    flash(f'Document "{filename}" uploaded successfully as {doc_type.upper()}!', 'success')
    return redirect(url_for('manager.dashboard'))


# ─────────────────────────────────────────────
# Projects Page
# ─────────────────────────────────────────────
@manager_bp.route('/projects')
@manager_required
def projects():
    manager_id = session.get('user_id')
    all_projects = Project.query.filter_by(manager_id=manager_id).order_by(Project.created_at.desc()).all()
    
    stats = {
        'total_projects': len(all_projects),
        'pending': len([p for p in all_projects if p.status == 'pending']),
        'in_progress': len([p for p in all_projects if p.status == 'in_progress']),
        'completed': len([p for p in all_projects if p.status == 'completed']),
    }
    return render_template('manager/projects.html', projects=all_projects, stats=stats)


# ─────────────────────────────────────────────
# Projects — Create New
# ─────────────────────────────────────────────
@manager_bp.route('/projects/add', methods=['POST'])
@manager_required
def add_project():
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip() or None
    
    if not name:
        flash('Project name is required.', 'error')
        return redirect(url_for('manager.projects'))
    
    manager_id = session.get('user_id')
    
    # Create the project
    project = Project(name=name, description=description, manager_id=manager_id, status='pending')
    
    # Handle CV upload
    if 'cv_file' in request.files:
        cv_file = request.files['cv_file']
        if cv_file.filename and allowed_file(cv_file.filename):
            upload_folder = os.path.join(current_app.root_path, 'uploads', 'projects', 'cv')
            os.makedirs(upload_folder, exist_ok=True)
            cv_filename = secure_filename(f"{name}_{cv_file.filename}")
            cv_path = os.path.join(upload_folder, cv_filename)
            cv_file.save(cv_path)
            project.cv_path = cv_path
    
    # Handle Specs upload
    if 'specs_file' in request.files:
        specs_file = request.files['specs_file']
        if specs_file.filename and allowed_file(specs_file.filename):
            upload_folder = os.path.join(current_app.root_path, 'uploads', 'projects', 'specs')
            os.makedirs(upload_folder, exist_ok=True)
            specs_filename = secure_filename(f"{name}_{specs_file.filename}")
            specs_path = os.path.join(upload_folder, specs_filename)
            specs_file.save(specs_path)
            project.specs_path = specs_path
    
    db.session.add(project)
    db.session.commit()
    
    flash(f'Project "{name}" created successfully!', 'success')
    return redirect(url_for('manager.projects'))


# ─────────────────────────────────────────────
# Projects — Delete
# ─────────────────────────────────────────────
@manager_bp.route('/projects/delete/<int:project_id>', methods=['POST'])
@manager_required
def delete_project(project_id):
    manager_id = session.get('user_id')
    project = Project.query.filter_by(id=project_id, manager_id=manager_id).first_or_404()
    
    project_name = project.name
    db.session.delete(project)
    db.session.commit()
    
    flash(f'Project "{project_name}" deleted.', 'success')
    return redirect(url_for('manager.projects'))


# ─────────────────────────────────────────────
# Projects — Update Status
# ─────────────────────────────────────────────
@manager_bp.route('/projects/<int:project_id>/status', methods=['POST'])
@manager_required
def update_project_status(project_id):
    manager_id = session.get('user_id')
    project = Project.query.filter_by(id=project_id, manager_id=manager_id).first_or_404()
    
    new_status = request.form.get('status', 'pending')
    if new_status in ['pending', 'in_progress', 'completed']:
        project.status = new_status
        db.session.commit()
        flash(f'Project "{project.name}" status updated to {new_status.replace("_", " ").title()}.', 'success')
    
    return redirect(url_for('manager.projects'))


# ─────────────────────────────────────────────
# Employees Page (separate from dashboard)
# ─────────────────────────────────────────────
@manager_bp.route('/employees')
@manager_required
def employees():
    all_employees = User.query.filter_by(role='employee').order_by(User.created_at.desc()).all()
    
    stats = {
        'total': len(all_employees),
        'active': len(all_employees),  # For now, all are active
        'inactive': 0,
    }
    return render_template('manager/employees.html', employees=all_employees, stats=stats)

