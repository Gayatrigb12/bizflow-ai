import logging
import traceback

from flask import jsonify

logger = logging.getLogger('bizflow')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def error_response(exc: Exception, message: str = 'Internal server error', status: int = 500):
    """Log the full traceback and return a consistent JSON error response."""
    logger.error('%s: %s\n%s', message, exc, traceback.format_exc())
    return jsonify({'error': message, 'details': str(exc)}), status


def not_found(message: str = 'Resource not found'):
    return jsonify({'error': message}), 404


def bad_request(message: str = 'Invalid request'):
    return jsonify({'error': message}), 400
