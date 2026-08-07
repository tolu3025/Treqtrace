from app import app, db

# Auto-create database tables on startup (required for production)
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run()
