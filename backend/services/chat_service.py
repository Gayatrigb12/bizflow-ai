import json
import re
from typing import Any, Dict, List, Optional

from backend.ai.action_executor import execute_actions
from backend.ai.ai_orchestrator import AIOrchestrator
from backend.services.customer_service import CustomerService
from backend.services.inventory_service import InventoryService
from backend.services.order_service import OrderService
from backend.services.pending_action_service import PendingActionService
from backend.services.report_service import ReportService
from backend.storage.repositories.activity_repository import ActivityRepository
from backend.storage.repositories.chat_message_repository import ChatMessageRepository

INVENTORY_ACTIONS = {'add_product', 'update_stock', 'delete_product', 'update_product', 'set_stock'}
ORDER_ACTIONS = {'create_order', 'update_order_status'}
CUSTOMER_ACTIONS = {'add_customer', 'update_customer'}


def _context_type_from_actions(actions: List[Dict[str, Any]]) -> str:
    types = {str(action.get('type') or '') for action in actions or [] if isinstance(action, dict)}
    if types & INVENTORY_ACTIONS:
        return 'inventory'
    if types & ORDER_ACTIONS:
        return 'orders'
    if types & CUSTOMER_ACTIONS:
        return 'customers'
    return 'general'


class ChatService:
    def __init__(self, session):
        self.session = session
        self.inventory_service = InventoryService(session)
        self.customer_service = CustomerService(session)
        self.order_service = OrderService(session)
        self.activity_repository = ActivityRepository(session)
        self.chat_message_repository = ChatMessageRepository(session)

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

    def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not message.strip():
            raise ValueError('Message is required')

        orchestrator = AIOrchestrator(self.session)
        result = orchestrator.orchestrate(message)

        executed: List[Dict[str, Any]] = []
        approval_required = any(v.get('requires_approval') for v in result.get('validation', []))
        pending_action_id = None

        if result.get('all_valid'):
            if approval_required and result.get('actions'):
                pending = PendingActionService(self.session).create_pending_action(
                    result.get('actions', []),
                    result.get('reply', ''),
                    requested_by=actor or 'AI',
                )
                pending_action_id = pending.id
            else:
                executed = execute_actions(self.session, result.get('actions', []), actor=actor or 'AI')

        response = {
            'reply': result.get('reply', 'Done.'),
            'actions': executed,
            'validation': result.get('validation', []),
            'state': ReportService(self.session).build_dashboard_state(),
        }

        if pending_action_id is not None:
            response['pending_action_id'] = pending_action_id
            response['approval_required'] = True

        context_type = _context_type_from_actions(executed or result.get('actions', []))
        metadata = {
            'actions': executed,
            'validation': result.get('validation', []),
            'approval_required': approval_required,
        }
        if pending_action_id is not None:
            metadata['pending_action_id'] = pending_action_id

        self.chat_message_repository.add(
            user_prompt=message,
            ai_response=response['reply'],
            session_id=session_id,
            metadata=metadata,
            actor=actor,
            context_type=context_type,
        )

        return response
