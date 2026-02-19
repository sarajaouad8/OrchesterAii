from datetime import datetime
from models import db


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    specs_path = db.Column(db.String(500), nullable=True)
    specs_file = db.Column(db.String(200), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # AI-analyzed detailed project data from CDC
    nom_projet = db.Column(db.String(300), nullable=True)
    resume = db.Column(db.Text, nullable=True)
    livrables_attendus = db.Column(db.JSON, nullable=True)  # List of deliverables
    besoins = db.Column(db.JSON, nullable=True)  # {fonctionnels: [], non_fonctionnels: []}
    taches_techniques = db.Column(db.JSON, nullable=True)  # Complete tasks with sous-taches
    analyse_ressources = db.Column(db.JSON, nullable=True)  # Resource analysis
    estimation_globale = db.Column(db.JSON, nullable=True)  # Global estimates
    
    # Legacy fields (for backward compatibility)
    required_skills = db.Column(db.JSON, nullable=True)
    project_type = db.Column(db.String(100), nullable=True)
    tech_stack = db.Column(db.JSON, nullable=True)
    complexity = db.Column(db.String(20), nullable=True)
    estimated_duration = db.Column(db.String(50), nullable=True)
    key_features = db.Column(db.JSON, nullable=True)
    specs_data = db.Column(db.JSON, nullable=True)

    # Relationships
    manager = db.relationship('User', backref=db.backref('projects', lazy='dynamic'))
    tasks = db.relationship('Task', backref='project', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Project {self.name}>'


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    task_id = db.Column(db.String(50), nullable=False)  # e.g., "T1", "T2"
    nom = db.Column(db.String(300), nullable=False)
    priorite = db.Column(db.String(20), nullable=True)  # Haute, Moyenne, Basse
    dependances = db.Column(db.JSON, nullable=True)  # List of task IDs
    duree_estimee_jours = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(50), default='not started')  # not started, in_progress, completed
    sous_taches = db.Column(db.JSON, nullable=True)  # Array of sub-tasks
    
    # Employee assignment
    assigned_employee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=True)
    match_score = db.Column(db.Float, nullable=True)  # Matching score from skills comparison
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assigned_employee = db.relationship('User', backref=db.backref('assigned_tasks', lazy='dynamic'))

    def __repr__(self):
        return f'<Task {self.task_id}: {self.nom}>'
    
    def get_required_skills(self):
        """Extract all required skills from sous-taches"""
        skills = set()
        if self.sous_taches:
            for st in self.sous_taches:
                if 'competences_requises' in st:
                    skills.update(st['competences_requises'])
        return list(skills)
