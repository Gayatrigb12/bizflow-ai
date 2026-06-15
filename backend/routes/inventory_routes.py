from flask import Blueprint, jsonify, request

from backend.auth.permissions import jwt_required, requires_roles
from backend.services.inventory_service import InventoryService
from backend.storage.database import get_db_session

inventory_bp = Blueprint('inventory_bp', __name__)


@inventory_bp.route('/api/inventory', methods=['GET'])
@jwt_required
def api_inventory():
    with get_db_session() as session:
        products = InventoryService(session).list_products()
    return jsonify(products)


@inventory_bp.route('/api/inventory', methods=['POST'])
@requires_roles('manager', 'admin')
def api_create_inventory():
    payload = request.get_json(silent=True) or {}

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

        # ✅ FIX: convert BEFORE session closes
        result = product.to_dict()

    return jsonify(result)


@inventory_bp.route('/api/inventory/<int:product_id>', methods=['PATCH'])
@requires_roles('manager', 'admin')
def api_update_inventory(product_id: int):
    payload = request.get_json(silent=True) or {}
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
    return jsonify(updated.to_dict())


@inventory_bp.route('/api/inventory/<int:product_id>', methods=['DELETE'])
@requires_roles('manager', 'admin')
def api_delete_inventory(product_id: int):
    with get_db_session() as session:
        service = InventoryService(session)
        ok = service.delete_product_by_id(product_id)
    return jsonify({'ok': ok})
