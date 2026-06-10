from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
import os
import json
import requests
import datetime
import random
import re
import time

load_dotenv()
app = Flask(__name__)
DATA_FILE = 'data/store.json'
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
print(GROQ_API_KEY, "heyyy")
GROQ_URL = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_MODEL = 'llama-3.3-70b-versatile'

DEFAULT_DATA = {
    "inventory": [],
    "orders": [],
    "customers": [],
    "activity": [],
    "order_counter": 1001
}


def load_data():
    os.makedirs('data', exist_ok=True)
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    save_data(DEFAULT_DATA.copy())
    return DEFAULT_DATA.copy()


def save_data(data):
    os.makedirs('data', exist_ok=True)
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        print(f"Error saving data: {e}")


def get_initials(name):
    parts = (name or '').strip().split()
    if not parts:
        return '??'
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return name[:2].upper()


def current_time():
    return datetime.datetime.now().isoformat()


def today_date():
    return datetime.date.today().strftime("%d/%m/%Y")


def activity_time():
    return datetime.datetime.now().strftime("%I:%M %p").lstrip('0')


def format_inr(amount):
    return f"₹{amount:,.2f}".replace('.00', '')


def find_product(inventory, name):
    name_lower = name.strip().lower()
    for p in inventory:
        if p.get('name', '').strip().lower() == name_lower:
            return p
    return None


def find_customer(customers, name):
    name_lower = name.strip().lower()
    for c in customers:
        if c.get('name', '').strip().lower() == name_lower:
            return c
    return None


def generate_sku(name):
    letters = ''.join(c for c in name.upper() if c.isalpha())[:3]
    if len(letters) < 3:
        letters = (letters + 'XXX')[:3]
    return letters + str(random.randint(10, 99))


def log_activity(data, entry_type, text, value=''):
    data.setdefault('activity', [])
    data['activity'].insert(0, {
        "type": entry_type,
        "text": text,
        "value": value,
        "time": activity_time()
    })
    data['activity'] = data['activity'][:50]


def execute_actions(actions, data):
    if not actions:
        return
    for action in actions:
        if not isinstance(action, dict):
            continue
        action_type = action.get('type', '')
        if action_type == 'info':
            continue
        elif action_type == 'add_product':
            _add_product(action, data)
        elif action_type == 'update_stock':
            _update_stock(action, data)
        elif action_type == 'create_order':
            _create_order(action, data)
        elif action_type == 'add_customer':
            _add_customer(action, data)
        elif action_type == 'delete_product':
            _delete_product(action, data)
        elif action_type == 'update_order_status':
            _update_order_status(action, data)


def _add_product(action, data):
    name = (action.get('name') or '').strip()
    if not name:
        return
    existing = find_product(data['inventory'], name)
    qty = float(action.get('qty', 0))
    price = float(action.get('price', 0))
    unit = action.get('unit', 'pcs') or 'pcs'
    if existing:
        existing['qty'] = existing.get('qty', 0) + qty
        if price > 0:
            existing['price'] = price
        if action.get('unit'):
            existing['unit'] = unit
        log_activity(data, 'inventory', f"Updated stock: {name}", f"+{int(qty)} {unit}")
    else:
        product = {
            "id": f"{int(time.time() * 1000)}{random.randint(100, 999)}",
            "name": name,
            "sku": action.get('sku') or generate_sku(name),
            "price": price,
            "qty": qty,
            "unit": unit,
            "low_stock_threshold": 10
        }
        data['inventory'].append(product)
        log_activity(data, 'inventory', f"Added product: {name}", format_inr(price))


def _update_stock(action, data):
    name = (action.get('name') or '').strip()
    product = find_product(data['inventory'], name)
    if not product:
        return
    change = float(action.get('qty_change', 0))
    product['qty'] = max(0, product.get('qty', 0) + change)
    log_activity(data, 'inventory', f"Stock update: {name}", f"{int(change):+d}")


def _create_order(action, data):
    customer_name = (action.get('customer') or 'Walk-in').strip()
    items_in = action.get('items', []) or []
    status = action.get('status', 'paid') or 'paid'
    order_items = []
    total = 0.0

    for item in items_in:
        item_name = (item.get('name') or '').strip()
        qty = float(item.get('qty', 1))
        product = find_product(data['inventory'], item_name)
        price = float(product['price']) if product else 0.0
        subtotal = price * qty
        order_items.append({
            "name": item_name,
            "qty": qty,
            "price": price,
            "subtotal": subtotal
        })
        total += subtotal
        if product:
            product['qty'] = max(0, product.get('qty', 0) - qty)

    order_id = f"INV-{data.get('order_counter', 1001)}"
    data['order_counter'] = data.get('order_counter', 1001) + 1

    order = {
        "id": order_id,
        "customer": customer_name,
        "items": order_items,
        "total": total,
        "status": status,
        "date": today_date(),
        "created_at": current_time()
    }
    data['orders'].insert(0, order)

    customer = find_customer(data['customers'], customer_name)
    if customer:
        customer['orders'] = customer.get('orders', 0) + 1
        customer['total_spent'] = customer.get('total_spent', 0) + total
    else:
        data['customers'].append({
            "id": f"{int(time.time() * 1000)}{random.randint(100, 999)}",
            "name": customer_name,
            "phone": "",
            "email": "",
            "orders": 1,
            "total_spent": total,
            "created_at": current_time()
        })

    log_activity(data, 'order', f"Invoice {order_id} for {customer_name}", format_inr(total))


def _add_customer(action, data):
    name = (action.get('name') or '').strip()
    if not name or find_customer(data['customers'], name):
        return
    data['customers'].append({
        "id": f"{int(time.time() * 1000)}{random.randint(100, 999)}",
        "name": name,
        "phone": action.get('phone', '') or '',
        "email": action.get('email', '') or '',
        "orders": 0,
        "total_spent": 0.0,
        "created_at": current_time()
    })
    log_activity(data, 'customer', f"Added customer: {name}", action.get('phone', '') or '')


def _delete_product(action, data):
    name = (action.get('name') or '').strip()
    data['inventory'] = [
        p for p in data['inventory']
        if p.get('name', '').strip().lower() != name.lower()
    ]
    log_activity(data, 'inventory', f"Removed product: {name}", '')


def _update_order_status(action, data):
    order_id = action.get('id', '')
    status = action.get('status', '')
    for order in data['orders']:
        if order.get('id') == order_id:
            order['status'] = status
            log_activity(data, 'order', f"Order {order_id} → {status}", '')
            break


def parse_groq_json(content):
    if not content:
        return None
    text = content.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```\s*$', '', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def build_system_prompt(data):
    return f"""You are BizFlow AI, a smart ERP assistant for small Indian businesses.
You help manage inventory, orders, and customers via natural language.

## Current Business State:
INVENTORY: {json.dumps(data['inventory'])}
ORDERS (last 10): {json.dumps(data['orders'][:10])}
CUSTOMERS: {json.dumps(data['customers'])}

## Your Response Format:
You MUST respond with ONLY a valid JSON object. No markdown. No explanation outside JSON.

{{
  "reply": "Short friendly 1-2 sentence response to the user in English",
  "actions": [
    // Array of action objects to execute. Can be empty [].
  ]
}}

## Available Action Types:

1. Add or update a product:
{{ "type": "add_product", "name": "Rice", "sku": "RIC001", "price": 60, "qty": 100, "unit": "kg" }}

2. Update stock quantity:
{{ "type": "update_stock", "name": "Rice", "qty_change": -5 }}

3. Create an invoice/order:
{{ "type": "create_order", "customer": "Rahul", "items": [{{"name": "Rice", "qty": 3}}], "status": "paid" }}

4. Add a customer:
{{ "type": "add_customer", "name": "Priya", "phone": "9876543210", "email": "" }}

5. Delete a product:
{{ "type": "delete_product", "name": "Rice" }}

6. Update order status:
{{ "type": "update_order_status", "id": "INV-1001", "status": "cancelled" }}

7. Just reply (no state change):
{{ "type": "info" }}

## Business Rules:
- All prices are in Indian Rupees (₹)
- When creating an order, look up product prices from INVENTORY
- If a product in an order is not found in inventory, still create the order but set price to 0 and mention it
- Automatically deduct stock when creating orders
- Auto-add customer if they don't exist when creating an order
- Low stock threshold is 10 units
- Be conversational, friendly, and helpful
- If asked for reports (revenue, top products, etc.), compute from the state and reply in the 'reply' field
- Use exact product names from INVENTORY when creating orders
"""


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/state')
def api_state():
    return jsonify(load_data())


@app.route('/api/chat', methods=['POST'])
def api_chat():
    body = request.get_json(silent=True) or {}
    message = (body.get('message') or '').strip()
    if not message:
        return jsonify({"error": "Message is required"}), 400

    if not GROQ_API_KEY or GROQ_API_KEY == 'gsk_your_key_here':
        return jsonify({
            "error": "Groq API key not configured",
            "details": "Set GROQ_API_KEY in .env"
        }), 500

    data = load_data()
    system_prompt = build_system_prompt(data)

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ],
        "temperature": 0.1,
        "max_tokens": 1000
    }
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(GROQ_URL, json=payload, headers=headers, timeout=60)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Groq API error", "details": str(e)}), 502

    if response.status_code != 200:
        return jsonify({
            "error": "Groq API error",
            "details": response.text
        }), response.status_code

    result = response.json()
    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
    parsed = parse_groq_json(content)

    if not parsed:
        return jsonify({
            "reply": "I had trouble understanding that. Could you rephrase?",
            "actions": [],
            "state": data
        })

    reply = parsed.get('reply', 'Done.')
    actions = parsed.get('actions', [])
    if not isinstance(actions, list):
        actions = []

    execute_actions(actions, data)
    save_data(data)

    return jsonify({
        "reply": reply,
        "actions": actions,
        "state": data
    })


@app.route('/api/reset', methods=['POST'])
def api_reset():
    save_data(DEFAULT_DATA.copy())
    return jsonify({"ok": True})


@app.route('/api/inventory')
def api_inventory():
    data = load_data()
    return jsonify(data.get('inventory', []))


@app.route('/api/orders')
def api_orders():
    data = load_data()
    return jsonify(data.get('orders', []))


@app.route('/api/customers')
def api_customers():
    data = load_data()
    return jsonify(data.get('customers', []))


def mask_api_key(key):
    if not key or len(key) < 8:
        return '(not set)'
    return f"{key[:4]}...{key[-4:]}"


if __name__ == '__main__':
    key_display = mask_api_key(GROQ_API_KEY)
    if not GROQ_API_KEY or GROQ_API_KEY == 'gsk_your_key_here':
        print("WARNING: GROQ_API_KEY not set. Add your key to .env")
    else:
        print(f"Groq API key loaded: {key_display}")
    print(f"Model: {GROQ_MODEL}")
    print("Starting BizFlow AI at http://localhost:5000")
    app.run(debug=True, port=5000)

# TODO: Add PDF invoice generation using reportlab
# TODO: Add WhatsApp notification via Twilio free tier
# TODO: Add date filtering on orders (/api/orders?from=&to=)
# TODO: Add product categories
# TODO: Add SQLite instead of JSON file for larger data
# TODO: Add login with Flask-Login for multi-user
# TODO: Add CSV export for inventory and orders
# TODO: Add barcode/QR code generation for products
