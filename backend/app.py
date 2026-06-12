import os
from pathlib import Path
from flask import Flask
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env')

from backend.routes.chat_routes import chat_bp
from backend.routes.customer_routes import customer_bp
from backend.routes.inventory_routes import inventory_bp
from backend.routes.order_routes import order_bp
from backend.routes.report_routes import report_bp
from backend.routes.analytics_routes import analytics_bp
from backend.routes.ui_routes import ui_bp
from backend.routes.auth_routes import auth_bp
from backend.routes.state_routes import state_bp
from backend.routes.approval_routes import approval_bp
from backend.storage.database import init_db


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(Path(__file__).resolve().parents[1] / 'static'),
        template_folder=str(Path(__file__).resolve().parents[1] / 'templates')
    )

    app.config.from_mapping(
        DATABASE_URL=os.getenv('DATABASE_URL', ''),
        GROQ_API_KEY=os.getenv('GROQ_API_KEY', ''),
        JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'bizflow-ai-secret-key'),
        JWT_ALGORITHM=os.getenv('JWT_ALGORITHM', 'HS256'),
        JWT_ACCESS_TOKEN_EXPIRES_MINUTES=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', '15')),
        JWT_REFRESH_TOKEN_EXPIRES_DAYS=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES_DAYS', '30')),
        DEBUG=os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    )

    app.register_blueprint(state_bp)
    app.register_blueprint(ui_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(approval_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(auth_bp)

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
