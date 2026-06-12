from flask import Blueprint, jsonify, request

from backend.auth.permissions import jwt_required, requires_roles
from backend.services.inventory_service import InventoryService
from backend.storage.database import get_db_session
from backend.routes.error_utils import error_response, not_found, bad_request

inventory_bp = Blueprint('inventory_bp', __name__)


@inventory_bp.route('/api/inventory', methods=['GET'])
@jwt_required
def api_inventory():
    try:
        with get_db_session() as session:
            products = InventoryService(session).list_products()
        return jsonify(products)
    except Exception as exc:
        return error_response(exc, 'Failed to load inventory')


@inventory_bp.route('/api/inventory', methods=['POST'])
@requires_roles('manager', 'admin')
def api_create_inventory():
    payload = request.get_json(silent=True) or {}

    try:
        with get_db_session() as session:
            service = InventoryService(session)

            product = service.create_or_update_product(
                name=str(payload.get('name') or ''),
                sku=str(payload.get('sku') or ''),
                price=float(payload.get('price') or 0.0),
                qty=float(payload.get('quantity') or payload.get('qty') or 0.0),
                unit=str(payload.get('unit') or 'pcs'),
                description=str(payload.get('description') or ''),
            )

            # Convert to dict BEFORE the session closes to avoid DetachedInstanceError
            result = product.to_dict()

        return jsonify(result)
    except ValueError as exc:
        return bad_request(str(exc))
    except Exception as exc:
        return error_response(exc, 'Failed to create product')


@inventory_bp.route('/api/inventory/<int:product_id>', methods=['PATCH'])
@requires_roles('manager', 'admin')
def api_update_inventory(product_id: int):
    payload = request.get_json(silent=True) or {}
    try:
        with get_db_session() as session:
            service = InventoryService(session)
            updated = service.update_product_by_id(
                product_id=product_id,
                name=payload.get('name'),
                sku=payload.get('sku'),
                price=payload.get('price'),
                qty=payload.get('quantity') or payload.get('qty'),
                unit=payload.get('unit'),
                description=payload.get('description'),
                low_stock_threshold=payload.get('low_stock_threshold'),
            )
            # Convert to dict BEFORE the session closes
            result = updated.to_dict()

        return jsonify(result)
    except ValueError as exc:
        return not_found(str(exc))
    except Exception as exc:
        return error_response(exc, 'Failed to update product')


@inventory_bp.route('/api/inventory/<int:product_id>', methods=['DELETE'])
@requires_roles('manager', 'admin')
def api_delete_inventory(product_id: int):
    try:
        with get_db_session() as session:
            service = InventoryService(session)
            ok = service.delete_product_by_id(product_id)
        return jsonify({'ok': ok})
    except Exception as exc:
        return error_response(exc, 'Failed to delete product')
