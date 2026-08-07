import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'treqtrace-dev-secret-key-2026'
    
    # Detect Vercel serverless environment (where filesystem is read-only except /tmp)
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

    if IS_VERCEL:
        UPLOAD_FOLDER = '/tmp/uploads'
    else:
        UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
