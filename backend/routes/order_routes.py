from flask import Blueprint, jsonify, request

from backend.auth.permissions import jwt_required, requires_roles
from backend.services.order_service import OrderService
from backend.storage.database import get_db_session

order_bp = Blueprint('order_bp', __name__)


@order_bp.route('/api/orders', methods=['GET'])
@jwt_required
def api_orders():
    with get_db_session() as session:
        orders = OrderService(session).list_orders()
    return jsonify(orders)


@order_bp.route('/api/orders', methods=['POST'])
@requires_roles('staff', 'manager', 'admin')
def api_create_order():
    payload = request.get_json(silent=True) or {}
    with get_db_session() as session:
        order = OrderService(session).create_order(
            customer_name=str(payload.get('customer') or 'Walk-in'),
            items=payload.get('items') or [],
            status=str(payload.get('status') or 'paid'),
            payment_status=str(payload.get('payment_status') or 'paid'),
        )
    return jsonify(order.to_dict())


@order_bp.route('/api/orders/<invoice_number>', methods=['PATCH'])
@requires_roles('staff', 'manager', 'admin')
def api_update_order_status(invoice_number: str):
    payload = request.get_json(silent=True) or {}
    status = str(payload.get('status') or '')
    with get_db_session() as session:
        order = OrderService(session).update_order_status(invoice_number, status)
        if not order:
            return jsonify({'error': 'Order not found'}), 404
    return jsonify(order.to_dict())
