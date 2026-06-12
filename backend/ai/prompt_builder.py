# from typing import Dict, Any
# import json


# def build_system_prompt(context: Dict[str, Any]) -> str:
#     # compact representation: include counts and short lists
#     inventory = context.get('inventory', [])
#     orders = context.get('orders', [])[:10]
#     customers = context.get('customers', [])

#     retrieval = context.get('retrieval_snippets', [])
#     retrieval_text = ''
#     if retrieval:
#         lines = []
#         for item in retrieval:
#             snippet = item.get('snippet') or item.get('metadata') or {}
#             snippet_text = snippet if isinstance(snippet, str) else json.dumps(snippet)
#             lines.append(f"- [{item.get('object_type')}:{item.get('object_id')}] {snippet_text}")
#         retrieval_text = 'RETRIEVAL_HINTS:\n' + '\n'.join(lines) + '\n\n'

#     return f"""You are BizFlow AI, a smart ERP assistant for small businesses.
# Provide JSON-only responses with a `reply` and `actions` array.

# INVENTORY_SUMMARY: {json.dumps([{'name': p.get('name'), 'qty': p.get('quantity', p.get('qty', 0))} for p in inventory[:50]])}
# ORDERS_SAMPLE: {json.dumps(orders)}
# CUSTOMERS_SAMPLE: {json.dumps([{'name': c.get('name')} for c in customers[:50]])}

# {retrieval_text}Business rules: Prices in INR; look up product prices from inventory; auto-create customers when creating orders; deduct stock on order creation.
# """


# def extract_json_from_model(content: str):
#     # naive extractor, remove code fences
#     import re, json
#     if not content:
#         return None
#     s = content.strip()
#     s = re.sub(r'^```(?:json)?\s*', '', s, flags=re.IGNORECASE)
#     s = re.sub(r'\s*```\s*$', '', s)
#     try:
#         return json.loads(s)
#     except Exception:
#         m = re.search(r'\{[\s\S]*\}', s)
#         if m:
#             try:
#                 return json.loads(m.group())
#             except Exception:
#                 return None
#     return None



# ─────────────────────────────────────────────────────────────────────────────
# PATCH for your existing prompt_builder.py
# Replace your extract_json_from_model function with this one.
# ─────────────────────────────────────────────────────────────────────────────

import re
import json
from typing import Dict, Any

def build_system_prompt(context: Dict[str, Any]) -> str:

    inventory = context.get("inventory", [])
    orders = context.get("orders", [])[:10]
    customers = context.get("customers", [])

    retrieval = context.get("retrieval_snippets", [])

    retrieval_text = ""

    if retrieval:
        lines = []

        for item in retrieval:
            snippet = item.get("snippet") or item.get("metadata") or {}

            if isinstance(snippet, str):
                snippet_text = snippet
            else:
                snippet_text = json.dumps(snippet)

            lines.append(
                f"- [{item.get('object_type')}:{item.get('object_id')}] {snippet_text}"
            )

        retrieval_text = (
            "RETRIEVAL_HINTS:\n"
            + "\n".join(lines)
            + "\n\n"
        )

    prompt = f"""
You are BizFlow AI, a smart ERP assistant.

INVENTORY_SUMMARY:
{json.dumps([
    {
        "name": p.get("name"),
        "qty": p.get("quantity", p.get("qty", 0))
    }
    for p in inventory[:50]
])}

ORDERS_SAMPLE:
{json.dumps(orders)}

CUSTOMERS_SAMPLE:
{json.dumps([
    {
        "name": c.get("name")
    }
    for c in customers[:50]
])}

{retrieval_text}

Business Rules:
- Prices are in INR
- Use inventory prices
- Auto-create customers if required
- Deduct stock when creating orders
"""

    return prompt + JSON_ENFORCEMENT
def extract_json_from_model(content: str) -> Dict[str, Any] | None:
    """
    Robust JSON extractor — replace your existing one with this.
    """
    if not content:
        return None

    # 1. Try direct parse
    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown fences
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", content, re.IGNORECASE)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3. Bracket-counting scan (finds deepest complete {...} block)
    best = None
    for start in [i for i, c in enumerate(content) if c == '{']:
        depth = 0
        for end, ch in enumerate(content[start:], start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    try:
                        best = json.loads(content[start:end + 1])
                    except json.JSONDecodeError:
                        pass
                    break
    if best:
        return best

    return None


# ─────────────────────────────────────────────────────────────────────────────
# Also add this JSON enforcement block to the END of your build_system_prompt()
# function, so the model always returns pure JSON.
# ─────────────────────────────────────────────────────────────────────────────

JSON_ENFORCEMENT = """
## OUTPUT FORMAT — MANDATORY
Respond with ONLY a raw JSON object. No markdown. No code fences. No text outside JSON.

{
  "reply": "<message to show the user>",
  "actions": [
    {
      "type": "<action_type>",
      ... other fields ...
    }
  ]
}

If no actions are needed, return an empty list: "actions": []
Start your response with { and end with }. Nothing before or after.
"""

# In your build_system_prompt function, append JSON_ENFORCEMENT to the prompt string:
# def build_system_prompt(context):
#     prompt = ... your existing code ...
#     return prompt + JSON_ENFORCEMENT