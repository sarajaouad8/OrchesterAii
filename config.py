import os

class Config:
    """Base configuration"""
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'orchestrai-dev-secret-key-change-in-production')
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    CV_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'cvs')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # n8n webhook URL - UPDATED WITH YOUR NGROK  
    N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL', 'https://toshia-nonfacetious-rachael.ngrok-free.dev/webhook/cv-analysis')
    
    # n8n webhook URL for project specs analysis
    N8N_PROJECT_WEBHOOK_URL = os.getenv('N8N_PROJECT_WEBHOOK_URL', 'https://toshia-nonfacetious-rachael.ngrok-free.dev/webhook-test/analyse-pdf')
    
    # Your public URL (update this with your current ngrok URL)
    PUBLIC_URL = os.getenv('PUBLIC_URL', 'https://untrumpeted-prenational-celeste.ngrok-free.dev')
    
    # Backup URLs for reliability
    N8N_BACKUP_URLS = [
        'https://toshia-nonfacetious-rachael.ngrok-free.dev/webhook/cv-analysis',
        'http://localhost:5678/webhook/cv-analysis'  # Direct n8n
    ]
class DevelopmentConfig(Config):
    """Development configuration"""
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:sara123@localhost:5432/orchestraai_db'
    )
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    TESTING = True

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}