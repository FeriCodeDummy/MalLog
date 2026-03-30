from app.config import settings
from app.main import create_app

app = create_app()


if __name__ == "__main__":
    app.run(host=settings.http_host, port=settings.http_port, debug=False)
