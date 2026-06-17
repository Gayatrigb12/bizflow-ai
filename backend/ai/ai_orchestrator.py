import json
import logging
import os
from typing import Any, Dict, List, Optional

from backend.ai.groq_provider import GroqProvider
from backend.ai.prompt_builder import build_system_prompt
from backend.ai.tools import TOOL_DEFINITIONS, ToolExecutor, parse_tool_arguments
from backend.services.report_service import ReportService

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 8


class AIOrchestrator:
    def __init__(self, session, provider=None):
        self.session = session
        api_key = os.getenv('GROQ_API_KEY', '')
        self.provider = provider or GroqProvider(api_key=api_key)

    def orchestrate(
        self,
        message: str,
        actor: str = 'AI',
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        system_prompt = build_system_prompt(ReportService(self.session).build_dashboard_state())
        messages: List[Dict[str, Any]] = [{'role': 'system', 'content': system_prompt}]

        for turn in history or []:
            role = turn.get('role')
            content = turn.get('content')
            if role in ('user', 'assistant') and content:
                messages.append({'role': role, 'content': str(content)})

        messages.append({'role': 'user', 'content': message})

        tool_executor = ToolExecutor(self.session, actor=actor)
        reply = ''
        raw_responses: List[Dict[str, Any]] = []

        for iteration in range(MAX_TOOL_ITERATIONS):
            logger.info('Calling AI provider (iteration %s)', iteration + 1)
            raw = self.provider.chat_completion(messages, tools=TOOL_DEFINITIONS)
            raw_responses.append(raw)

            if raw.get('error'):
                return self._error_result(
                    'The AI service is temporarily unavailable. Please try again.',
                    raw=raw,
                    tool_executor=tool_executor,
                )

            choices = raw.get('choices') or []
            if not choices:
                return self._error_result(
                    'The AI service returned an unexpected response. Please try again.',
                    raw=raw,
                    tool_executor=tool_executor,
                )

            assistant_message = choices[0].get('message', {})
            tool_calls = assistant_message.get('tool_calls') or []

            if not tool_calls:
                reply = str(assistant_message.get('content') or '').strip()
                if reply:
                    break
                return self._error_result(
                    'Sorry, I could not generate a response. Please try again.',
                    raw=raw,
                    tool_executor=tool_executor,
                )

            messages.append(assistant_message)

            for tool_call in tool_calls:
                function = tool_call.get('function') or {}
                tool_name = function.get('name', '')
                arguments = parse_tool_arguments(function.get('arguments'))
                logger.info('Executing tool: %s', tool_name)
                result = tool_executor.execute(tool_name, arguments)
                messages.append({
                    'role': 'tool',
                    'tool_call_id': tool_call.get('id'),
                    'content': json.dumps(result, default=str),
                })
        else:
            reply = reply or 'I gathered the data but need another message to finish. Please try again.'

        all_valid = all(item.get('valid', True) for item in tool_executor.validation_results)
        return {
            'reply': reply,
            'actions': tool_executor.executed_writes,
            'validation': tool_executor.validation_results,
            'all_valid': all_valid,
            'actions_executed': True,
            'pending_action_ids': tool_executor.pending_action_ids,
            'approval_required': bool(tool_executor.pending_action_ids),
            'raw': raw_responses[-1] if raw_responses else None,
        }

    @staticmethod
    def _error_result(message: str, raw: Any, tool_executor: ToolExecutor) -> Dict[str, Any]:
        return {
            'reply': message,
            'raw': raw,
            'actions': tool_executor.executed_writes,
            'validation': tool_executor.validation_results,
            'all_valid': False,
            'actions_executed': True,
            'pending_action_ids': tool_executor.pending_action_ids,
            'approval_required': bool(tool_executor.pending_action_ids),
        }
