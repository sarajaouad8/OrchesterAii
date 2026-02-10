from datetime import datetime
from models import db


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed
    cv_path = db.Column(db.String(500), nullable=True)
    specs_path = db.Column(db.String(500), nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    manager = db.relationship('User', backref=db.backref('projects', lazy='dynamic'))

    def __repr__(self):
        return f'<Project {self.name}>'
