# BizFlow AI — Local Setup

**Full documentation:** see the [`docs/`](docs/README.md) folder (architecture, API, data schema, user guide, and development).

## Prerequisites
- Python 3.10+
- Free Groq API key from https://console.groq.com

## Setup

1. Clone or unzip the project folder, then enter the app directory:
   ```bash
   cd bizflow-ai
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file (or edit the existing one):
   ```
   GROQ_API_KEY=gsk_your_key_here
   ```

5. Run the app:
   ```bash
   python app.py
   ```

6. Open browser:
   http://localhost:5000

## Usage Examples
- "Add product Wheat at ₹45 per kg, quantity 200"
- "Create invoice for Suresh for 10 Wheat and 5 Rice"
- "Add customer Meena, phone 9823456789"
- "How many products are low on stock?"
- "What is my total revenue this month?"
- "Mark order INV-1002 as cancelled"
