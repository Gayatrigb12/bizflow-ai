import json
import logging
from typing import Any, Dict, List

from backend.ai.action_executor import execute_action
from backend.ai.action_normalizer import normalize_action
from backend.ai.action_validator import ActionValidator
from backend.embeddings.embedding_service import generate_embedding
from backend.embeddings.retriever import similarity_search
from backend.services.analytics_service import AnalyticsService
from backend.services.customer_service import CustomerService
from backend.services.inventory_service import InventoryService
from backend.services.order_service import OrderService
from backend.services.pending_action_service import PendingActionService
from backend.services.report_service import ReportService
from backend.storage.repositories.activity_repository import ActivityRepository

logger = logging.getLogger(__name__)

READ_TOOLS = {
    'list_inventory',
    'search_product',
    'get_low_stock',
    'list_orders',
    'get_order',
    'list_customers',
    'get_customer',
    'search_customer',
    'get_analytics',
    'get_dashboard',
    'get_activity_log',
    'search_knowledge',
}

WRITE_TOOLS = {
    'add_product',
    'update_stock',
    'add_customer',
    'create_order',
    'delete_product',
    'update_order_status',
}

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        'type': 'function',
        'function': {
            'name': 'list_inventory',
            'description': 'List all products with name, sku, price, quantity, and unit.',
            'parameters': {'type': 'object', 'properties': {}, 'required': []},
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'search_product',
            'description': 'Find a product by name and return full details including price and stock.',
            'parameters': {
                'type': 'object',
                'properties': {'name': {'type': 'string', 'description': 'Product name'}},
                'required': ['name'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_low_stock',
            'description': 'List products that are below their low-stock threshold.',
            'parameters': {'type': 'object', 'properties': {}, 'required': []},
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_orders',
            'description': 'List all orders with invoice number, customer, items, totals, and status.',
            'parameters': {'type': 'object', 'properties': {}, 'required': []},
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_order',
            'description': 'Get a single order by invoice number (e.g. INV-1016).',
            'parameters': {
                'type': 'object',
                'properties': {
                    'invoice_number': {'type': 'string', 'description': 'Invoice number like INV-1016'},
                },
                'required': ['invoice_number'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'list_customers',
            'description': 'List all customers with name, phone, email, total spent, and order count.',
            'parameters': {'type': 'object', 'properties': {}, 'required': []},
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_customer',
            'description': 'Get a customer profile by ID including their order history.',
            'parameters': {
                'type': 'object',
                'properties': {'customer_id': {'type': 'integer', 'description': 'Customer ID'}},
                'required': ['customer_id'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'search_customer',
            'description': 'Find a customer by name.',
            'parameters': {
                'type': 'object',
                'properties': {'name': {'type': 'string', 'description': 'Customer name'}},
                'required': ['name'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_analytics',
            'description': 'Get revenue, inventory, customer, and product analytics report.',
            'parameters': {'type': 'object', 'properties': {}, 'required': []},
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_dashboard',
            'description': 'Get full dashboard state: inventory, orders, customers, revenue, and low stock.',
            'parameters': {'type': 'object', 'properties': {}, 'required': []},
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'get_activity_log',
            'description': 'Get recent business activity log entries.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'limit': {'type': 'integer', 'description': 'Max entries to return (default 20)'},
                },
                'required': [],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'search_knowledge',
            'description': 'Semantic search across products, customers, and orders.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {'type': 'string', 'description': 'Search query'},
                    'top_k': {'type': 'integer', 'description': 'Number of results (default 5)'},
                },
                'required': ['query'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'add_product',
            'description': 'Add or update a product in inventory.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'price': {'type': 'number'},
                    'qty': {'type': 'number'},
                    'unit': {'type': 'string'},
                    'sku': {'type': 'string'},
                },
                'required': ['name', 'price', 'qty'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'update_stock',
            'description': 'Adjust product stock by a delta (positive or negative).',
            'parameters': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'qty_change': {'type': 'number'},
                },
                'required': ['name', 'qty_change'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'add_customer',
            'description': 'Add or update a customer.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'phone': {'type': 'string'},
                    'email': {'type': 'string'},
                    'address': {'type': 'string'},
                },
                'required': ['name'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'create_order',
            'description': 'Create an invoice/order for a customer with line items.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'customer': {'type': 'string'},
                    'items': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'name': {'type': 'string'},
                                'qty': {'type': 'number'},
                            },
                            'required': ['name', 'qty'],
                        },
                    },
                    'status': {'type': 'string'},
                    'payment_status': {'type': 'string'},
                },
                'required': ['customer', 'items'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'delete_product',
            'description': 'Delete a product from inventory (may require manager approval).',
            'parameters': {
                'type': 'object',
                'properties': {'name': {'type': 'string'}},
                'required': ['name'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'update_order_status',
            'description': 'Update an order status by invoice number.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'description': 'Invoice number'},
                    'status': {'type': 'string'},
                },
                'required': ['id', 'status'],
            },
        },
    },
]


class ToolExecutor:
    def __init__(self, session, actor: str = 'AI'):
        self.session = session
        self.actor = actor
        self.inventory_service = InventoryService(session)
        self.customer_service = CustomerService(session)
        self.order_service = OrderService(session)
        self.analytics_service = AnalyticsService(session)
        self.report_service = ReportService(session)
        self.activity_repository = ActivityRepository(session)
        self.validator = ActionValidator(session, self.inventory_service)
        self.executed_writes: List[Dict[str, Any]] = []
        self.validation_results: List[Dict[str, Any]] = []
        self.pending_action_ids: List[int] = []

    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if tool_name in READ_TOOLS:
                return {'success': True, 'data': self._execute_read(tool_name, arguments)}
            if tool_name in WRITE_TOOLS:
                return self._execute_write(tool_name, arguments)
            return {'success': False, 'error': f'Unknown tool: {tool_name}'}
        except Exception as exc:
            logger.exception('Tool %s failed', tool_name)
            return {'success': False, 'error': str(exc)}

    def _execute_read(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if tool_name == 'list_inventory':
            return self.inventory_service.list_products()

        if tool_name == 'search_product':
            product = self.inventory_service.find_by_name(str(args.get('name') or ''))
            return product.to_dict() if product else None

        if tool_name == 'get_low_stock':
            return self.inventory_service.get_low_stock_products()

        if tool_name == 'list_orders':
            return self.order_service.list_orders()

        if tool_name == 'get_order':
            invoice = str(args.get('invoice_number') or args.get('id') or '')
            return self.order_service.get_by_invoice(invoice)

        if tool_name == 'list_customers':
            return self.customer_service.list_customers()

        if tool_name == 'get_customer':
            customer_id = int(args.get('customer_id'))
            return self.customer_service.get_customer_profile(customer_id)

        if tool_name == 'search_customer':
            customer = self.customer_service.get_by_name(str(args.get('name') or ''))
            return customer.to_dict() if customer else None

        if tool_name == 'get_analytics':
            return self.analytics_service.build_analytics_report()

        if tool_name == 'get_dashboard':
            return self.report_service.build_dashboard_state()

        if tool_name == 'get_activity_log':
            limit = min(int(args.get('limit') or 20), 50)
            activities = self.activity_repository.list_recent(limit=limit)
            return [
                {
                    'action_type': activity.action_type,
                    'description': activity.description,
                    'actor': activity.actor,
                    'created_at': activity.created_at.isoformat() if activity.created_at else None,
                }
                for activity in activities
            ]

        if tool_name == 'search_knowledge':
            query = str(args.get('query') or '').strip()
            top_k = min(int(args.get('top_k') or 5), 10)
            embedding = generate_embedding(query)
            return similarity_search(self.session, embedding, top_k=top_k)

        raise ValueError(f'Unhandled read tool: {tool_name}')

    def _execute_write(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        action = normalize_action({'type': tool_name, **(args or {})})
        validation = self.validator.validate(action)
        validation_entry = {
            'action': action,
            'valid': validation.valid,
            'errors': validation.errors,
            'requires_approval': validation.requires_approval,
        }
        self.validation_results.append(validation_entry)

        if not validation.valid:
            return {'success': False, 'errors': validation.errors, 'action': action}

        if validation.requires_approval:
            pending = PendingActionService(self.session).create_pending_action(
                [action],
                reply=f'Approval required for {tool_name}',
                requested_by=self.actor,
            )
            self.pending_action_ids.append(pending.id)
            return {
                'success': True,
                'approval_required': True,
                'pending_action_id': pending.id,
                'message': 'Action queued for manager approval',
            }

        executed = execute_action(self.session, action, actor=self.actor)
        self.executed_writes.append(executed)
        return {'success': True, 'result': executed}


def parse_tool_arguments(raw_arguments: Any) -> Dict[str, Any]:
    if isinstance(raw_arguments, dict):
        return raw_arguments
    if not raw_arguments:
        return {}
    try:
        return json.loads(raw_arguments)
    except json.JSONDecodeError:
        logger.warning('Failed to parse tool arguments: %s', raw_arguments)
        return {}
