# User Guide

How to use BizFlow AI day to day after the app is running at **http://localhost:5000**.

## Starting the app

1. Open a terminal in the `bizflow-ai` folder.
2. Activate your virtual environment (`venv\Scripts\activate` on Windows).
3. Ensure `.env` contains a valid `GROQ_API_KEY`.
4. Run `python app.py`.
5. Open the URL shown in the terminal (default port 5000).

The header shows **Ready** when idle and **Thinking...** while waiting for Groq.

---

## Navigation (sidebar)

| Panel | Purpose |
|-------|---------|
| **Dashboard** | Summary stats and recent activity |
| **AI Chat** | Main control — type commands in plain English |
| **Inventory** | Product cards and stock levels |
| **Orders** | Invoice history with status |
| **Customers** | Directory with spend totals |

Click any sidebar item to switch panels. Badge numbers show counts for inventory, orders, and customers.

---

## AI Chat

### Sending messages

- Type in the text box at the bottom.
- Press **Enter** to send (use **Shift+Enter** for a new line).
- Or click the green send button.

### Suggestion chips

Six quick examples are shown above the input. Click one to send it immediately (switches to chat panel if needed).

Examples:

- Add product Rice ₹60 qty 100 kg
- Create invoice for Rahul for 3 Rice
- Add customer Priya 9876543210
- Show low stock items
- What is my total revenue?
- List all customers

### What you will see in chat

- **Your messages** — green bubbles on the right.
- **AI replies** — gray bubbles on the left.
- **Invoice cards** — after creating an order, line items and total appear inside the AI message.
- **Inventory cards** — after adding/updating a product, name, qty, and price summary.
- **Errors** — red bubble if API key is missing or Groq fails.

After each successful chat, all panels update automatically (no page refresh).

---

## Example commands

### Inventory

```
Add product Rice at ₹60 per kg, quantity 100
Add product Sunflower Oil at ₹180 per litre, qty 50
Update stock for Rice by -10
Delete product Rice
Show products with low stock
```

### Customers

```
Add customer Rahul, phone 9876543210
List all customers
```

### Orders / invoices

```
Create invoice for Rahul for 5 Rice and 2 Sunflower Oil
Mark order INV-1002 as cancelled
```

**Tip:** Use the **full product name** as stored in inventory (e.g. "Sunflower Oil", not "Oil") so prices and stock deduct correctly.

### Reports (no data change — AI computes from state)

```
What is my total revenue?
How many orders do I have?
Which products are low on stock?
```

---

## Dashboard

| Stat | Meaning |
|------|---------|
| Total Orders | Count of all orders |
| Revenue (Paid) | Sum of `total` for orders with `status: paid` |
| Products | Number of inventory items |
| Customers | Number of customer records |

**Recent Activity** shows the last 8 log entries (invoices, new products, customers, etc.).

---

## Inventory panel

- Products shown as cards in a grid.
- Large green number = current quantity.
- **Red left border** = low stock (`qty` at or below threshold, default 10).
- Empty state prompts you to use AI Chat to add products.

---

## Orders panel

Each row shows:

- Invoice ID (`INV-1001`, …)
- Customer name
- Date
- Status badge (paid = green, pending = amber, cancelled = red)
- Total amount in ₹

---

## Customers panel

- Circular avatar with initials
- Name and phone
- Total spent and order count on the right

Customers can be added via chat or **automatically** when you create an invoice for a new name.

---

## Resetting data

To clear all business data programmatically (developers):

```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/reset" -Method POST
```

Or delete `data/store.json` and restart the app (a fresh file will be created).

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Red error: API key not configured | Set real key in `.env`, restart Flask |
| Groq API error | Check internet, key validity, Groq status |
| Wrong invoice total | Ensure product names in chat match inventory exactly |
| UI empty after chat | Check browser console; confirm server is running |
| Data gone after manual delete | Restart app — `load_data()` recreates defaults |

---

## Recommended test sequence

Use this order to verify everything works:

1. Add Rice ₹60, qty 100 kg  
2. Add Sunflower Oil ₹180, qty 50 litre  
3. Add customer Rahul  
4. Invoice Rahul: 5 Rice + 2 Sunflower Oil → expect INV-1001, ₹660, stock 95 / 48  
5. Ask total revenue → ~₹660  
6. Ask low stock items  
7. Invoice Meena: 3 Rice → Meena auto-added, second order  
8. Dashboard → 2 orders, ₹840 revenue, 2 products, 2 customers  
