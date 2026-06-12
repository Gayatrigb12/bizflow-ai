from flask import Blueprint, jsonify, request

from backend.auth.permissions import jwt_required, requires_roles
from backend.services.customer_service import CustomerService
from backend.storage.database import get_db_session
from backend.routes.error_utils import error_response, not_found, bad_request

customer_bp = Blueprint('customer_bp', __name__)


@customer_bp.route('/api/customers', methods=['GET'])
@jwt_required
def api_customers():
    try:
        with get_db_session() as session:
            customers = CustomerService(session).list_customers()
        return jsonify(customers)
    except Exception as exc:
        return error_response(exc, 'Failed to load customers')


@customer_bp.route('/api/customers/<int:customer_id>', methods=['GET'])
@jwt_required
def api_customer_detail(customer_id: int):
    try:
        with get_db_session() as session:
            profile = CustomerService(session).get_customer_profile(customer_id)
            if not profile:
                return not_found('Customer not found')
        return jsonify(profile)
    except Exception as exc:
        return error_response(exc, 'Failed to load customer')


@customer_bp.route('/api/customers', methods=['POST'])
@requires_roles('manager', 'admin')
def api_create_customer():
    payload = request.get_json(silent=True) or {}
    try:
        with get_db_session() as session:
            customer = CustomerService(session).create_customer(
                name=str(payload.get('name') or ''),
                phone=str(payload.get('phone') or ''),
                email=str(payload.get('email') or ''),
                address=str(payload.get('address') or ''),
            )
            # Convert to dict BEFORE the session closes to avoid DetachedInstanceError
            result = customer.to_dict()

        return jsonify(result)
    except ValueError as exc:
        return bad_request(str(exc))
    except Exception as exc:
        return error_response(exc, 'Failed to create customer')
