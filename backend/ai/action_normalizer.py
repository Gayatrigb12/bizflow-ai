from typing import Any, Dict, List
import re

# Maps alternate model outputs to supported action types.
_TYPE_ALIASES = {
    'adjust_stock': 'update_stock',
    'add_inventory': 'add_product',
    'update_product': 'add_product',
    'set_stock': 'add_product',
    'create_customer': 'add_customer',
    'create_invoice': 'create_order',
    'create_order_invoice': 'create_order',
}

_FIELD_ALIASES = {
    'quantity': 'qty',
    'product_name': 'name',
    'product': 'name',
    'invoice': 'id',
}


def _coerce_inventory_action(action: Dict[str, Any]) -> str:
    if 'qty_change' in action and 'price' not in action and 'qty' not in action:
        return 'update_stock'
    return 'add_product'


def _normalize_order_item(item: Dict[str, Any]) -> Dict[str, Any]:
    normalized_item = dict(item)
    if 'product' in normalized_item and 'name' not in normalized_item:
        normalized_item['name'] = normalized_item.pop('product')
    if 'product_name' in normalized_item and 'name' not in normalized_item:
        normalized_item['name'] = normalized_item.pop('product_name')
    if 'quantity' in normalized_item and 'qty' not in normalized_item:
        normalized_item['qty'] = normalized_item.pop('quantity')

    name = str(normalized_item.get('name') or '').strip()
    qty = normalized_item.get('qty')
    match = re.match(
        r'^([\d.]+)\s*(kg|g|pcs|pc|ltr|l|ml|units?)?\s+(.+)$',
        name,
        flags=re.IGNORECASE,
    )
    if match:
        parsed_qty = float(match.group(1))
        parsed_name = match.group(3).strip()
        if parsed_name:
            normalized_item['name'] = parsed_name
        if not qty or float(qty) <= 1:
            normalized_item['qty'] = parsed_qty

    return normalized_item


def _normalize_create_order_fields(action: Dict[str, Any]) -> None:
    if 'customer_name' in action and 'customer' not in action:
        action['customer'] = action.pop('customer_name')
    elif 'name' in action and 'customer' not in action and 'items' in action:
        action['customer'] = action.pop('name')

    items = action.get('items')
    if not isinstance(items, list):
        return

    normalized_items = []
    for item in items:
        if not isinstance(item, dict):
            continue
        normalized_items.append(_normalize_order_item(item))
    action['items'] = normalized_items


def normalize_action(action: Any) -> Any:
    if not isinstance(action, dict):
        return action

    normalized = dict(action)
    action_type = str(normalized.get('type') or '').strip()

    for source, target in _FIELD_ALIASES.items():
        if source in normalized and target not in normalized:
            normalized[target] = normalized.pop(source)

    if action_type in ('update_inventory', 'inventory_update'):
        normalized['type'] = _coerce_inventory_action(normalized)
    elif action_type in _TYPE_ALIASES:
        normalized['type'] = _TYPE_ALIASES[action_type]
    elif action_type:
        normalized['type'] = action_type

    if normalized.get('type') == 'create_order':
        _normalize_create_order_fields(normalized)
    elif normalized.get('type') == 'add_customer':
        if 'customer_name' in normalized and 'name' not in normalized:
            normalized['name'] = normalized.pop('customer_name')
    elif normalized.get('type') == 'update_order_status':
        if 'invoice_number' in normalized and 'id' not in normalized:
            normalized['id'] = normalized.pop('invoice_number')

    return normalized


def normalize_actions(actions: List[Any]) -> List[Any]:
    return [normalize_action(action) for action in actions or []]
