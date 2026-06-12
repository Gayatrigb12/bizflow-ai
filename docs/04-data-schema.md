# Data Schema

Persistent data is stored in **PostgreSQL** via SQLAlchemy models. Legacy JSON in `data/store.json` can be imported with `python -m backend.scripts.import_legacy_json`.

## Database tables

| Table | Description |
|-------|-------------|
| `products` | Product catalog (inventory) |
| `customers` | Customer directory |
| `orders` | Sales / invoices |
| `order_items` | Line items per order |
| `activity_logs` | Audit feed |
| `users` | Authentication accounts |
| `knowledge_embeddings` | RAG vector index (pgvector) |
| `pending_actions` | AI actions awaiting approval |

Configure the database with `DATABASE_URL` in `.env`:

```
DATABASE_URL=postgresql://user:password@localhost:5432/bizflowdb
```

Run migrations:

```bash
alembic -c backend/alembic.ini upgrade head
```

Verify and repair the database:

```bash
python -m backend.scripts.verify_db --fix
```

## Product (`products`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Primary key |
| `sku` | string | Unique SKU |
| `name` | string | Product name |
| `description` | text | Optional description |
| `unit` | string | Unit of measure |
| `price` | float | Unit price |
| `quantity` | float | Stock on hand |
| `low_stock_threshold` | float | Alert threshold |
| `created_at` / `updated_at` | datetime | Timestamps |

## Customer (`customers`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Primary key |
| `name` | string | Customer name |
| `phone` | string | Phone number |
| `email` | string | Email address |
| `address` | text | Address |
| `total_spent` | float | Lifetime spend |
| `order_count` | integer | Number of orders |
| `created_at` / `updated_at` | datetime | Timestamps |

## Order (`orders` + `order_items`)

| Field | Type | Description |
|-------|------|-------------|
| `invoice_number` | string | Unique invoice ID (e.g. INV-1001) |
| `customer_id` | integer | FK to customers |
| `subtotal` / `tax` / `total` | float | Amounts |
| `status` | string | draft, paid, cancelled |
| `payment_status` | string | pending, paid |
| `items` | relation | Order line items |

## AI action types

The AI assistant returns structured JSON actions validated before execution:

- `add_product`, `update_product`, `delete_product`
- `add_customer`
- `create_order`, `update_order_status`
- `adjust_stock`

High-impact actions may be queued in `pending_actions` for manager approval.
