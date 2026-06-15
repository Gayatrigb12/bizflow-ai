import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env')

from backend.routes.analytics_routes import analytics_bp
from backend.routes.approval_routes import approval_bp
from backend.routes.auth_routes import auth_bp
from backend.routes.chat_routes import chat_bp
from backend.routes.customer_routes import customer_bp
from backend.routes.error_utils import structured_error
from backend.routes.inventory_routes import inventory_bp
from backend.routes.order_routes import order_bp
from backend.routes.report_routes import report_bp
from backend.routes.state_routes import state_bp
from backend.routes.ui_routes import ui_bp
from backend.storage.database import init_db

logger = logging.getLogger('bizflow')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(Path(__file__).resolve().parents[1] / 'static'),
        template_folder=str(Path(__file__).resolve().parents[1] / 'templates'),
    )

    app.config.from_mapping(
        DATABASE_URL=os.getenv('DATABASE_URL', ''),
        GROQ_API_KEY=os.getenv('GROQ_API_KEY', ''),
        JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY', 'bizflow-ai-secret-key'),
        JWT_ALGORITHM=os.getenv('JWT_ALGORITHM', 'HS256'),
        JWT_ACCESS_TOKEN_EXPIRES_MINUTES=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', '15')),
        JWT_REFRESH_TOKEN_EXPIRES_DAYS=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES_DAYS', '30')),
        DEBUG=os.getenv('FLASK_DEBUG', 'false').lower() in ('1', 'true', 'yes'),
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

    @app.errorhandler(404)
    def handle_not_found(exc):
        return structured_error('Resource not found', code=404)

    @app.errorhandler(500)
    def handle_server_error(exc):
        logger.error('Unhandled server error: %s', exc)
        return structured_error('Internal server error', code=500)

    with app.app_context():
        init_db()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
