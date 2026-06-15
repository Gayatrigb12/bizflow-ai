# API Reference

Base URL when running locally: **`http://localhost:5000`**

All JSON APIs return `Content-Type: application/json` unless noted.

---

## `GET /`

Serves the main single-page application.

**Response:** HTML (`templates/index.html`)

---

## `GET /api/state`

Returns the full business state from `data/store.json`. Used on page load to hydrate the UI.

**Response 200:**

```json
{
  "inventory": [],
  "orders": [],
  "customers": [],
  "activity": [],
  "order_counter": 1001
}
```

---

## `POST /api/chat`

Sends a user message to Groq, executes returned actions, saves data, and returns updated state.

**Request body:**

```json
{
  "message": "Add product Rice at ₹60 per kg, quantity 100"
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `message` | Yes | Non-empty string after trim |
| `session_id` | No | Client chat session id for history grouping |

**Response 200 (success):**

```json
{
  "reply": "Rice has been added to your inventory.",
  "actions": [
    { "type": "add_product", "name": "Rice", "price": 60, "qty": 100, "unit": "kg" }
  ],
  "state": { "...full store object..." }
}
```

**Response 400:**

```json
{ "error": true, "message": "Message is required", "code": 400 }
```

**Response 500** (API key missing or placeholder):

```json
{
  "error": true,
  "message": "Groq API key not configured",
  "code": 500
}
```

---

## `GET /api/chat/history`

Returns persisted chat messages for the authenticated user session.

**Query parameters:**

| Param | Default | Description |
|-------|---------|-------------|
| `limit` | `30` | Max rows (capped at 100) |
| `session_id` | — | Optional filter by client session id |

**Response 200:**

```json
[
  {
    "id": 1,
    "user_prompt": "Add product Rice",
    "ai_response": "Rice has been added.",
    "metadata": { "actions": [] },
    "session_id": "session-123",
    "created_at": "2026-06-15T10:00:00+00:00"
  }
]
```

**Response 502** (network failure to Groq):

```json
{
  "error": "Groq API error",
  "details": "..."
}
```

**Groq configuration (server-side):**

| Setting | Value |
|---------|-------|
| URL | `https://api.groq.com/openai/v1/chat/completions` |
| Model | `llama-3.3-70b-versatile` |
| Temperature | `0.1` |
| Max tokens | `1000` |

---

## `POST /api/reset`

Resets `data/store.json` to empty default state (clears inventory, orders, customers, activity; `order_counter` = 1001).

**Response 200:**

```json
{ "ok": true }
```

---

## `GET /api/inventory`

Returns the inventory array only.

**Response 200:** `Product[]` — see [Data Schema](04-data-schema.md)

---

## `GET /api/orders`

Returns the orders array only (newest first in storage).

**Response 200:** `Order[]`

---

## `GET /api/customers`

Returns the customers array only.

**Response 200:** `Customer[]`

---

## Static assets

| Path | File |
|------|------|
| `/static/style.css` | Styles |
| `/static/app.js` | Frontend logic |

Flask serves these from the `static/` folder automatically.

---

## Example: chat with curl

```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"List all customers\"}"
```

PowerShell:

```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/chat" -Method POST `
  -ContentType "application/json" `
  -Body '{"message":"What is my total revenue?"}' | Select-Object -ExpandProperty Content
```
