from typing import Any, Dict, List

from backend.services.customer_service import CustomerService
from backend.services.inventory_service import InventoryService
from backend.services.order_service import OrderService
from backend.storage.repositories.activity_repository import ActivityRepository


def execute_action(session, action: Dict[str, Any], actor: str = 'AI') -> Dict[str, Any]:
    action_type = action.get('type')
    inventory_service = InventoryService(session)
    customer_service = CustomerService(session)
    order_service = OrderService(session)
    activity_repository = ActivityRepository(session)

    if action_type == 'add_product':
        product = inventory_service.create_or_update_product(
            name=str(action.get('name') or ''),
            sku=str(action.get('sku') or ''),
            price=float(action.get('price') or 0.0),
            qty=float(action.get('qty') or 0.0),
            unit=str(action.get('unit') or 'pcs'),
        )
        activity_repository.log('inventory', f"Added/updated product {product.name}", actor)
        return {'type': 'add_product', 'id': product.id}

    if action_type == 'update_stock':
        product = inventory_service.adjust_stock(
            name=str(action.get('name') or ''),
            qty_change=float(action.get('qty_change') or 0.0),
        )
        if product:
            activity_repository.log('inventory', f"Updated stock for {product.name}", actor)
            return {'type': 'update_stock', 'id': product.id}
        return {'type': 'update_stock', 'error': 'Product not found'}

    if action_type == 'create_order':
        order = order_service.create_order(
            customer_name=str(action.get('customer') or 'Walk-in'),
            items=action.get('items') or [],
            status=str(action.get('status') or 'paid'),
            payment_status=str(action.get('payment_status') or 'paid'),
        )
        activity_repository.log('order', f"Created order {order.invoice_number}", actor)
        return {
            'type': 'create_order',
            'invoice_number': order.invoice_number,
            'total': float(order.total or 0.0),
            'customer': order.customer.name if order.customer else None,
            'items': [item.to_dict() for item in order.items],
        }

    if action_type == 'add_customer':
        customer = customer_service.create_customer(
            name=str(action.get('name') or ''),
            phone=str(action.get('phone') or ''),
            email=str(action.get('email') or ''),
            address=str(action.get('address') or ''),
        )
        activity_repository.log('customer', f"Added customer {customer.name}", actor)
        return {'type': 'add_customer', 'id': customer.id}

    if action_type == 'delete_product':
        deleted = inventory_service.delete_product(str(action.get('name') or ''))
        if deleted:
            activity_repository.log('inventory', f"Deleted product {action.get('name')}", actor)
            return {'type': 'delete_product'}
        return {'type': 'delete_product', 'error': 'Product not found'}

    if action_type == 'update_order_status':
        order = order_service.update_order_status(
            invoice_number=str(action.get('id') or ''),
            status=str(action.get('status') or ''),
        )
        if order:
            activity_repository.log('order', f"Updated order {order.invoice_number} to {order.status}", actor)
            return {'type': 'update_order_status', 'id': order.invoice_number}
        return {'type': 'update_order_status', 'error': 'Order not found'}

    if action_type == 'info':
        return {'type': 'info'}

    return {'type': action_type, 'error': 'Unsupported action type'}


def execute_actions(session, actions: List[Dict[str, Any]], actor: str = 'AI') -> List[Dict[str, Any]]:
    return [execute_action(session, action, actor) for action in actions or []]
