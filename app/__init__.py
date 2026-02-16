from flask import Flask
from app.extensions import scheduler, init_db, get_supabase_config
from app.dashboard import init_app as init_dashboard
from flask_cors import CORS
from app.config import get_settings


def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for development

    settings = get_settings()

    # Config
    app.config["SCHEDULER_API_ENABLED"] = True

    # Initialize Database
    init_db(app)

    # Initialize Scheduler
    scheduler.init_app(app)

    # Register Blueprints
    init_dashboard(app)

    # Load Tasks (This registers the cron jobs)
    try:
        from app import tasks

        scheduler.start()
        print("Scheduler started")
    except Exception as e:
        print(f"Failed to start scheduler: {e}")

    # Root route to check if app is running
    @app.route("/system/health")
    def system_health():
        return "DeepDiver System Active", 200

    # Expose config to templates
    @app.context_processor
    def inject_supabase_config():
        return {"supabase_config": get_supabase_config()}

    return app
