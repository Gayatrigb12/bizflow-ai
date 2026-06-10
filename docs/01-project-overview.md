# Project Overview

## What is BizFlow AI?

**BizFlow AI** is an AI-powered micro-ERP (Enterprise Resource Planning) web application for small businesses. Instead of filling long forms, the owner types **natural language commands** in a chat interface to manage:

- **Inventory** — products, stock, prices, units
- **Orders / invoices** — sales with automatic stock deduction
- **Customers** — contact details and purchase history
- **Reports** — revenue, low stock, and summaries (via AI replies)

The app targets small Indian businesses such as kirana stores, freelancers, and local traders. All monetary values use **Indian Rupees (₹)**.

## Key idea

```
User types: "Create invoice for Rahul for 5 kg Rice"
     ↓
Groq LLM understands intent and returns structured JSON actions
     ↓
Flask executes actions (deduct stock, create order, update customer)
     ↓
UI updates instantly from returned state
```

The AI does not touch the database directly. It only suggests **actions**; the Python backend applies them with fixed business rules. That keeps data consistent even if the model makes mistakes.

## Features

| Feature | Description |
|---------|-------------|
| Conversational ERP | Natural language chat powered by Groq |
| Dashboard | Orders count, paid revenue, product count, customers, activity feed |
| Inventory grid | Product cards with low-stock visual warning (red left border) |
| Orders list | Invoice IDs, customer, status badges (paid / pending / cancelled) |
| Customers list | Avatars, phone, order count, total spent |
| Suggestion chips | One-click example commands in chat |
| Persistence | All data saved to `data/store.json` on disk |
| No database (MVP) | JSON file storage — simple to run and inspect |

## Technology stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.10+, Flask 3.0.2 |
| Frontend | Single HTML page, vanilla CSS and JavaScript (no React, no npm) |
| AI | Groq API — model `llama-3.3-70b-versatile` (free tier) |
| Config | `python-dotenv` for `.env` |
| HTTP client | `requests` for Groq API calls |
| Storage | JSON file (`data/store.json`) |
| Fonts | Google Fonts — Courier Prime, DM Sans |
| Icons | Tabler Icons (CDN) |

## What BizFlow AI is not (MVP scope)

- No user login or multi-tenant support
- No PDF invoices (planned TODO)
- No WhatsApp notifications (planned TODO)
- No SQL database
- No mobile app — browser only

See `app.py` bottom comments for the full roadmap of planned enhancements.

## Documentation map

- **How it works internally** → [Architecture](02-architecture.md)
- **HTTP APIs** → [API Reference](03-api-reference.md)
- **JSON structures** → [Data Schema](04-data-schema.md)
- **How to use the UI** → [User Guide](05-user-guide.md)
- **Install and extend** → [Setup & Development](06-setup-and-development.md)
