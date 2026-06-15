# Setup & Development

## Prerequisites

- **Python 3.10+**
- **Free Groq API key** — https://console.groq.com (no credit card for free tier)

## Installation

```powershell
cd "C:\AI Usecase\AI USE CASE\bizflow-ai"

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

### Dependencies (`requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| flask | 3.0.2 | Web server and routing |
| python-dotenv | 1.0.1 | Load `.env` variables |
| requests | 2.31.0 | HTTP calls to Groq |

## Configuration

Create or edit **`.env`** in the `bizflow-ai` folder:

```
GROQ_API_KEY=gsk_your_actual_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bizflowdb
JWT_SECRET_KEY=replace-with-a-secure-key
```

Never commit `.env` to version control.

### Database setup

1. Install PostgreSQL 16+ with the pgvector extension.
2. Create the database: `bizflowdb`.
3. Run migrations: `alembic -c backend/alembic.ini upgrade head`
4. Verify and seed data: `python -m backend.scripts.verify_db --fix`

This imports legacy `data/store.json` if tables are empty and creates an admin user (`admin` / `changeme`) when needed.

On startup, the server prints a **masked** key (`gsk_...last4`) or a warning if missing.

## Running

```powershell
python app.py
```

Open **http://localhost:5000** in your browser.

Debug mode is enabled (`debug=True`) for development — auto-reloads on code changes.

---

## Folder structure

```
bizflow-ai/
├── app.py                 # Flask app, Groq, business logic
├── requirements.txt
├── .env                   # Secrets (local only)
├── README.md              # Quick start
├── docs/                  # Full documentation
│   ├── README.md
│   ├── 01-project-overview.md
│   ├── 02-architecture.md
│   ├── 03-api-reference.md
│   ├── 04-data-schema.md
│   ├── 05-user-guide.md
│   └── 06-setup-and-development.md
├── data/
│   └── store.json         # Auto-created persistence
├── static/
│   ├── style.css          # UI theme and layout
│   └── app.js             # Frontend logic
└── templates/
    └── index.html         # Page shell
```

---

## Key source files

### `app.py`

| Function / area | Purpose |
|-----------------|---------|
| `load_data` / `save_data` | JSON file I/O |
| `execute_actions` | Dispatches action types |
| `_add_product`, `_create_order`, … | Per-action business rules |
| `build_system_prompt` | Groq system message with live state |
| `parse_groq_json` | Parse AI output safely |
| Routes | `/`, `/api/*` |

### `static/app.js`

| Function | Purpose |
|----------|---------|
| `init` | Load state on page open |
| `showPanel` | Sidebar navigation |
| `sendMessage` | Chat → `/api/chat` |
| `executeState` | Sync UI from server state |
| `renderInventory`, `renderOrders`, `renderCustomers` | Panel content |
| `updateDashboard`, `updateAllBadges` | Stats |

### `templates/index.html`

Defines all panel DOM ids used by JavaScript. Do not rename ids without updating `app.js`.

---

## Extending the application

### Add a new AI action type

1. Document the action in `build_system_prompt()` (system prompt in `app.py`).
2. Add a branch in `execute_actions()` and implement `_your_action()`.
3. Optionally handle display in `appendAiMsg()` in `app.js`.

### Add a new API route

1. Add `@app.route(...)` in `app.py`.
2. Use `load_data()` / `save_data()` as needed.
3. Call from `app.js` if the UI should use it.

### Change the Groq model

Edit `GROQ_MODEL` in `app.py` and update the badge text in `templates/index.html`.

Current model: `llama-3.3-70b-versatile` (replaces deprecated `llama3-70b-8192`).

---

## Planned enhancements (from code TODOs)

- PDF invoice generation (reportlab)
- WhatsApp notifications (Twilio)
- Order date filtering (`/api/orders?from=&to=`)
- Product categories
- SQLite database
- Flask-Login authentication
- CSV export
- Barcode / QR codes for products

---

## Development tips

- Inspect live data: open `data/store.json` in an editor while the server is stopped, or use `GET /api/state`.
- Test business logic without Groq:

  ```python
  from app import load_data, execute_actions, save_data
  data = load_data()
  execute_actions([{"type": "add_product", "name": "Test", "price": 10, "qty": 5, "unit": "pcs"}], data)
  save_data(data)
  ```

- Reset data: `POST /api/reset` or delete `data/store.json`.

---

## Production notes

This MVP uses Flask’s built-in server and has **no authentication**. For production you would need:

- A production WSGI server (e.g. Gunicorn)
- HTTPS
- Secure secret management
- User accounts and data isolation
- Database with backups

For local demos and learning, the current setup is sufficient.
