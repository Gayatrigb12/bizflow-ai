import os
import re
import json
import logging
from typing import Dict, Any

from backend.ai.groq_provider import GroqProvider
from backend.ai.prompt_builder import build_system_prompt, extract_json_from_model
from backend.ai.context_builder import ContextBuilder
from backend.ai.action_validator import ActionValidator
from backend.services.customer_service import CustomerService
from backend.services.inventory_service import InventoryService
from backend.services.order_service import OrderService

logger = logging.getLogger(__name__)


def _extract_json(content: str) -> Dict[str, Any] | None:
    parsed = extract_json_from_model(content)
    if parsed is not None:
        return parsed

    if not content or not content.strip():
        return None

    for name, candidate in _json_candidates(content):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            try:
                fixed = re.sub(r',\s*([}\]])', r'\1', candidate)
                return json.loads(fixed)
            except json.JSONDecodeError:
                logger.debug('JSON parse failed for strategy %s', name)
                continue

    logger.warning('Failed to parse model JSON response')
    return None


def _json_candidates(content: str):
    yield 'direct', content.strip()

    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', content, re.IGNORECASE)
    if match:
        yield 'fence', match.group(1).strip()

    for index, char in enumerate(content):
        if char != '{':
            continue
        depth = 0
        for end, ch in enumerate(content[index:], index):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    yield 'brace', content[index:end + 1]
                    break


class AIOrchestrator:
    def __init__(self, session, provider=None):
        self.session = session
        api_key = os.getenv('GROQ_API_KEY', '')
        self.provider = provider or GroqProvider(api_key=api_key)
        self.context_builder = ContextBuilder(session)

    def orchestrate(self, message: str) -> Dict[str, Any]:
        context = self.context_builder.build(message)
        prompt = build_system_prompt(context)

        logger.info('Calling AI provider for chat message')
        raw = self.provider.generate_response(prompt, message)

        choices = raw.get('choices') or []
        if not choices:
            return {
                'reply': 'The AI service returned an unexpected response. Please try again.',
                'raw': raw,
                'actions': [],
                'validation': [],
                'all_valid': False,
            }

        content = choices[0].get('message', {}).get('content', '')
        parsed = _extract_json(content)

        if parsed is None:
            return {
                'reply': 'Sorry, I could not understand the AI response. Please try again.',
                'raw': raw,
                'raw_content': content,
                'actions': [],
                'validation': [],
                'all_valid': False,
            }

        inventory_service = InventoryService(self.session)
        customer_service = CustomerService(self.session)
        order_service = OrderService(self.session)
        validator = ActionValidator(
            self.session,
            inventory_service,
            customer_service,
            order_service,
        )

        actions = parsed.get('actions') if isinstance(parsed.get('actions'), list) else []
        validation_results = []
        all_valid = True

        for act in actions:
            res = validator.validate(act)
            validation_results.append({
                'action': act,
                'valid': res.valid,
                'errors': res.errors,
                'requires_approval': res.requires_approval,
            })
            if not res.valid:
                all_valid = False

        return {
            'reply': parsed.get('reply', ''),
            'raw': raw,
            'actions': actions,
            'validation': validation_results,
            'all_valid': all_valid,
        }
