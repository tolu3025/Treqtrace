from app import app, db

# Auto-create database tables on startup safely
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print("Database initialization note:", e)

# Export app object for WSGI / Vercel
app = app

if __name__ == "__main__":
    app.run()
