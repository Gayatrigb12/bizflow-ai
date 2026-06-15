from flask import Blueprint, jsonify, request

from backend.auth.permissions import jwt_required, requires_roles
from backend.services.customer_service import CustomerService
from backend.storage.database import get_db_session

customer_bp = Blueprint('customer_bp', __name__)


@customer_bp.route('/api/customers', methods=['GET'])
@jwt_required
def api_customers():
    with get_db_session() as session:
        customers = CustomerService(session).list_customers()
    return jsonify(customers)


@customer_bp.route('/api/customers/<int:customer_id>', methods=['GET'])
@jwt_required
def api_customer_detail(customer_id: int):
    with get_db_session() as session:
        profile = CustomerService(session).get_customer_profile(customer_id)
        if not profile:
            return jsonify({'error': 'Customer not found'}), 404
    return jsonify(profile)


@customer_bp.route('/api/customers', methods=['POST'])
@requires_roles('staff', 'manager', 'admin')
def api_create_customer():
    payload = request.get_json(silent=True) or {}
    with get_db_session() as session:
        customer = CustomerService(session).create_customer(
            name=str(payload.get('name') or ''),
            phone=str(payload.get('phone') or ''),
            email=str(payload.get('email') or ''),
            address=str(payload.get('address') or ''),
        )
        result = customer.to_dict()

    return jsonify(result)


@customer_bp.route('/api/customers/<int:customer_id>', methods=['PATCH'])
@requires_roles('staff', 'manager', 'admin')
def api_update_customer(customer_id: int):
    payload = request.get_json(silent=True) or {}
    with get_db_session() as session:
        customer = CustomerService(session).update_customer(
            customer_id=customer_id,
            name=payload.get('name'),
            phone=payload.get('phone'),
            email=payload.get('email'),
            address=payload.get('address'),
        )
        result = customer.to_dict()

    return jsonify(result)


@customer_bp.route('/api/customers/<int:customer_id>', methods=['DELETE'])
@requires_roles('staff', 'manager', 'admin')
def api_delete_customer(customer_id: int):
    with get_db_session() as session:
        ok = CustomerService(session).delete_customer(customer_id)

    if not ok:
        return jsonify({'error': 'Customer not found or has existing orders'}), 404
    return jsonify({'ok': True})
