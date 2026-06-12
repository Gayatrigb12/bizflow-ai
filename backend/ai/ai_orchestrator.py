import os
import re
import json
import logging
from typing import Dict, Any, List

from backend.ai.groq_provider import GroqProvider
from backend.ai.prompt_builder import build_system_prompt
from backend.ai.context_builder import ContextBuilder
from backend.ai.action_validator import ActionValidator

logger = logging.getLogger(__name__)


def _extract_json(content: str) -> Dict[str, Any] | None:

    print("\n================ JSON PARSE START ================")
    print(content)
    print("==================================================\n")

    if not content or not content.strip():
        print("EMPTY CONTENT FROM MODEL")
        return None

    strategies = []

    strategies.append(("direct", content.strip()))

    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", content, re.IGNORECASE)
    if m:
        strategies.append(("fence", m.group(1).strip()))

    for i, c in enumerate(content):
        if c == '{':
            depth = 0
            for j, ch in enumerate(content[i:], i):
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        strategies.append(("brace", content[i:j+1]))
                        break

    for name, candidate in strategies:
        try:
            result = json.loads(candidate)
            print(f"[JSON PARSED via {name}]")
            return result
        except Exception:
            try:
                fixed = re.sub(r',\s*([}\]])', r'\1', candidate)
                result = json.loads(fixed)
                print(f"[JSON PARSED after fix via {name}]")
                return result
            except Exception:
                continue

    print("\n❌ JSON PARSE FAILED ❌")
    print(content)
    return None


class AIOrchestrator:

    def __init__(self, session, provider=None):
        self.session = session
        api_key = os.getenv('GROQ_API_KEY', '')
        self.provider = provider or GroqProvider(api_key=api_key)
        self.context_builder = ContextBuilder(session)
        self.validator = None

    def orchestrate(self, message: str) -> Dict[str, Any]:

        print("\n================ ORCHESTRATOR START ================")
        print("INPUT:", message)

        context = self.context_builder.build(message)

        print("\n[CONTEXT]")
        print(json.dumps(context, indent=2, default=str))

        base_prompt = build_system_prompt(context)

        prompt = base_prompt + """

STRICT RULE:
Return ONLY JSON.
NO explanation.
NO markdown.
ONLY JSON.
"""

        print("\n[PROMPT GENERATED]")
        print(prompt[:1500])

        print("\n================ CALLING GROQ ================")

        raw = self.provider.generate_response(prompt, message)

        print("\n[RAW GROQ RESPONSE]")
        print(json.dumps(raw, indent=2, default=str))

        choices = raw.get('choices') or []

        if not choices:
            print("❌ NO CHOICES FROM GROQ")
            return {
                'reply': 'The AI service returned an unexpected response. Please try again.',
                'raw': raw,
                'actions': [],
                'validation': [],
                'all_valid': False,
            }

        content = choices[0].get('message', {}).get('content', '')

        print("\n[MODEL CONTENT]")
        print(content)

        parsed = _extract_json(content)

        if parsed is None:
            print("\n❌ PARSING FAILED")
            return {
                'reply': 'Sorry, I could not understand the AI response.',
                'raw': raw,
                'raw_content': content,
                'actions': [],
                'validation': [],
                'all_valid': False,
            }

        from backend.services.inventory_service import InventoryService
        inventory_service = InventoryService(self.session)
        self.validator = ActionValidator(self.session, inventory_service)

        actions = parsed.get('actions') if isinstance(parsed.get('actions'), list) else []

        validation_results = []
        all_valid = True

        for act in actions:
            res = self.validator.validate(act)
            validation_results.append({
                'action': act,
                'valid': res.valid,
                'errors': res.errors,
                'requires_approval': res.requires_approval,
            })
            if not res.valid:
                all_valid = False

        print("\n[VALIDATION RESULT]")
        print(validation_results)

        return {
            'reply': parsed.get('reply', ''),
            'raw': raw,
            'actions': actions,
            'validation': validation_results,
            'all_valid': all_valid,
        }