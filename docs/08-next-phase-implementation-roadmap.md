# Next Phase Implementation Roadmap

This document defines the next phase of work for BizFlow AI, with feature priorities, architecture improvements, and implementation milestones.

## Goals for the next phase

- move from prototype to product-ready architecture
- improve reliability, extensibility, and user experience
- add product features that deliver real business value
- create a stronger foundation for future growth

## Priority areas

### 1. Modular backend and persistence

What to do:
- split `app.py` into modules: routes, services, storage, AI integration
- replace JSON file persistence with SQLite or SQLAlchemy
- add a simple database initialization and migration path
- isolate business logic from web route handlers

Why:
- easier testing and maintenance
- safer data storage
- better foundation for multi-user and analytics

### 2. AI orchestration layer

What to do:
- add LangChain-style orchestration for commands
- create prompt templates and tool definitions
- implement action validation before state changes
- support multiple AI providers with a pluggable interface

Why:
- makes the AI workflow more robust
- allows future upgrades without rewriting core logic
- improves safety and traceability of model actions

### 3. Retrieval and grounding

What to do:
- add a vector store for business data and docs
- implement a retriever for historical and analytics queries
- use RAG to answer reporting and lookup questions
- add a small knowledge base for business rules and help text

Why:
- reduces AI hallucinations
- makes analytics answers more accurate
- supports complex queries using real data

### 4. Better UI and explicit workflows

What to do:
- refine the dashboard with charts and filters
- add dedicated pages/forms for products, orders, and customers
- keep AI chat but make it one interaction mode among many
- add search, sort, and low-stock alerts

Why:
- better usability for non-chat-first users
- supports faster operations and transparency
- increases product maturity and adoption

### 5. Reporting, export, and notifications

What to do:
- add CSV export for inventory/orders/customers
- add PDF invoice generation
- add notification hooks for low stock and order status
- add basic reporting: revenue by day/week/month

Why:
- delivers business value beyond chat
- supports real operational workflows
- makes the product more compelling for customers

## Implementation milestones

### Milestone 1 — Core refactor

- create `routes.py`, `services.py`, `storage.py`, `ai.py`
- implement SQLite persistence
- add basic unit tests for service actions
- keep existing UI working with new API

### Milestone 2 — AI and RAG integration

- add prompt templates and validation
- add vector store for retrieval
- implement RAG for analytics questions
- add AI provider switching support

### Milestone 3 — UI improvements

- add search/filter in inventory/orders/customers
- add explicit create/edit forms
- add dashboard metrics and charts
- add clear status and error handling

### Milestone 4 — Product features

- add invoice PDF export
- add CSV export
- add order date filtering and export
- add low-stock alert and reminder support

### Milestone 5 — Product readiness

- add authentication/user roles
- harden error handling and validation
- improve docs and deployment instructions
- prepare a product demo and onboarding flow

## Long-term extensions

- WhatsApp/SMS integration for customer notifications
- supplier and purchase order management
- sales forecasting and trend prediction
- multi-business/multi-location support
- mobile-first UI or PWA

## How to use this roadmap

- treat this as the next phase after the current prototype
- implement one milestone at a time
- validate each improvement with a real small-business use case
- keep the AI assistant grounded in business data and rules
