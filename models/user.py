from models import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string
import json


class User(db.Model):
    """User model for the database"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    location = db.Column(db.String(100), nullable=True)  # "City, Country"
    professional_headline = db.Column(db.String(255), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')
    status = db.Column(db.String(20), nullable=False, default='active')
    
    # Critical fields for task matching
    technical_skills = db.Column(db.JSON, nullable=True)  # Store as JSON object
    certifications = db.Column(db.JSON, nullable=True)    # List of certifications
    languages = db.Column(db.JSON, nullable=True)         # Language proficiency
    years_of_experience = db.Column(db.Integer, nullable=True)  # Calculate from work_experience
    
    # Full CV data (for reference)
    cv_data = db.Column(db.JSON, nullable=True)  # Store complete CV analysis
    cv_file = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def generate_username(name):
        """Generate a unique username from the full name."""
        if not name:
            base = "employee"
        else:
            base = name.lower().replace(' ', '_')
            base = ''.join(c for c in base if c.isalnum() or c == '_')
        
        username = base
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base}_{counter}"
            counter += 1
        return username

    @staticmethod
    def generate_password(length=10):
        """Generate a random secure password."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def get_all_skills(self):
        """Get flat list of all technical skills for matching."""
        if not self.technical_skills:
            return []
        
        all_skills = []
        if isinstance(self.technical_skills, dict):
            for category, skills in self.technical_skills.items():
                if isinstance(skills, list):
                    all_skills.extend(skills)
        return all_skills

    @property
    def competencies(self):
        """Return skills as comma-separated string (for template compatibility)."""
        skills = self.get_all_skills()
        return ', '.join(skills) if skills else None

    def calculate_skill_match_score(self, required_skills):
        """
        Calculate how well this employee matches required skills.
        Returns a score between 0 and 100.
        """
        if not required_skills or not self.technical_skills:
            return 0
        
        employee_skills = [s.lower() for s in self.get_all_skills()]
        required_skills_lower = [s.lower() for s in required_skills]
        
        matched = sum(1 for skill in required_skills_lower if skill in employee_skills)
        score = (matched / len(required_skills_lower)) * 100
        
        return round(score, 2)

    @property
    def full_name(self):
        """Return the user's display name."""
        return self.name or self.username

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'location': self.location,
            'professional_headline': self.professional_headline,
            'role': self.role,
            'status': self.status,
            'technical_skills': self.technical_skills,
            'certifications': self.certifications,
            'languages': self.languages,
            'years_of_experience': self.years_of_experience,
            'cv_file': self.cv_file,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }