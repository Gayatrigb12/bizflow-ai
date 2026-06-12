from flask import Blueprint, jsonify, request

from backend.auth.permissions import jwt_required, requires_roles
from backend.services.order_service import OrderService
from backend.storage.database import get_db_session
from backend.routes.error_utils import error_response, not_found, bad_request

order_bp = Blueprint('order_bp', __name__)


@order_bp.route('/api/orders', methods=['GET'])
@jwt_required
def api_orders():
    try:
        with get_db_session() as session:
            orders = OrderService(session).list_orders()
        return jsonify(orders)
    except Exception as exc:
        return error_response(exc, 'Failed to load orders')


@order_bp.route('/api/orders', methods=['POST'])
@requires_roles('staff', 'manager', 'admin')
def api_create_order():
    payload = request.get_json(silent=True) or {}
    try:
        with get_db_session() as session:
            order = OrderService(session).create_order(
                customer_name=str(payload.get('customer') or 'Walk-in'),
                items=payload.get('items') or [],
                status=str(payload.get('status') or 'paid'),
                payment_status=str(payload.get('payment_status') or 'paid'),
            )
            # Convert to dict BEFORE the session closes to avoid DetachedInstanceError
            result = order.to_dict()

        return jsonify(result)
    except ValueError as exc:
        return bad_request(str(exc))
    except Exception as exc:
        return error_response(exc, 'Failed to create order')


@order_bp.route('/api/orders/<invoice_number>', methods=['PATCH'])
@requires_roles('staff', 'manager', 'admin')
def api_update_order_status(invoice_number: str):
    payload = request.get_json(silent=True) or {}
    status = str(payload.get('status') or '')
    if not status:
        return bad_request('Status is required')

    try:
        with get_db_session() as session:
            order = OrderService(session).update_order_status(invoice_number, status)
            if not order:
                return not_found('Order not found')
            # Convert to dict BEFORE the session closes
            result = order.to_dict()

        return jsonify(result)
    except Exception as exc:
        return error_response(exc, 'Failed to update order status')
