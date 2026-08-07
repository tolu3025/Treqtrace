from datetime import timedelta
import os

class Config:
    # Fixed fallback secret key so sessions persist across process restarts
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'treqtrace-production-fixed-secret-key-2026-v1'
    
    # Detect Vercel / serverless environment
    IS_VERCEL = os.environ.get('VERCEL') == '1' or 'VERCEL' in os.environ
    
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = db_url
    elif IS_VERCEL:
        SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/treqtrace.db'
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///treqtrace.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session & Cookie persistence settings to prevent unexpected logouts
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_REFRESH_EACH_REQUEST = True

    if IS_VERCEL:
        UPLOAD_FOLDER = '/tmp/uploads'
    else:
        UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
