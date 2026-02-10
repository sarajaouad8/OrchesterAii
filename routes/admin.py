from flask import Blueprint, render_template
from models import db
from models.user import User

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/database')
def view_database():
    """Simple web page to view database contents"""
    try:
        # Get all users from database
        users = User.query.all()
        
        # Convert to list of dictionaries for easy display
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'email': user.email or 'Not set',
                'role': user.role,
                'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'Unknown',
                'updated_at': user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else 'Unknown'
            })
        
        return render_template('database_viewer.html', users=users_data)
    except Exception as e:
        return f"Database error: {str(e)}"