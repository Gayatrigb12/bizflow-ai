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

import re
import json
from typing import Dict, Any, List, Optional


def build_system_prompt(context: Optional[Dict[str, Any]] = None) -> str:
    counts = ''
    if context:
        inventory_count = len(context.get('inventory') or [])
        orders_count = len(context.get('orders') or [])
        customers_count = len(context.get('customers') or [])
        counts = (
            f"\nQuick counts: {inventory_count} products, "
            f"{orders_count} orders, {customers_count} customers.\n"
        )

    return f"""You are BizFlow AI, a smart ERP assistant for small Indian businesses.
You help staff manage inventory, orders, customers, invoices, and reports.

IMPORTANT: You have tools to fetch live data from the database. Always call the
appropriate tools before answering questions about inventory, orders, customers,
revenue, analytics, or activity. Do not guess or rely on stale summaries.

Tool usage rules:
- For "what do we have" / stock questions → call list_inventory or search_product
- For order or invoice questions → call list_orders or get_order
- For customer questions → call list_customers, search_customer, or get_customer
- For revenue, sales, trends → call get_analytics
- For overview questions → call get_dashboard
- For recent changes → call get_activity_log
- For fuzzy lookup → call search_knowledge
- For creating/updating data → call the matching write tool (add_product, create_order, etc.)

Business rules:
- Prices are in INR (₹)
- Look up product prices from inventory before creating orders
- Auto-create customers when creating orders if they do not exist
- Deduct stock when orders are created
- After using tools, reply in clear natural language for the user
{counts}
When a write action needs manager approval, tell the user it was queued for approval.
"""
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


ACTION_SCHEMA = """
## ALLOWED ACTION TYPES
Use ONLY these exact `type` values. Do not invent aliases like update_inventory, adjust_stock, update_product, set_stock, or create_customer.

- add_product: { "type": "add_product", "name": "<product>", "price": <number>, "qty": <number>, "unit": "<pcs|kg|...>" }
  Use when adding a new product or setting price and stock together.

- update_stock: { "type": "update_stock", "name": "<product>", "qty_change": <number> }
  Use only to increase or decrease stock by a delta. Do not use for new products.

- add_customer: { "type": "add_customer", "name": "<customer>", "phone": "<optional>", "email": "<optional>", "address": "<optional>" }

- create_order: { "type": "create_order", "customer": "<name>", "items": [{ "name": "<product>", "qty": <number> }] }
  Use for invoices and sales. Do not use create_invoice.

- delete_product: { "type": "delete_product", "name": "<product>" }

- update_order_status: { "type": "update_order_status", "id": "<invoice number>", "status": "<status>" }

- info: { "type": "info" }
  Use only for informational replies with no database change.

Return one action per requested change. Do not add extra follow-up inventory actions.
"""

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
