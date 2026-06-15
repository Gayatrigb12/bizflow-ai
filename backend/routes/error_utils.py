import logging
import traceback

from flask import current_app, jsonify

logger = logging.getLogger('bizflow')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def structured_error(message: str, code: int = 500, details: str | None = None):
    body = {
        'error': True,
        'message': message,
        'code': code,
    }
    if details and current_app.debug:
        body['details'] = details
    return jsonify(body), code


def error_response(exc: Exception, message: str = 'Internal server error', status: int = 500):
    logger.error('%s: %s\n%s', message, exc, traceback.format_exc())
    return structured_error(message, code=status, details=str(exc))


def not_found(message: str = 'Resource not found'):
    return structured_error(message, code=404)


def bad_request(message: str = 'Invalid request'):
    return structured_error(message, code=400)
