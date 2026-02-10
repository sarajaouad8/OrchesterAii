from routes.auth import auth_bp
from routes.main import main_bp
from routes.admin import admin_bp
from routes.manager import manager_bp
from routes.employee import employee_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app."""
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(employee_bp)
