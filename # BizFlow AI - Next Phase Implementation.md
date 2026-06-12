# BizFlow AI - Next Phase Implementation Prompt (PostgreSQL + pgvector)

## Role

You are a Senior Software Architect, AI Engineer, and Full-Stack Developer.

You are working on an existing project called **BizFlow AI**, an AI-powered Micro ERP platform for small businesses.

Current Stack:
- Frontend: HTML, CSS, Vanilla JavaScript
- Backend: Python Flask
- AI: Groq LLM
- Storage: JSON (`data/store.json`)

Your task is to transform the current MVP into a production-ready architecture using **PostgreSQL** and **pgvector** while keeping the current functionality operational.

---

# Business Goal

BizFlow AI should become a scalable AI-powered ERP platform that supports:

- Inventory Management
- Order & Invoice Management
- Customer Management
- Analytics & Reporting
- AI-powered Business Assistant
- Retrieval-Augmented Generation (RAG)
- Future Multi-Tenant Support

---

# Core Technology Decisions

## Database

Replace JSON storage completely.

Use:

- PostgreSQL 16+
- SQLAlchemy ORM
- Alembic for migrations

## Vector Database

Use:

- pgvector extension inside PostgreSQL

Do NOT use:
- ChromaDB
- Pinecone
- Weaviate
- FAISS

All vector embeddings must be stored directly inside PostgreSQL using pgvector.

---

# Target Project Structure

```text
backend/
│
├── app.py
│
├── routes/
│   ├── chat_routes.py
│   ├── inventory_routes.py
│   ├── order_routes.py
│   ├── customer_routes.py
│   ├── report_routes.py
│   └── auth_routes.py
│
├── services/
│   ├── inventory_service.py
│   ├── order_service.py
│   ├── customer_service.py
│   ├── report_service.py
│   ├── analytics_service.py
│   └── notification_service.py
│
├── ai/
│   ├── provider_interface.py
│   ├── groq_provider.py
│   ├── prompt_builder.py
│   ├── action_validator.py
│   └── rag_service.py
│
├── storage/
│   ├── database.py
│   ├── models.py
│   ├── repositories/
│   └── migrations/
│
├── embeddings/
│   ├── embedding_service.py
│   ├── vector_store.py
│   └── retriever.py
│
├── auth/
│   ├── jwt_handler.py
│   ├── permissions.py
│   └── middleware.py
│
├── tests/
│
└── requirements.txt
```

---

# Milestone 1: Database Migration

## Objective

Move from JSON persistence to PostgreSQL.

### Create SQLAlchemy Models

#### Product

Fields:

- id
- sku
- name
- description
- unit
- price
- quantity
- low_stock_threshold
- created_at
- updated_at

---

#### Customer

Fields:

- id
- name
- phone
- email
- address
- total_spent
- order_count
- created_at
- updated_at

---

#### Order

Fields:

- id
- invoice_number
- customer_id
- subtotal
- tax
- total
- status
- payment_status
- created_at
- updated_at

---

#### OrderItem

Fields:

- id
- order_id
- product_id
- quantity
- unit_price
- line_total

---

#### ActivityLog

Fields:

- id
- action_type
- description
- actor
- created_at

---

#### User

Fields:

- id
- username
- email
- password_hash
- role
- created_at

---

# PostgreSQL Requirements

Generate:

- SQLAlchemy models
- Alembic migrations
- Repository layer
- Database initialization
- Connection pooling
- Environment-based configuration

Use:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/bizflow
```

---

# Milestone 2: AI Orchestration Layer

Create an AI abstraction layer.

## Interface

```python
class AIProvider:
    def generate_response(self):
        pass
```

Implement:

- GroqProvider
- Future OpenAIProvider
- Future AzureProvider

---

## Prompt Management

Create:

- PromptBuilder
- SystemPromptManager
- ContextBuilder

The AI must never directly modify the database.

Workflow:

User Query
→ Prompt Builder
→ AI Provider
→ Structured JSON Actions
→ Validation Layer
→ Service Layer
→ Database

---

## Action Validation

Validate:

- action type
- required fields
- inventory availability
- pricing correctness
- order totals
- duplicate products

Return user-friendly errors.

---

# Milestone 3: RAG Using PostgreSQL + pgvector

## Objective

Ground AI responses using business data.

---

## Enable pgvector

Generate migration:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Embedding Table

Create:

### KnowledgeEmbedding

Fields:

- id
- source_type
- source_id
- content
- embedding VECTOR(1536)
- metadata
- created_at

---

## Sources To Embed

Inventory

Orders

Customers

Reports

Help Documents

Business Rules

Knowledge Base

---

## Embedding Pipeline

When:

- Product created
- Product updated
- Order created
- Customer updated

Automatically:

1. Generate embedding
2. Store in pgvector
3. Update retrieval index

---

## Retriever

Implement similarity search using:

```sql
ORDER BY embedding <=> query_embedding
```

---

## RAG Queries

Support:

- What products are low in stock?
- Which products sold the most this month?
- Show revenue trend.
- Who are my best customers?
- Summarize sales performance.

---

# Milestone 4: Analytics

Create analytics service.

Generate:

## Revenue

- Daily
- Weekly
- Monthly
- Yearly

---

## Inventory

- Low Stock
- Fast Moving
- Slow Moving

---

## Customer

- Top Customers
- New Customers
- Repeat Customers

---

## Product

- Best Sellers
- Least Selling Products

---

# Milestone 5: Modern UI

Keep existing UI working.

Enhance:

## Dashboard

Add:

- Revenue Chart
- Orders Chart
- Inventory Chart
- Customer Growth Chart

Use:

- Chart.js

---

## Inventory

Add:

- Search
- Sort
- Filters
- Create Product Form
- Edit Product Form

---

## Orders

Add:

- Search
- Date Range Filter
- Status Filter
- Export Button

---

## Customers

Add:

- Search
- Customer Profile
- Purchase History

---

## Notifications

Add:

- Toast notifications
- Success messages
- Error messages
- Loading states

---

# Milestone 6: Reporting & Export

## CSV Export

Generate exports for:

- Inventory
- Orders
- Customers

---

## PDF Invoices

Use:

- reportlab

Invoice must include:

- Company Information
- Invoice Number
- Customer Details
- Product Table
- Tax
- Grand Total

---

## Reporting

Generate:

- Daily Revenue
- Weekly Revenue
- Monthly Revenue
- Product Reports
- Customer Reports

---

# Milestone 7: Authentication & Authorization

Implement:

## Authentication

- JWT Authentication
- Refresh Tokens
- Password Hashing

Use:

- bcrypt
- PyJWT

---

## Roles

Admin

Manager

Staff

---

## Permissions

Admin:
- Full Access

Manager:
- Inventory
- Orders
- Reports

Staff:
- Orders Only

---

# Future Extension Points

Design architecture for:

- WhatsApp Integration
- SMS Notifications
- Supplier Management
- Purchase Orders
- Multi-Location Inventory
- Multi-Tenant Businesses
- Mobile App
- PWA
- AI Recommendations
- Sales Forecasting

Do NOT implement these now.

Create extension interfaces only.

---

# Development Rules

1. Follow Clean Architecture.
2. Follow SOLID Principles.
3. Use Repository Pattern.
4. Use Service Layer Pattern.
5. Use Dependency Injection where appropriate.
6. Add Type Hints everywhere.
7. Add Unit Tests.
8. Add API Documentation.
9. Add Logging.
10. Add Error Handling.
11. Add Alembic Migrations.
12. Add PostgreSQL Optimization.
13. Add pgvector Integration.
14. Keep APIs backward compatible.
15. Generate production-quality code only.

---

# Expected Output

For every milestone provide:

1. Folder Structure
2. Database Schema
3. SQLAlchemy Models
4. Alembic Migration Files
5. Service Layer Code
6. Repository Layer Code
7. API Endpoints
8. Unit Tests
9. Implementation Notes
10. Migration Strategy

Start with Milestone 1 and generate complete implementation code.