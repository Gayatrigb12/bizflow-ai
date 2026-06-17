import json

import pytest

from backend.ai.ai_orchestrator import AIOrchestrator
from backend.ai.tools import ToolExecutor, parse_tool_arguments
from backend.services.inventory_service import InventoryService


def test_parse_tool_arguments_json_string():
    assert parse_tool_arguments('{"name": "Rice"}') == {'name': 'Rice'}


def test_tool_executor_list_inventory(db_session):
    InventoryService(db_session).create_or_update_product(
        name='Rice',
        sku='RIC001',
        price=60.0,
        qty=100,
        unit='kg',
    )
    executor = ToolExecutor(db_session, actor='test')
    result = executor.execute('list_inventory', {})
    assert result['success'] is True
    assert any(item['name'] == 'Rice' for item in result['data'])


def test_tool_executor_search_product_not_found(db_session):
    executor = ToolExecutor(db_session, actor='test')
    result = executor.execute('search_product', {'name': 'Missing'})
    assert result['success'] is True
    assert result['data'] is None


def test_tool_executor_add_product_write(db_session):
    executor = ToolExecutor(db_session, actor='test')
    result = executor.execute('add_product', {'name': 'Sugar', 'price': 40, 'qty': 25, 'unit': 'kg'})
    assert result['success'] is True
    assert result['result']['type'] == 'add_product'
    assert len(executor.executed_writes) == 1


class MockToolProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def chat_completion(self, messages, tools=None, tool_choice='auto', temperature=0.2):
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return response


def test_orchestrator_tool_loop_then_reply(db_session):
    InventoryService(db_session).create_or_update_product(
        name='Rice',
        sku='RIC001',
        price=60.0,
        qty=100,
        unit='kg',
    )

    provider = MockToolProvider([
        {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'tool_calls': [{
                        'id': 'call_1',
                        'type': 'function',
                        'function': {
                            'name': 'list_inventory',
                            'arguments': '{}',
                        },
                    }],
                },
            }],
        },
        {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': 'You have Rice in stock at 100 kg.',
                },
            }],
        },
    ])

    orchestrator = AIOrchestrator(db_session, provider=provider)
    result = orchestrator.orchestrate('What is in inventory?')
    assert provider.calls == 2
    assert 'Rice' in result['reply']
    assert result['actions_executed'] is True


def test_orchestrator_create_order_via_tool(db_session):
    InventoryService(db_session).create_or_update_product(
        name='Rice',
        sku='RIC001',
        price=60.0,
        qty=100,
        unit='kg',
    )

    provider = MockToolProvider([
        {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'tool_calls': [{
                        'id': 'call_1',
                        'type': 'function',
                        'function': {
                            'name': 'create_order',
                            'arguments': json.dumps({
                                'customer': 'Rahul',
                                'items': [{'name': 'Rice', 'qty': 3}],
                            }),
                        },
                    }],
                },
            }],
        },
        {
            'choices': [{
                'message': {
                    'role': 'assistant',
                    'content': 'Invoice created for Rahul for 3 Rice.',
                },
            }],
        },
    ])

    orchestrator = AIOrchestrator(db_session, provider=provider)
    result = orchestrator.orchestrate('Create invoice for Rahul for 3 Rice')
    assert result['actions']
    assert result['actions'][0]['type'] == 'create_order'
    assert 'invoice_number' in result['actions'][0]
