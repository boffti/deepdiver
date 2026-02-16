from flask_apscheduler import APScheduler
from app.db import health_check

# Scheduler Instance
scheduler = APScheduler()


def init_db(app):
    """Initialize database connection."""
    try:
        if health_check():
            print("Database connected successfully")
        else:
            print("Database health check failed")
    except Exception as e:
        print(f"Failed to initialize database: {e}")


def get_supabase_config():
    """Get Supabase config for frontend (returns empty for local DB)."""
    return {
        "url": "",
        "anon_key": "",
    }
