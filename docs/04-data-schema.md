# Data Schema

All persistent data lives in **`data/store.json`**. The file is created automatically on first run if it does not exist.

## Root document

```json
{
  "inventory": [],
  "orders": [],
  "customers": [],
  "activity": [],
  "order_counter": 1001
}
```

| Field | Type | Description |
|-------|------|-------------|
| `inventory` | array | Product catalog |
| `orders` | array | Sales / invoices (newest inserted at index 0) |
| `customers` | array | Customer directory |
| `activity` | array | Recent audit feed (max 50 entries kept) |
| `order_counter` | number | Next invoice number suffix (e.g. 1001 → `INV-1001`) |

---

## Inventory item

```json
{
  "id": "1780555294082456",
  "name": "Rice",
  "sku": "RIC33",
  "price": 60.0,
  "qty": 100,
  "unit": "kg",
  "low_stock_threshold": 10
}
```

| Field | Description |
|-------|-------------|
| `id` | Unique string (timestamp + random digits) |
| `name` | Display name; matched case-insensitively for orders |
| `sku` | Stock keeping unit; auto-generated if omitted (3 letters + 2 digits) |
| `price` | Unit price in ₹ |
| `qty` | Current quantity in stock |
| `unit` | e.g. `kg`, `litre`, `pcs` |
| `low_stock_threshold` | Default `10`; UI shows red border when `qty <= threshold` |

**Merge rule:** `add_product` with an existing name (case-insensitive) **adds** to `qty` instead of creating a duplicate row.

---

## Order (invoice)

```json
{
  "id": "INV-1001",
  "customer": "Rahul",
  "items": [
    {
      "name": "Rice",
      "qty": 5,
      "price": 60.0,
      "subtotal": 300.0
    }
  ],
  "total": 300.0,
  "status": "paid",
  "date": "04/06/2026",
  "created_at": "2026-06-04T12:11:34.082327"
}
```

| Field | Description |
|-------|-------------|
| `id` | Format `INV-{order_counter}` at creation time |
| `customer` | Customer name string |
| `items` | Line items with computed `subtotal` |
| `total` | Sum of line subtotals |
| `status` | `paid`, `pending`, or `cancelled` |
| `date` | Display date `DD/MM/YYYY` |
| `created_at` | ISO 8601 timestamp |

**Order creation rules:**

- Prices come from inventory lookup by product name.
- Missing products get `price: 0` but order still created.
- Stock is deducted for each matched product.
- Customer is auto-created if name not found.

---

## Customer

```json
{
  "id": "1780555294082789",
  "name": "Rahul",
  "phone": "9876543210",
  "email": "",
  "orders": 2,
  "total_spent": 840.0,
  "created_at": "2026-06-04T10:00:00"
}
```

| Field | Description |
|-------|-------------|
| `orders` | Count of orders linked to this customer |
| `total_spent` | Cumulative ₹ from orders (updated on `create_order`) |

Duplicate customers by name (case-insensitive) are not added twice via `add_customer`.

---

## Activity log entry

```json
{
  "type": "order",
  "text": "Invoice INV-1001 for Rahul",
  "value": "₹660",
  "time": "10:30 AM"
}
```

| `type` | Typical use |
|--------|-------------|
| `inventory` | Product add, stock change, delete |
| `order` | Invoice created or status updated |
| `customer` | New customer added |

New entries are inserted at the **beginning** of the array. Dashboard shows the latest 8.

---

## AI action types

Actions appear in the `actions` array from Groq and are processed by `execute_actions()` in `app.py`.

### 1. `add_product`

```json
{
  "type": "add_product",
  "name": "Rice",
  "sku": "RIC001",
  "price": 60,
  "qty": 100,
  "unit": "kg"
}
```

### 2. `update_stock`

```json
{
  "type": "update_stock",
  "name": "Rice",
  "qty_change": -5
}
```

`qty_change` can be negative. Quantity is clamped to minimum 0.

### 3. `create_order`

```json
{
  "type": "create_order",
  "customer": "Rahul",
  "items": [{ "name": "Rice", "qty": 3 }],
  "status": "paid"
}
```

Use **exact inventory product names** for reliable pricing and stock updates.

### 4. `add_customer`

```json
{
  "type": "add_customer",
  "name": "Priya",
  "phone": "9876543210",
  "email": ""
}
```

### 5. `delete_product`

```json
{ "type": "delete_product", "name": "Rice" }
```

### 6. `update_order_status`

```json
{
  "type": "update_order_status",
  "id": "INV-1001",
  "status": "cancelled"
}
```

### 7. `info`

No state change. Used when the AI only answers a question (revenue, low stock list, etc.) in the `reply` field.

---

## AI response envelope (from Groq)

The model must return JSON in this shape (parsed by backend):

```json
{
  "reply": "Short friendly message to the user",
  "actions": []
}
```

`actions` may contain zero or more action objects. Multiple actions in one response are executed in order.
