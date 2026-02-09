from flask import Flask
from config import config
from models import db
from routes import register_blueprints


def create_app(config_name='development'):
    """Application factory — creates and configures the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)

    # Register all blueprints (routes)
    register_blueprints(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
