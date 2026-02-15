from flask_apscheduler import APScheduler
from supabase import create_client, Client
from app.config import get_settings, get_supabase_client

# Scheduler Instance
scheduler = APScheduler()

# Supabase Client (Lazy load to prevent import errors)
supabase: Client = None


def init_supabase(app):
    global supabase
    url = app.config.get("SUPABASE_URL")
    key = app.config.get("SUPABASE_KEY")
    if url and key:
        try:
            supabase = create_client(url, key)
            print(f"Supabase initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Supabase: {e}")
    else:
        print("Supabase credentials not found. Skipping initialization.")


def get_supabase():
    """Get Supabase client, falling back to config client if Flask app not initialized."""
    global supabase
    if supabase is not None:
        return supabase
    # Fallback to config client
    return get_supabase_client()


def get_supabase_config():
    """Get Supabase config for frontend."""
    settings = get_settings()
    return {
        "url": settings.supabase_url,
        "anon_key": settings.supabase_anon_key.get_secret_value(),
    }
