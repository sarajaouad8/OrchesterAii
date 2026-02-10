from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models after db is created to avoid circular imports
from models.user import User
from models.project import Project