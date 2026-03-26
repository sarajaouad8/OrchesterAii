import os
from datetime import datetime

from flask import Blueprint, render_template, session, redirect, url_for, request, flash, current_app, send_from_directory
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from models import db
from models.project import Project, Task, TaskCollaborator
from models.user import User
from utils.decorators import employee_required

employee_bp = Blueprint('employee', __name__, url_prefix='/employee')


@employee_bp.app_context_processor
def inject_current_employee():
    """Inject the current employee's User object into all templates."""
    user_id = session.get('user_id')
    if user_id:
        emp = User.query.get(user_id)
        return dict(current_employee=emp)
    return dict(current_employee=None)


@employee_bp.route('/dashboard')
@employee_required
def dashboard():
    # Backward-compatible entrypoint
    return redirect(url_for('employee.overview'))


def _employee_accessible_project_ids(user_id: int):
    primary_ids = (
        db.session.query(Task.project_id)
        .filter(Task.assigned_employee_id == user_id)
        .distinct()
        .all()
    )
    collab_ids = (
        db.session.query(Task.project_id)
        .join(TaskCollaborator, TaskCollaborator.task_id == Task.id)
        .filter(TaskCollaborator.employee_id == user_id)
        .distinct()
        .all()
    )
    ids = {pid for (pid,) in primary_ids} | {pid for (pid,) in collab_ids}
    return list(ids)


def _employee_overview_data(user_id: int):
    if not user_id:
        return [], {}, []

    # Primary tasks
    primary_tasks = (
        Task.query
        .filter_by(assigned_employee_id=user_id)
        .join(Project, Task.project_id == Project.id)
        .all()
    )

    # Collaborator tasks
    collab_links = (
        TaskCollaborator.query
        .filter_by(employee_id=user_id)
        .join(Task, TaskCollaborator.task_id == Task.id)
        .join(Project, Task.project_id == Project.id)
        .all()
    )

    # Group tasks by project
    projects_map = {}

    def add_task(p, t, role_label):
        if p.id not in projects_map:
            projects_map[p.id] = {
                'project': p,
                'tasks': [],
            }
        projects_map[p.id]['tasks'].append((t, role_label))

    for t in primary_tasks:
        add_task(t.project, t, 'Primary')

    for collab in collab_links:
        t = collab.task
        # Avoid duplicate if already primary
        if any(existing_task.id == t.id for existing_task, _ in projects_map.get(t.project_id, {}).get('tasks', [])):
            continue
        add_task(t.project, t, 'Helper')

    projects_with_tasks = list(projects_map.values())

    # Global stats across all projects for this employee
    all_tasks = [t for p in projects_with_tasks for (t, _) in p['tasks']]
    total_tasks = len(all_tasks)
    completed = sum(1 for t in all_tasks if t.status == 'completed')
    in_progress = sum(1 for t in all_tasks if t.status == 'in_progress')
    not_started = total_tasks - completed - in_progress

    stats = {
        'total_projects': len(projects_with_tasks),
        'total_tasks': total_tasks,
        'completed': completed,
        'in_progress': in_progress,
        'not_started': not_started,
    }

    # Sort projects by created_at desc
    projects_with_tasks.sort(key=lambda p: p['project'].created_at or 0, reverse=True)

    # Recent tasks (most recently updated)
    recent_tasks = (
        Task.query
        .filter(or_(
            Task.assigned_employee_id == user_id,
            Task.id.in_(
                db.session.query(TaskCollaborator.task_id).filter(TaskCollaborator.employee_id == user_id)
            )
        ))
        .order_by(Task.updated_at.desc())
        .limit(8)
        .all()
    )

    return projects_with_tasks, stats, recent_tasks


def _project_status_counts(projects_with_tasks):
    counts = {'pending': 0, 'in_progress': 0, 'completed': 0}
    for item in projects_with_tasks:
        st = item['project'].status
        if st in counts:
            counts[st] += 1
    return counts


@employee_bp.route('/overview')
@employee_required
def overview():
    user_id = session.get('user_id')
    projects, stats, recent_tasks = _employee_overview_data(user_id)
    project_status_counts = _project_status_counts(projects)
    now = datetime.now()
    hour = now.hour
    greeting = 'morning' if hour < 12 else ('afternoon' if hour < 18 else 'evening')
    return render_template(
        'employee/overview.html',
        stats=stats,
        recent_tasks=recent_tasks,
        projects=projects,
        project_status_counts=project_status_counts,
        now=now,
        greeting=greeting,
        active_nav='overview',
    )


@employee_bp.route('/projects')
@employee_required
def projects():
    user_id = session.get('user_id')
    accessible_ids = _employee_accessible_project_ids(user_id)
    all_projects = (
        Project.query
        .filter(Project.id.in_(accessible_ids))
        .order_by(Project.created_at.desc())
        .all()
    ) if accessible_ids else []

    stats = {
        'total_projects': len(all_projects),
        'pending': len([p for p in all_projects if p.status == 'pending']),
        'in_progress': len([p for p in all_projects if p.status == 'in_progress']),
        'completed': len([p for p in all_projects if p.status == 'completed']),
    }

    return render_template(
        'employee/projects.html',
        projects=all_projects,
        stats=stats,
        active_nav='projects',
    )


@employee_bp.route('/project/<int:project_id>')
@employee_required
def project_detail(project_id):
    user_id = session.get('user_id')
    accessible_ids = _employee_accessible_project_ids(user_id)
    if project_id not in accessible_ids:
        flash('Access denied for this project.', 'error')
        return redirect(url_for('employee.projects'))

    project = Project.query.get_or_404(project_id)

    # Show full project task table (employee sees whole project), with a "mine" marker
    tasks = Task.query.filter_by(project_id=project.id).all()
    tasks.sort(key=lambda t: (int(''.join(filter(str.isdigit, t.task_id)) or 0), t.task_id))

    mine_task_ids = set(
        [t.id for t in Task.query.filter_by(project_id=project.id, assigned_employee_id=user_id).all()]
    )
    mine_task_ids |= set(
        [tid for (tid,) in db.session.query(TaskCollaborator.task_id).join(Task).filter(
            Task.project_id == project.id,
            TaskCollaborator.employee_id == user_id
        ).all()]
    )

    total_tasks = len(tasks)
    completed = sum(1 for t in tasks if t.status == 'completed')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    assigned_to_me = sum(1 for t in tasks if t.id in mine_task_ids)
    total_days = sum(t.duree_estimee_jours or 0 for t in tasks)

    stats = {
        'total_tasks': total_tasks,
        'completed': completed,
        'in_progress': in_progress,
        'not_started': total_tasks - completed - in_progress,
        'assigned_to_me': assigned_to_me,
        'total_days': total_days,
    }

    return render_template(
        'employee/project_detail.html',
        project=project,
        tasks=tasks,
        stats=stats,
        mine_task_ids=mine_task_ids,
        active_nav='projects',
    )


# ─────────────────────────────────────────────
# Task Status Update (employee can change status of their own tasks)
# ─────────────────────────────────────────────
@employee_bp.route('/task/<int:task_id>/status', methods=['POST'])
@employee_required
def update_task_status(task_id):
    user_id = session.get('user_id')
    task = Task.query.get_or_404(task_id)

    # Verify employee is assigned to this task (primary or collaborator)
    is_primary = task.assigned_employee_id == user_id
    is_collaborator = TaskCollaborator.query.filter_by(
        task_id=task_id, employee_id=user_id
    ).first() is not None

    if not is_primary and not is_collaborator:
        flash('You can only update status for your own tasks.', 'error')
        return redirect(url_for('employee.project_detail', project_id=task.project_id))

    new_status = request.form.get('status', '').strip()
    allowed = {'not_started', 'in_progress', 'completed'}
    if new_status not in allowed:
        flash('Invalid status.', 'error')
        return redirect(url_for('employee.project_detail', project_id=task.project_id))

    task.status = new_status
    task.updated_at = datetime.utcnow()
    db.session.commit()

    status_labels = {'not_started': 'Not Started', 'in_progress': 'In Progress', 'completed': 'Done'}
    flash(f'Task "{task.nom}" marked as {status_labels.get(new_status, new_status)}.', 'success')
    return redirect(url_for('employee.project_detail', project_id=task.project_id))


# ─────────────────────────────────────────────
# Profile
# ─────────────────────────────────────────────
@employee_bp.route('/profile', methods=['GET', 'POST'])
@employee_required
def profile():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip() or None
        email = request.form.get('email', '').strip() or None
        phone = request.form.get('phone', '').strip() or None
        location = request.form.get('location', '').strip() or None
        professional_headline = request.form.get('professional_headline', '').strip() or None

        # Update password if provided
        password = request.form.get('password', '').strip()
        if password:
            user.set_password(password)

        if email and email != user.email:
            if User.query.filter(User.email == email, User.id != user.id).first():
                flash('Email already in use.', 'error')
                return redirect(url_for('employee.profile'))

        user.name = name
        user.email = email
        user.phone = phone
        user.location = location
        user.professional_headline = professional_headline

        # Handle profile picture upload
        if 'profile_pic' in request.files:
            pic_file = request.files['profile_pic']
            if pic_file and pic_file.filename != '':
                allowed_pic_ext = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                ext = pic_file.filename.rsplit('.', 1)[1].lower() if '.' in pic_file.filename else ''
                if ext in allowed_pic_ext:
                    pic_folder = os.path.join(current_app.root_path, 'uploads', 'profile_pics')
                    os.makedirs(pic_folder, exist_ok=True)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    pic_filename = secure_filename(f"{user.id}_{timestamp}.{ext}")
                    pic_file.save(os.path.join(pic_folder, pic_filename))
                    user.profile_pic = pic_filename
                else:
                    flash('Invalid image format. Use PNG, JPG, GIF, or WebP.', 'error')

        db.session.commit()
        session['username'] = user.name or user.username
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('employee.profile'))

    return render_template('employee/profile.html', user=user, active_nav='profile')


@employee_bp.route('/profile/delete-pic', methods=['POST'])
@employee_required
def delete_own_pic():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)
    if user.profile_pic:
        pic_path = os.path.join(current_app.root_path, 'uploads', 'profile_pics', user.profile_pic)
        if os.path.exists(pic_path):
            os.remove(pic_path)
        user.profile_pic = None
        db.session.commit()
        flash('Profile picture removed.', 'success')
    return redirect(url_for('employee.profile'))


@employee_bp.route('/profile-pic/<filename>')
@employee_required
def profile_pic(filename):
    pic_folder = os.path.join(current_app.root_path, 'uploads', 'profile_pics')
    return send_from_directory(pic_folder, filename)
