import json
import re
from typing import Any, Dict, List, Optional

import requests
from flask import current_app

from backend.ai.action_executor import execute_actions
from backend.services.customer_service import CustomerService
from backend.services.inventory_service import InventoryService
from backend.services.order_service import OrderService
from backend.services.pending_action_service import PendingActionService
from backend.storage.repositories.activity_repository import ActivityRepository
from backend.storage.database import get_db_session
from backend.ai.ai_orchestrator import AIOrchestrator


class ChatService:
    def __init__(self, session):
        self.session = session
        self.inventory_service = InventoryService(session)
        self.customer_service = CustomerService(session)
        self.order_service = OrderService(session)
        self.activity_repository = ActivityRepository(session)

    def build_system_prompt(self, state: Dict[str, Any]) -> str:
        return f"""You are BizFlow AI, a smart ERP assistant for small Indian businesses.
You help manage inventory, orders, and customers via natural language.

INVENTORY: {json.dumps(state.get('inventory', []))}
ORDERS: {json.dumps(state.get('orders', [])[:10])}
CUSTOMERS: {json.dumps(state.get('customers', []))}

Respond ONLY in JSON:
{{
  "reply": "...",
  "actions": []
}}
"""

    def parse_groq_json(self, content: str) -> Optional[Dict[str, Any]]:
        if not content:
            return None

        body = content.strip()
        body = re.sub(r'^```(?:json)?\s*', '', body, flags=re.IGNORECASE)
        body = re.sub(r'\s*```\s*$', '', body)

        try:
            return json.loads(body)
        except json.JSONDecodeError:
            match = re.search(r'\{[\s\S]*\}', body)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
        return None

    def execute_actions(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for action in actions or []:
            if not isinstance(action, dict):
                continue

            print("\n[ACTION EXECUTION]")
            print(action)

            action_type = action.get('type')

            if action_type == 'add_product':
                product = self.inventory_service.create_or_update_product(
                    name=str(action.get('name') or ''),
                    sku=str(action.get('sku') or ''),
                    price=float(action.get('price') or 0.0),
                    qty=float(action.get('qty') or 0.0),
                    unit=str(action.get('unit') or 'pcs'),
                )
                self.activity_repository.log('inventory', f"Added product {product.name}", 'AI')
                results.append({'type': 'add_product', 'id': product.id})

            elif action_type == 'update_stock':
                product = self.inventory_service.adjust_stock(
                    name=str(action.get('name') or ''),
                    qty_change=float(action.get('qty_change') or 0.0),
                )
                if product:
                    results.append({'type': 'update_stock', 'id': product.id})

            elif action_type == 'create_order':
                order = self.order_service.create_order(
                    customer_name=str(action.get('customer') or 'Walk-in'),
                    items=action.get('items') or [],
                    status=str(action.get('status') or 'paid'),
                    payment_status=str(action.get('payment_status') or 'paid'),
                )
                results.append({'type': 'create_order', 'invoice': order.invoice_number})

        return results

    def process_message(self, message: str) -> Dict[str, Any]:

        print("\n================ CHAT SERVICE START ================")
        print("USER MESSAGE:", message)
        print("====================================================\n")

        if not message.strip():
            raise ValueError('Message is required')

        orchestrator = AIOrchestrator(self.session)

        print("\n[CALLING ORCHESTRATOR]")
        result = orchestrator.orchestrate(message)

        print("\n================ ORCHESTRATOR RESULT ================")
        print(json.dumps(result, indent=2, default=str))
        print("====================================================\n")

        executed = []
        approval_required = any(v.get('requires_approval') for v in result.get('validation', []))
        pending_action_id = None

        print("\n[VALIDATION CHECK]")
        print("ALL VALID:", result.get('all_valid'))

        if result.get('all_valid'):

            if approval_required and result.get('actions'):
                pending = PendingActionService(self.session).create_pending_action(
                    result.get('actions', []),
                    result.get('reply', ''),
                    requested_by='AI',
                )
                pending_action_id = pending.id
                print("[PENDING CREATED]", pending_action_id)

            else:
                print("[EXECUTING ACTIONS]")
                executed = execute_actions(self.session, result.get('actions', []))
                print("[EXECUTED]", executed)

        from backend.services.report_service import ReportService

        response = {
            'reply': result.get('reply', 'Done.'),
            'actions': executed,
            'validation': result.get('validation', []),
            'state': ReportService(self.session).build_dashboard_state(),
        }

        print("\n================ FINAL RESPONSE ================")
        print(json.dumps(response, indent=2, default=str))
        print("================================================\n")

        if pending_action_id is not None:
            response['pending_action_id'] = pending_action_id
            response['approval_required'] = True

        return response