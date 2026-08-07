from app import app, db

# Auto-create database tables on startup safely
with app.app_context():
    try:
        db.create_all()
        # Handle database migrations dynamically (add avatar column to existing users table)
        try:
            db.session.execute(db.text("ALTER TABLE users ADD COLUMN avatar VARCHAR(256)"))
            db.session.commit()
        except Exception:
            db.session.rollback()
    except Exception as e:
        print("Database initialization note:", e)

# Export app object for WSGI / Vercel / Railway
app = app

if __name__ == "__main__":
    app.run()
