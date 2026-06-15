from typing import Dict, Any, List

VALID_ACTIONS = {
    'add_product': ['name', 'price', 'qty'],
    'update_stock': ['name', 'qty_change'],
    'create_order': ['customer', 'items'],
    'add_customer': ['name'],
    'delete_product': ['name'],
    'update_order_status': ['id', 'status'],
    'info': [],
}


class ActionValidationResult:
    def __init__(self, action: Dict[str, Any], valid: bool, errors: List[str] | None = None, requires_approval: bool = False):
        self.action = action
        self.valid = valid
        self.errors = errors or []
        self.requires_approval = requires_approval


class ActionValidator:
    def __init__(self, session=None, inventory_service=None):
        self.session = session
        self.inventory_service = inventory_service

    def validate(self, action: Dict[str, Any]) -> ActionValidationResult:
        if not isinstance(action, dict):
            return ActionValidationResult(action, False, ['Action must be an object'])
        action_type = action.get('type')
        if action_type not in VALID_ACTIONS:
            return ActionValidationResult(action, False, [f'Unknown action type: {action_type}'])

        errors = []
        for field in VALID_ACTIONS[action_type]:
            if field not in action:
                errors.append(f'Missing required field: {field}')

        # domain checks
        if action_type == 'create_order':
            items = action.get('items') or []
            if not isinstance(items, list) or not items:
                errors.append('Order must include at least one item')
            else:
                for it in items:
                    if not it.get('name'):
                        errors.append('Order item missing name')
                    if float(it.get('qty', 0)) <= 0:
                        errors.append('Order item qty must be > 0')

        requires_approval = False

        if action_type == 'create_order':
            total_value = 0.0
            for item in items:
                qty = float(item.get('qty', 0)) if isinstance(item.get('qty', 0), (int, float, str)) else 0.0
                if qty > 20:
                    requires_approval = True
                name = str(item.get('name') or '').strip()
                if self.inventory_service:
                    product = self.inventory_service.find_by_name(name)
                    if not product:
                        requires_approval = True
                    total_value += (product.price if product else 0.0) * qty
            if total_value > 10000:
                requires_approval = True

        if action_type == 'add_product':
            price = float(action.get('price') or 0.0)
            qty = float(action.get('qty') or 0.0)
            if price > 50000 or qty > 100:
                requires_approval = True

        if action_type == 'delete_product':
            requires_approval = True

        if action_type == 'update_stock':
            qty_change = float(action.get('qty_change') or 0.0)
            if abs(qty_change) >= 20:
                requires_approval = True
            if self.inventory_service and action.get('name'):
                prod = self.inventory_service.find_by_name(action.get('name'))
                if not prod:
                    errors.append('Product not found for stock update')
                elif qty_change < 0 and prod.quantity + qty_change < 0:
                    errors.append('Stock update would make inventory negative')

        if action_type == 'update_order_status':
            status = str(action.get('status') or '').lower()
            if status in ('cancelled', 'refunded', 'returned'):
                requires_approval = True

        valid = len(errors) == 0
        return ActionValidationResult(action, valid, errors, requires_approval)
