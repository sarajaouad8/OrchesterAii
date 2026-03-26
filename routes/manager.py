import os
import json
import re
import requests
from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, flash, session, jsonify, current_app
from werkzeug.utils import secure_filename
from models import db
from models.user import User
from models.project import Project, Task, TaskCollaborator
from utils.decorators import manager_required
from utils.matching import auto_match_tasks, auto_reassign_employee

manager_bp = Blueprint('manager', __name__, url_prefix='/manager')


@manager_bp.app_context_processor
def inject_current_manager():
    """Inject the current manager's User object into all templates."""
    user_id = session.get('user_id')
    if user_id:
        mgr = User.query.get(user_id)
        return dict(current_manager=mgr)
    return dict(current_manager=None)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
ALLOWED_CV_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_cv_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_CV_EXTENSIONS


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file using pdfplumber (better extraction quality)."""
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        current_app.logger.error(f"Error extracting PDF text with pdfplumber: {e}")
        # Fallback to PyPDF2 if pdfplumber fails
        try:
            import PyPDF2
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
            return text.strip()
        except Exception as e2:
            current_app.logger.error(f"Error extracting PDF text with PyPDF2: {e2}")
            return None


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
# Employee Management — Add (CV Upload)
# ─────────────────────────────────────────────
@manager_bp.route('/employees/add', methods=['POST'])
@manager_required
def add_employee():
    """
    New workflow: Manager uploads one or multiple CVs.
    For each CV:
    1. Save CV file
    2. Extract text from PDF
    3. Send to n8n for AI analysis
    4. n8n will call back /api/employee/create with the analyzed data
    """
    cv_files = request.files.getlist('cv_files')
    
    if not cv_files or all(f.filename == '' for f in cv_files):
        flash('Please upload at least one CV file.', 'error')
        return redirect(url_for('manager.employees'))
    
    # Filter valid files
    valid_files = [f for f in cv_files if f and f.filename != '' and allowed_cv_file(f.filename)]
    skipped = len(cv_files) - len(valid_files)
    
    if not valid_files:
        flash('No valid PDF files found. Only PDF files are allowed.', 'error')
        return redirect(url_for('manager.employees'))
    
    if skipped > 0:
        flash(f'⚠️ {skipped} non-PDF file(s) were skipped.', 'warning')
    
    # Create CV upload directory if it doesn't exist
    cv_folder = current_app.config.get('CV_UPLOAD_FOLDER', os.path.join(current_app.root_path, 'uploads', 'cvs'))
    os.makedirs(cv_folder, exist_ok=True)
    
    # n8n URLs
    n8n_url = current_app.config.get('N8N_WEBHOOK_URL')
    backup_urls = current_app.config.get('N8N_BACKUP_URLS', [])
    urls_to_try = [n8n_url] + backup_urls if backup_urls else [n8n_url]
    
    success_count = 0
    fail_count = 0
    
    for cv_file in valid_files:
        # Save CV file with unique name
        filename = secure_filename(cv_file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        unique_filename = f"{timestamp}_{filename}"
        cv_path = os.path.join(cv_folder, unique_filename)
        cv_file.save(cv_path)
        
        # Extract text from PDF
        cv_text = extract_text_from_pdf(cv_path)
        
        if not cv_text:
            current_app.logger.warning(f"❌ Could not extract text from {filename}")
            flash(f'⚠️ Could not extract text from {filename}. Skipping.', 'warning')
            os.remove(cv_path)
            fail_count += 1
            continue
        
        # Send to n8n for analysis with retry logic
        sent = False
        for attempt, url in enumerate(urls_to_try, 1):
            if not url:
                continue
            try:
                current_app.logger.info(f"🔄 [{filename}] Attempt {attempt}: Trying {url}")
                
                public_url = current_app.config.get('PUBLIC_URL', 'http://localhost:5000')
                callback_url = f"{public_url}/manager/api/employee/create"
                
                response = requests.post(
                    url,
                    json={
                        'cv_text': cv_text,
                        'cv_filename': unique_filename,
                        'callback_url': callback_url,
                        'retry_count': attempt
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    success_count += 1
                    sent = True
                    break
                else:
                    current_app.logger.warning(f"❌ [{filename}] Attempt {attempt} failed: {response.status_code}")
            except requests.exceptions.RequestException as e:
                current_app.logger.error(f"❌ [{filename}] Attempt {attempt} connection error: {e}")
                continue
        
        if not sent:
            fail_count += 1
            current_app.logger.error(f"❌ All n8n attempts failed for {filename}")
    
    # Summary flash messages
    total = len(valid_files)
    if success_count == total:
        if total == 1:
            flash('✅ CV uploaded successfully! The AI is analyzing it. The employee will be added shortly.', 'success')
        else:
            flash(f'✅ All {success_count} CVs uploaded successfully! The AI is analyzing them. Employees will be added shortly.', 'success')
    elif success_count > 0:
        flash(f'⚠️ {success_count}/{total} CVs sent to AI successfully. {fail_count} failed.', 'warning')
    else:
        flash(f'❌ All {total} CV uploads failed to reach n8n.', 'error')
        flash('💡 Solutions: 1) Ask friend to restart ngrok, 2) Get new URL, 3) Use test endpoint', 'warning')
    
    return redirect(url_for('manager.employees'))

# ─────────────────────────────────────────────
# TEMPORARY: Test Employee Creation Without n8n
# ─────────────────────────────────────────────
@manager_bp.route('/test/create-employee', methods=['POST', 'GET'])
@manager_required  
def test_create_employee():
    """
    Test endpoint to create employee without n8n (for testing only)
    """
    if request.method == 'GET':
        # Show test form
        return '''
        <h2>Test Employee Creation (No n8n needed)</h2>
        <form method="POST">
            <p><input name="name" placeholder="Full Name" required></p>
            <p><input name="email" placeholder="Email" required></p>
            <p><input name="phone" placeholder="+212..." ></p>
            <p><textarea name="skills" placeholder="Python, React, SQL..."></textarea></p>
            <button type="submit">Create Test Employee</button>
        </form>
        <p><a href="/manager/employees">← Back to Employees</a></p>
        '''
    
    # Create employee manually
    name = request.form.get('name')
    email = request.form.get('email') 
    phone = request.form.get('phone')
    skills_text = request.form.get('skills', '')
    
    if not name or not email:
        flash('Name and email required', 'error')
        return redirect(request.url)
    
    # Check if email exists
    if User.query.filter_by(email=email).first():
        flash(f'Email {email} already exists!', 'error')
        return redirect(request.url)
    
    # Create employee with manual data
    username = User.generate_username(name)
    password = User.generate_password()
    
    # Parse skills
    skills_list = [s.strip() for s in skills_text.split(',') if s.strip()]
    technical_skills = {"manual_entry": skills_list} if skills_list else {}
    
    employee = User(
        username=username,
        name=name,
        email=email,
        phone=phone,
        role='employee',
        status='active',
        technical_skills=technical_skills,
        cv_file='test_manual_entry.pdf'
    )
    employee.set_password(password)
    
    db.session.add(employee)
    db.session.commit()
    
    flash(f'✅ Test employee created! Username: {username}, Password: {password}', 'success')
    return redirect(url_for('manager.employees'))


@manager_bp.route('/test/create-hind')
@manager_required
def create_hind_employee():
    """
    Convenience route to create a demo employee named 'hind'
    so you can quickly log in and test the employee dashboard.
    """
    name = 'hind'
    email = 'hind@example.com'
    username = 'hind'
    fixed_password = 'hind1234'  # demo password so you can log in

    # Try to find any existing "hind" user (by username, email or name)
    existing = User.query.filter(
        (User.username == username) |
        (User.email == email) |
        (User.name.ilike('hind%'))
    ).first()

    if existing:
        # Ensure role + password are as expected
        existing.role = 'employee'
        existing.status = 'active'
        existing.set_password(fixed_password)
        db.session.commit()
        flash(
            f'Employee "hind" already existed. Username: {existing.username}, Password reset to: {fixed_password}',
            'info'
        )
        return redirect(url_for('manager.employees'))

    employee = User(
        username=username,
        name=name,
        email=email,
        role='employee',
        status='active',
        technical_skills={"manual_entry": ["Python", "Flask", "SQL"]},
        cv_file='hind_demo.pdf'
    )
    employee.set_password(fixed_password)

    db.session.add(employee)
    db.session.commit()

    flash(f'✅ Employee "hind" created! Username: {username}, Password: {fixed_password}', 'success')
    return redirect(url_for('manager.employees'))


@manager_bp.route('/debug/webhook')
def debug_webhook():
    """Debug endpoint to test n8n webhook connection"""
    n8n_url = current_app.config['N8N_WEBHOOK_URL']
    
    try:
        # Test connection to n8n
        response = requests.post(
            n8n_url,
            json={'test': 'connection', 'timestamp': str(datetime.now())},
            timeout=10
        )
        
        return jsonify({
            'success': True,
            'webhook_url': n8n_url,
            'status_code': response.status_code,
            'response': response.text[:500]
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'webhook_url': n8n_url,
            'error': str(e)
        })


@manager_bp.route('/debug/analyze', methods=['POST'])
def debug_analyze():
    """
    Debug endpoint for your friend to test what JSON structure 
    her AI analysis is actually producing.
    She can send her AI output here to see what fields exist.
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False, 
                'error': 'No JSON data received',
                'tip': 'Make sure to send JSON in the request body'
            }), 400
        
        # Analyze the structure
        analysis = {
            'received_keys': list(data.keys()),
            'personal_info_exists': 'personal_info' in data,
            'technical_skills_exists': 'technical_skills' in data,
            'certifications_exists': 'certifications' in data,
            'languages_exists': 'languages' in data,
            'work_experience_exists': 'work_experience' in data,
        }
        
        # Check nested personal_info structure
        if 'personal_info' in data:
            analysis['personal_info_keys'] = list(data['personal_info'].keys()) if isinstance(data['personal_info'], dict) else 'not_a_dict'
        
        # Check technical_skills structure  
        if 'technical_skills' in data:
            analysis['technical_skills_type'] = str(type(data['technical_skills']))
            if isinstance(data['technical_skills'], dict):
                analysis['technical_skills_keys'] = list(data['technical_skills'].keys())
            elif isinstance(data['technical_skills'], list):
                analysis['technical_skills_length'] = len(data['technical_skills'])
        
        return jsonify({
            'success': True,
            'message': 'JSON structure analyzed successfully!',
            'analysis': analysis,
            'full_data_received': data,
            'recommendations': {
                'missing_fields': [field for field in ['personal_info', 'technical_skills', 'certifications', 'languages', 'work_experience'] 
                                 if field not in data],
                'suggested_minimal_format': {
                    'personal_info': {
                        'full_name': 'Required field',
                        'email': 'Required field'
                    },
                    'technical_skills': 'This field was missing from your JSON!'
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Debug analysis failed: {str(e)}'
        }), 500


# ─────────────────────────────────────────────
# API Endpoint for n8n to create employee
# ─────────────────────────────────────────────
@manager_bp.route('/api/employee/create', methods=['POST'])
def api_create_employee():
    """
    API endpoint for n8n to send analyzed CV data.
    Receives the complete CV analysis JSON and creates employee.
    Auto-generates: username, password
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # ─── Extract from metadata ───
        metadata = data.get('metadata', {})
        cv_filename = metadata.get('cv_filename', '')
        
        # ─── Extract from personal_info ───
        personal_info = data.get('personal_info', {})
        name = personal_info.get('full_name', '').strip()
        email = personal_info.get('email', '').strip() or None
        phone = personal_info.get('phone', '').strip() or None
        professional_headline = personal_info.get('professional_headline', '').strip() or None
        
        # Location: combine city + country
        location_data = personal_info.get('location', {})
        city = location_data.get('city', '')
        country = location_data.get('country', '')
        location = f"{city}, {country}".strip(', ') or None
        
        # ─── Validate required fields ───
        if not name:
            return jsonify({'success': False, 'error': 'Name (full_name) is required'}), 400
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': f'Email "{email}" already exists'}), 400
        
        # ─── Generate username and password automatically ───
        username = User.generate_username(name)
        password = User.generate_password()
        
        # ─── Extract technical_skills (keep as JSON object) ───
        technical_skills = data.get('technical_skills', {})
        
        # Log what we're receiving from n8n for debugging
        current_app.logger.info(f"📊 Received from n8n - technical_skills: {technical_skills}")
        current_app.logger.info(f"📊 Full received data keys: {list(data.keys())}")
        
        # If skills is empty, try alternative keys that n8n might send
        if not technical_skills or technical_skills == {}:
            # Try common alternative key names
            alternative_keys = ['skills', 'competences', 'competencies', 'abilities']
            for key in alternative_keys:
                if key in data and data[key]:
                    technical_skills = data[key]
                    current_app.logger.info(f"✅ Found skills under key '{key}': {technical_skills}")
                    break
        
        # ─── Extract certifications ───
        certifications = data.get('certifications', [])
        
        # ─── Extract languages ───
        languages = data.get('languages', [])
        
        # ─── Calculate years of experience from work_experience ───
        work_experience = data.get('work_experience', [])
        years_of_experience = 0
        
        for exp in work_experience:
            start_date = exp.get('start_date', '')
            end_date = exp.get('end_date', '')
            is_current = exp.get('is_current', False)
            
            # Parse start year
            start_year = None
            if start_date:
                # Handle formats like "Mars 2022" or "2022-03"
                import re
                year_match = re.search(r'(\d{4})', start_date)
                if year_match:
                    start_year = int(year_match.group(1))
            
            # Parse end year
            end_year = datetime.now().year  # Default to current year
            if not is_current and end_date and end_date.lower() not in ['présent', 'present', '']:
                year_match = re.search(r'(\d{4})', end_date)
                if year_match:
                    end_year = int(year_match.group(1))
            
            # Calculate duration
            if start_year:
                years_of_experience += (end_year - start_year)
        
        # ─── Create the employee ───
        employee = User(
            username=username,
            name=name,
            email=email,
            phone=phone,
            location=location,
            professional_headline=professional_headline,
            role='employee',
            status='active',
            technical_skills=technical_skills,
            certifications=certifications,
            languages=languages,
            years_of_experience=years_of_experience,
            cv_data=data,  # Store complete CV analysis for reference
            cv_file=cv_filename
        )
        employee.set_password(password)
        
        db.session.add(employee)
        db.session.commit()
        
        # ─── Send Welcome Email ───
        try:
            from email.mime.text import MIMEText
            import smtplib
            import os
            
            smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', 587))
            smtp_user = os.environ.get('SMTP_USER')
            smtp_pass = os.environ.get('SMTP_PASS')
            
            if smtp_user and smtp_pass and email:
                msg = MIMEText(f"Hello {name},\n\nWelcome to OrchestrAi! Your account has been created.\n\nUsername: {username}\nPassword: {password}\n\nPlease log in and change your password.\n\nBest,\nOrchestrAi Team")
                msg['Subject'] = 'Welcome to OrchestrAi'
                msg['From'] = smtp_user
                msg['To'] = email
                
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                current_app.logger.info(f"📧 Welcome email sent to {email}")
            else:
                current_app.logger.info(f"📧 [DEV MODE] Welcome email would be sent to {email}.\nUsername: {username}\nPassword: {password}\n(Configure SMTP_USER and SMTP_PASS env vars to send real emails)")
        except Exception as email_err:
            current_app.logger.error(f"Failed to send welcome email: {email_err}")
        

        # ─── Return success with credentials ───
        return jsonify({
            'success': True,
            'message': f'Employee "{name}" created successfully',
            'debug': {
                'skills_received': technical_skills,
                'skills_stored_in_db': employee.technical_skills,
                'skills_extracted': employee.get_all_skills()
            },
            'employee': {
                'id': employee.id,
                'username': username,
                'password': password,  # ⚠️ Send back so manager can give to employee
                'name': name,
                'email': email,
                'phone': phone,
                'location': location,
                'professional_headline': professional_headline,
                'technical_skills': employee.get_all_skills(),
                'years_of_experience': years_of_experience,
                'status': 'active'
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating employee: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


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

    name = request.form.get('name', '').strip() or None
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip() or None
    status = request.form.get('status', 'active').strip()
    password = request.form.get('password', '').strip()

    # Update name
    if name:
        employee.name = name

    # Update username
    if username and username != employee.username:
        if User.query.filter_by(username=username).first():
            flash(f'Username "{username}" already exists.', 'error')
            return redirect(url_for('manager.employees'))
        employee.username = username

    # Update email
    if email != employee.email:
        if email and User.query.filter_by(email=email).first():
            flash(f'Email "{email}" already in use.', 'error')
            return redirect(url_for('manager.employees'))
        employee.email = email

    # Update status
    if status in ['active', 'inactive']:
        employee.status = status

    # Update password
    if password:
        employee.set_password(password)

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
                pic_filename = secure_filename(f"{employee.id}_{timestamp}.{ext}")
                pic_file.save(os.path.join(pic_folder, pic_filename))
                employee.profile_pic = pic_filename
            else:
                flash('Invalid image format. Use PNG, JPG, GIF, or WebP.', 'error')

    db.session.commit()
    flash(f'Employee "{employee.name or employee.username}" updated successfully!', 'success')
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
# Serve Profile Pictures
# ─────────────────────────────────────────────
@manager_bp.route('/uploads/profile_pics/<filename>')
@manager_required
def profile_pic(filename):
    pic_folder = os.path.join(current_app.root_path, 'uploads', 'profile_pics')
    from flask import send_from_directory
    return send_from_directory(pic_folder, filename)


@manager_bp.route('/employees/<int:employee_id>/delete-pic', methods=['POST'])
@manager_required
def delete_profile_pic(employee_id):
    employee = User.query.get_or_404(employee_id)
    if employee.profile_pic:
        pic_path = os.path.join(current_app.root_path, 'uploads', 'profile_pics', employee.profile_pic)
        if os.path.exists(pic_path):
            os.remove(pic_path)
        employee.profile_pic = None
        db.session.commit()
        flash('Profile picture removed.', 'success')
    return redirect(url_for('manager.employees'))


# ─────────────────────────────────────────────
# Manager Profile
# ─────────────────────────────────────────────
@manager_bp.route('/profile', methods=['GET', 'POST'])
@manager_required
def manager_profile():
    user_id = session.get('user_id')
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip() or None
        email = request.form.get('email', '').strip() or None
        phone = request.form.get('phone', '').strip() or None
        location = request.form.get('location', '').strip() or None
        headline = request.form.get('professional_headline', '').strip() or None

        # Update password if provided
        password = request.form.get('password', '').strip()
        if password:
            user.set_password(password)

        # Update email (check uniqueness)
        if email and email != user.email:
            if User.query.filter(User.email == email, User.id != user.id).first():
                flash('Email already in use.', 'error')
                return redirect(url_for('manager.manager_profile'))

        user.name = name
        user.email = email
        user.phone = phone
        user.location = location
        user.professional_headline = headline

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
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('manager.manager_profile'))

    return render_template('manager/profile.html', user=user)


@manager_bp.route('/profile/delete-pic', methods=['POST'])
@manager_required
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
    return redirect(url_for('manager.manager_profile'))


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
# Projects — Create New (upload PDF → send to friend's n8n → callback)
# ─────────────────────────────────────────────
@manager_bp.route('/projects/add', methods=['POST'])
@manager_required
def add_project():
    manager_id = session.get('user_id')
    
    # Only specs file is required — no name needed
    if 'specs_file' not in request.files:
        flash('Please upload a project specification PDF.', 'error')
        return redirect(url_for('manager.projects'))
        
    specs_file = request.files['specs_file']
    
    if not specs_file.filename:
        flash('Please select a PDF file.', 'error')
        return redirect(url_for('manager.projects'))
    
    if not allowed_file(specs_file.filename):
        flash('Invalid file type. Only PDF files are allowed.', 'error')
        return redirect(url_for('manager.projects'))
    
    # Save specs file
    upload_folder = os.path.join(current_app.root_path, 'uploads', 'projects', 'specs')
    os.makedirs(upload_folder, exist_ok=True)
    original_filename = specs_file.filename
    specs_filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{original_filename}")
    specs_path = os.path.join(upload_folder, specs_filename)
    specs_file.save(specs_path)
    
    # ── Step 1: Extract text from specs PDF ──
    specs_text = ""
    try:
        import pdfplumber
        with pdfplumber.open(specs_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                specs_text += page_text
        
        print(f"\n{'='*60}")
        print(f"📄 EXTRACTED TEXT ({len(specs_text)} chars):")
        print(specs_text[:500])
        print(f"{'='*60}\n")
        
        if not specs_text.strip():
            flash('Could not extract text from the PDF. The file may be scanned/image-based.', 'error')
            return redirect(url_for('manager.projects'))
        
    except Exception as e:
        current_app.logger.error(f"❌ Error extracting text from specs: {e}")
        flash(f'Error reading the PDF file: {str(e)}', 'error')
        return redirect(url_for('manager.projects'))
    
    # ── Step 2: Create project in DB first (status = "analyzing") ──
    project_name = original_filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
    project = Project(
        name=project_name,
        description='AI analysis in progress...',
        manager_id=manager_id,
        status='pending',
        specs_path=specs_path,
        specs_file=original_filename
    )
    db.session.add(project)
    db.session.commit()
    
    print(f"✅ Project created in DB with ID: {project.id}")
    
    # ── Step 3: Send text + project_id + callback_url to friend's n8n ──
    n8n_url = current_app.config.get('N8N_PROJECT_WEBHOOK_URL')
    public_url = current_app.config.get('PUBLIC_URL', '')
    callback_url = f"{public_url}/manager/api/project/callback"
    
    try:
        import requests as req_lib
        
        payload = {
            'texte': specs_text,
            'project_id': project.id,
            'callback_url': callback_url
        }
        
        print(f"\n{'='*60}")
        print(f"📤 SENDING TO FRIEND'S n8n: {n8n_url}")
        print(f"📦 project_id: {project.id}")
        print(f"📦 callback_url: {callback_url}")
        print(f"📦 texte length: {len(specs_text)} chars")
        print(f"📦 texte preview: {specs_text[:200]}")
        print(f"{'='*60}\n")
        
        response = req_lib.post(
            n8n_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30  # Just sending — don't wait for AI to finish
        )
        
        print(f"📥 FRIEND RESPONSE: {response.status_code} — {response.text[:500]}")
        
        if response.status_code == 200:
            flash(f'Project "{project_name}" created! AI analysis is in progress — results will appear shortly.', 'success')
        else:
            current_app.logger.error(f"❌ Webhook error: {response.status_code} - {response.text}")
            flash(f'Project created but AI analysis request failed (HTTP {response.status_code}). You can check again later.', 'warning')
            
    except req_lib.exceptions.Timeout:
        flash(f'Project "{project_name}" created but the AI service is slow. Results will appear when ready.', 'warning')
    except req_lib.exceptions.ConnectionError:
        current_app.logger.error("❌ Cannot connect to friend's n8n")
        flash(f'Project created but cannot reach AI service. Is your friend\'s ngrok running?', 'error')
    except Exception as e:
        current_app.logger.error(f"❌ Error sending to n8n: {e}")
        flash(f'Project created but AI request failed: {str(e)}', 'warning')
    
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
# API: Callback from friend's n8n — receives AI analysis
# ─────────────────────────────────────────────
@manager_bp.route('/api/project/callback', methods=['POST'])
def project_analysis_callback():
    """
    Callback endpoint for friend's n8n workflow.
    Receives the AI analysis results and updates the project + creates tasks.
    
    Friend's n8n sends JSON like:
    {
      "project_id": 123,
      "analysis_results": {
        "nom_projet": "...",
        "resume": "...",
        "besoins_fonctionnels": [...],
        "besoins_non_fonctionnels": [...],
        "livrables": [...]
      }
    }
    
    But we also handle the full format with taches_techniques etc.
    """
    try:
        data = request.get_json()
        
        print(f"\n{'='*60}")
        print(f"📥 CALLBACK RECEIVED!")
        print(f"📥 RAW DATA: {json.dumps(data, ensure_ascii=False)[:2000]}")
        print(f"{'='*60}\n")
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Get project ID
        project_id = data.get('project_id')
        if not project_id:
            return jsonify({'success': False, 'error': 'project_id is required'}), 400
        
        # Find project
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'success': False, 'error': f'Project {project_id} not found'}), 404
        
        # The friend's n8n may wrap results in "analysis_results" key
        ai_data = data.get('analysis_results', data)
        
        # Handle case where response might be wrapped in a list
        if isinstance(ai_data, list) and len(ai_data) > 0:
            ai_data = ai_data[0]
        
        # If there's an 'output' wrapper, unwrap it
        if isinstance(ai_data, dict) and 'output' in ai_data and isinstance(ai_data['output'], dict):
            ai_data = ai_data['output']
        
        print(f"📦 PARSED AI DATA KEYS: {list(ai_data.keys()) if isinstance(ai_data, dict) else type(ai_data)}")
        
        # Update project with AI results
        nom_projet = ai_data.get('nom_projet', '').strip()
        if nom_projet:
            project.nom_projet = nom_projet
            project.name = nom_projet
        
        project.resume = ai_data.get('resume', '').strip() or None
        project.description = ai_data.get('resume', '') or project.description
        
        # Handle besoins — friend sends flat keys, or nested
        besoins = ai_data.get('besoins', {})
        if not besoins:
            # Friend may send besoins_fonctionnels and besoins_non_fonctionnels at top level
            fonctionnels = ai_data.get('besoins_fonctionnels', [])
            non_fonctionnels = ai_data.get('besoins_non_fonctionnels', [])
            if fonctionnels or non_fonctionnels:
                besoins = {'fonctionnels': fonctionnels, 'non_fonctionnels': non_fonctionnels}
        project.besoins = besoins
        
        # Handle livrables — friend may send as "livrables" or "livrables_attendus"
        livrables = ai_data.get('livrables_attendus', ai_data.get('livrables', []))
        project.livrables_attendus = livrables
        
        # Other fields (if present in AI response)
        project.taches_techniques = ai_data.get('taches_techniques', [])
        project.analyse_ressources = ai_data.get('analyse_ressources', {})
        project.estimation_globale = ai_data.get('estimation_globale', {})
        project.specs_data = data  # Store complete callback data
        project.status = 'pending'
        
        # Delete old tasks before creating new ones
        Task.query.filter_by(project_id=project.id).delete()
        
        # Create Task records from taches_techniques
        tasks_created = 0
        taches_techniques = ai_data.get('taches_techniques', [])
        
        for tache_data in taches_techniques:
            task = Task(
                project_id=project.id,
                task_id=tache_data.get('id_tache', f'T{tasks_created + 1}'),
                nom=tache_data.get('nom', ''),
                priorite=tache_data.get('priorite'),
                dependances=tache_data.get('dependances', []),
                duree_estimee_jours=tache_data.get('duree_estimee_jours'),
                status='not started',
                sous_taches=tache_data.get('sous_taches', [])
            )
            db.session.add(task)
            tasks_created += 1
        
        db.session.commit()
        
        print(f"✅ Project {project_id} updated! Name: {project.name}, Tasks: {tasks_created}")
        current_app.logger.info(f"✅ Project {project_id} updated with AI analysis. {tasks_created} tasks created.")
        
        # ── Auto-match tasks to employees ──
        match_results = []
        try:
            match_results = auto_match_tasks(project.id)
            if match_results:
                print(f"🤖 AUTO-MATCHING: {len(match_results)} tasks matched to employees:")
                for m in match_results:
                    print(f"   • {m['task_id']} → {m['employee_name']} (score: {m['score']})")
            else:
                print("⚠️ AUTO-MATCHING: No employees available or no skills to match.")
        except Exception as match_err:
            print(f"⚠️ Auto-matching error (non-fatal): {match_err}")
            current_app.logger.warning(f"Auto-matching failed: {match_err}")
        
        return jsonify({
            'success': True,
            'message': f'Project "{project.name}" updated with {tasks_created} tasks',
            'matched': len(match_results),
            'matches': match_results
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"❌ Callback error: {e}")
        print(f"❌ CALLBACK ERROR: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to update project: {str(e)}'
        }), 500


# Keep old endpoint as alias for backward compatibility
@manager_bp.route('/api/project/update', methods=['POST'])
def api_update_project():
    """Alias for project_analysis_callback (backward compat)"""
    return project_analysis_callback()


# ─────────────────────────────────────────────
# Project Detail Page (Tasks View)
# ─────────────────────────────────────────────
@manager_bp.route('/project/<int:project_id>')
@manager_required
def project_detail(project_id):
    """View project details with task breakdown and employee assignment"""
    project = Project.query.get_or_404(project_id)
    
    # Get all tasks for this project, ordered by task_id (T1, T2, ... T10, T11)
    tasks = Task.query.filter_by(project_id=project.id).all()
    tasks.sort(key=lambda t: (int(''.join(filter(str.isdigit, t.task_id)) or 0), t.task_id))
    
    # Get all employees for assignment dropdown
    employees = User.query.filter_by(role='employee', status='active').all()
    
    # Calculate project statistics
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == 'completed')
    in_progress_tasks = sum(1 for t in tasks if t.status == 'in_progress')
    assigned_tasks = sum(1 for t in tasks if t.assigned_employee_id is not None)
    
    total_days = sum(t.duree_estimee_jours or 0 for t in tasks)
    
    stats = {
        'total_tasks': total_tasks,
        'completed': completed_tasks,
        'in_progress': in_progress_tasks,
        'not_started': total_tasks - completed_tasks - in_progress_tasks,
        'assigned': assigned_tasks,
        'unassigned': total_tasks - assigned_tasks,
        'total_days': total_days
    }
    
    return render_template('manager/project_detail.html', 
                         project=project, 
                         tasks=tasks, 
                         employees=employees,
                         stats=stats)


@manager_bp.route('/project/<int:project_id>/auto-match', methods=['POST'])
@manager_required
def auto_match_project(project_id):
    """Manually trigger auto-matching for unassigned tasks in a project."""
    project = Project.query.get_or_404(project_id)
    try:
        results = auto_match_tasks(project.id)
        if results:
            names = ', '.join(f"{r['task_id']}→{r['employee_name']}" for r in results)
            flash(f'🤖 Auto-matched {len(results)} tasks: {names}', 'success')
        else:
            flash('No unassigned tasks to match, or no available employees.', 'warning')
    except Exception as e:
        flash(f'Auto-matching error: {str(e)}', 'error')
    return redirect(url_for('manager.project_detail', project_id=project_id))


@manager_bp.route('/project/<int:project_id>/task/<int:task_id>/assign', methods=['POST'])
@manager_required
def assign_task(project_id, task_id):
    """Assign an employee to a task"""
    task = Task.query.get_or_404(task_id)
    
    if task.project_id != project_id:
        flash('Invalid task/project combination', 'error')
        return redirect(url_for('manager.project_detail', project_id=project_id))
    
    employee_id = request.form.get('employee_id')
    
    if employee_id:
        employee = User.query.get(employee_id)
        if not employee or employee.role != 'employee':
            flash('Invalid employee', 'error')
            return redirect(url_for('manager.project_detail', project_id=project_id))
        
        task.assigned_employee_id = employee_id
        task.assigned_at = datetime.utcnow()
        
        db.session.commit()
        flash(f'✅ Task "{task.nom}" assigned to {employee.full_name}', 'success')
    else:
        # Unassign
        task.assigned_employee_id = None
        task.assigned_at = None
        db.session.commit()
        flash(f'✅ Task "{task.nom}" unassigned', 'success')
    
    return redirect(url_for('manager.project_detail', project_id=project_id))


@manager_bp.route('/project/<int:project_id>/task/<int:task_id>/status', methods=['POST'])
@manager_required  
def update_task_status(project_id, task_id):
    """Update task status — triggers auto-reassignment when completed"""
    task = Task.query.get_or_404(task_id)
    
    if task.project_id != project_id:
        flash('Invalid task/project combination', 'error')
        return redirect(url_for('manager.project_detail', project_id=project_id))
    
    new_status = request.form.get('status')
    
    if new_status in ['not started', 'in_progress', 'completed']:
        old_status = task.status
        task.status = new_status
        db.session.commit()
        flash(f'Task status updated to "{new_status}"', 'success')
        
        # Auto-reassign when task is completed
        if new_status == 'completed' and old_status != 'completed':
            # Try to reassign the primary assignee
            if task.assigned_employee_id:
                result = auto_reassign_employee(task.assigned_employee_id, project_id)
                if result:
                    flash(
                        f'🤖 {result["employee_name"]} finished their task and was auto-assigned to help on {result["task_id"]} ({result["task_name"]}) — {result["score"]:.0f}% match',
                        'success'
                    )
            
            # Try to reassign collaborators too
            for collab in task.collaborators:
                result = auto_reassign_employee(collab.employee_id, project_id)
                if result:
                    flash(
                        f'🤖 {result["employee_name"]} was auto-reassigned to help on {result["task_id"]} ({result["task_name"]}) — {result["score"]:.0f}% match',
                        'success'
                    )
    else:
        flash('Invalid status', 'error')
    
    return redirect(url_for('manager.project_detail', project_id=project_id))


@manager_bp.route('/project/<int:project_id>/task/<int:task_id>/edit', methods=['POST'])
@manager_required
def edit_task(project_id, task_id):
    """Edit a task's details"""
    task = Task.query.get_or_404(task_id)
    
    if task.project_id != project_id:
        return jsonify({'success': False, 'error': 'Invalid task'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data'}), 400
    
    if 'nom' in data:
        task.nom = data['nom']
    if 'priorite' in data:
        task.priorite = data['priorite']
    if 'duree_estimee_jours' in data:
        try:
            task.duree_estimee_jours = int(data['duree_estimee_jours'])
        except (ValueError, TypeError):
            pass
    
    old_status = task.status
    if 'status' in data and data['status'] in ['not started', 'in_progress', 'completed']:
        task.status = data['status']
    if 'sous_taches' in data:
        task.sous_taches = data['sous_taches']
    
    db.session.commit()
    
    # Auto-reassign when task is completed via modal
    reassignment_info = None
    if data.get('status') == 'completed' and old_status != 'completed':
        if task.assigned_employee_id:
            reassignment_info = auto_reassign_employee(task.assigned_employee_id, project_id)
        for collab in task.collaborators:
            r = auto_reassign_employee(collab.employee_id, project_id)
            if r and not reassignment_info:
                reassignment_info = r
    
    # Calculate updated project total days
    all_tasks = Task.query.filter_by(project_id=project_id).all()
    total_days = sum(t.duree_estimee_jours or 0 for t in all_tasks)
    
    response = {'success': True, 'message': 'Task updated', 'total_days': total_days}
    if reassignment_info:
        response['reassignment'] = reassignment_info
    
    return jsonify(response)


@manager_bp.route('/project/<int:project_id>/task/<int:task_id>/delete', methods=['POST'])
@manager_required
def delete_task(project_id, task_id):
    """Delete a task"""
    task = Task.query.get_or_404(task_id)
    
    if task.project_id != project_id:
        flash('Invalid task', 'error')
        return redirect(url_for('manager.project_detail', project_id=project_id))
    
    task_name = task.nom
    db.session.delete(task)
    db.session.commit()
    flash(f'Task "{task_name}" deleted.', 'success')
    
    return redirect(url_for('manager.project_detail', project_id=project_id))


@manager_bp.route('/project/<int:project_id>/task/<int:task_id>/remove-collaborator/<int:collab_id>', methods=['POST'])
@manager_required
def remove_collaborator(project_id, task_id, collab_id):
    """Remove a collaborator from a task"""
    collab = TaskCollaborator.query.get_or_404(collab_id)
    
    if collab.task.project_id != project_id or collab.task_id != task_id:
        flash('Invalid collaborator', 'error')
        return redirect(url_for('manager.project_detail', project_id=project_id))
    
    emp_name = collab.employee.full_name
    db.session.delete(collab)
    db.session.commit()
    flash(f'Removed {emp_name} from task helpers', 'success')
    
    return redirect(url_for('manager.project_detail', project_id=project_id))


@manager_bp.route('/project/<int:project_id>/task/<int:task_id>/add-collaborator', methods=['POST'])
@manager_required
def add_collaborator(project_id, task_id):
    """Manually add a collaborator to a task"""
    task = Task.query.get_or_404(task_id)
    
    if task.project_id != project_id:
        flash('Invalid task', 'error')
        return redirect(url_for('manager.project_detail', project_id=project_id))
    
    employee_id = request.form.get('employee_id')
    if not employee_id:
        flash('No employee selected', 'error')
        return redirect(url_for('manager.project_detail', project_id=project_id))
    
    employee = User.query.get(employee_id)
    if not employee:
        flash('Employee not found', 'error')
        return redirect(url_for('manager.project_detail', project_id=project_id))
    
    # Check if already primary or collaborator
    if task.assigned_employee_id == int(employee_id):
        flash(f'{employee.full_name} is already the primary assignee', 'error')
        return redirect(url_for('manager.project_detail', project_id=project_id))
    
    existing = TaskCollaborator.query.filter_by(task_id=task_id, employee_id=employee_id).first()
    if existing:
        flash(f'{employee.full_name} is already helping on this task', 'error')
        return redirect(url_for('manager.project_detail', project_id=project_id))
    
    # Calculate skill match score
    required_skills = task.get_required_skills()
    score = employee.calculate_skill_match_score(required_skills) if required_skills else 50
    
    collab = TaskCollaborator(
        task_id=task_id,
        employee_id=int(employee_id),
        role='helper',
        match_score=score,
        reason=f'Manually added by manager'
    )
    db.session.add(collab)
    db.session.commit()
    flash(f'✅ {employee.full_name} added as helper on "{task.nom}"', 'success')
    
    return redirect(url_for('manager.project_detail', project_id=project_id))


# ─────────────────────────────────────────────
# Employees Page (separate from dashboard)
# ─────────────────────────────────────────────
@manager_bp.route('/employees')
@manager_required
def employees():
    all_employees = User.query.filter_by(role='employee').order_by(User.created_at.desc()).all()
    
    active_count = sum(1 for e in all_employees if e.status == 'active')
    inactive_count = sum(1 for e in all_employees if e.status == 'inactive')
    
    stats = {
        'total': len(all_employees),
        'active': active_count,
        'inactive': inactive_count,
    }
    return render_template('manager/employees.html', employees=all_employees, stats=stats)

