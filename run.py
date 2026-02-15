from app import create_app
from app.config import get_settings

app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    port = settings.port
    app.run(host="0.0.0.0", port=port, debug=True)
