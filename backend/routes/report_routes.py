from flask import Blueprint, jsonify, Response, send_file
import csv
import io

from backend.auth.permissions import requires_roles
from backend.services.report_service import ReportService
from backend.services.inventory_service import InventoryService
from backend.services.customer_service import CustomerService
from backend.services.order_service import OrderService
from backend.storage.database import get_db_session

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
except Exception:
    letter = None
    canvas = None

report_bp = Blueprint('report_bp', __name__)


@report_bp.route('/api/reports/summary', methods=['GET'])
@requires_roles('manager', 'admin')
def api_report_summary():
    with get_db_session() as session:
        state = ReportService(session).build_dashboard_state()
    return jsonify(state)


@report_bp.route('/api/export/inventory', methods=['GET'])
@requires_roles('manager', 'admin')
def export_inventory_csv():
    with get_db_session() as session:
        products = InventoryService(session).list_products()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['id', 'sku', 'name', 'description', 'price', 'quantity', 'unit', 'low_stock_threshold', 'created_at'])
    for p in products:
        writer.writerow([p['id'], p['sku'], p['name'], p.get('description') or '', p.get('price') or 0.0, p.get('quantity') or 0.0, p.get('unit') or '', p.get('low_stock_threshold') or 0.0, p.get('created_at') or ''])

    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='inventory.csv')


@report_bp.route('/api/export/customers', methods=['GET'])
@requires_roles('manager', 'admin')
def export_customers_csv():
    with get_db_session() as session:
        customers = CustomerService(session).list_customers()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['id', 'name', 'phone', 'email', 'address', 'total_spent', 'order_count', 'created_at'])
    for c in customers:
        writer.writerow([c['id'], c['name'], c.get('phone') or '', c.get('email') or '', c.get('address') or '', c.get('total_spent') or 0.0, c.get('order_count') or 0, c.get('created_at') or ''])

    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='customers.csv')


@report_bp.route('/api/export/orders', methods=['GET'])
@requires_roles('manager', 'admin')
def export_orders_csv():
    with get_db_session() as session:
        orders = OrderService(session).list_orders()

    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(['id', 'invoice_number', 'customer', 'subtotal', 'tax', 'total', 'status', 'payment_status', 'created_at'])
    for o in orders:
        writer.writerow([o['id'], o['invoice_number'], o.get('customer') or '', o.get('subtotal') or 0.0, o.get('tax') or 0.0, o.get('total') or 0.0, o.get('status') or '', o.get('payment_status') or '', o.get('created_at') or ''])

    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='orders.csv')


@report_bp.route('/api/export/invoice/<invoice_number>', methods=['GET'])
@requires_roles('manager', 'admin')
def export_invoice_pdf(invoice_number: str):
    with get_db_session() as session:
        order = OrderService(session).get_by_invoice(invoice_number)
        if not order:
            return jsonify({'error': 'Order not found'}), 404

    if canvas is None:
        return jsonify({'error': 'PDF generation not available (reportlab not installed)'}), 500

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont('Helvetica-Bold', 16)
    p.drawString(40, height - 50, 'Invoice')
    p.setFont('Helvetica', 10)
    p.drawString(40, height - 70, f"Invoice #: {order['invoice_number']}")
    p.drawString(40, height - 85, f"Customer: {order.get('customer')}")
    p.drawString(40, height - 100, f"Date: {order.get('created_at')}")

    y = height - 140
    p.setFont('Helvetica-Bold', 10)
    p.drawString(40, y, 'Item')
    p.drawString(300, y, 'Qty')
    p.drawString(360, y, 'Unit Price')
    p.drawString(460, y, 'Line Total')
    y -= 14
    p.setFont('Helvetica', 10)
    for item in order.get('items', []):
        p.drawString(40, y, item.get('name') or '')
        p.drawString(300, y, str(item.get('quantity') or ''))
        p.drawString(360, y, f"{float(item.get('unit_price') or 0):.2f}")
        p.drawString(460, y, f"{float(item.get('line_total') or 0):.2f}")
        y -= 14
        if y < 80:
            p.showPage()
            y = height - 50

    p.setFont('Helvetica-Bold', 12)
    p.drawString(360, y - 10, 'Total:')
    p.drawString(460, y - 10, f"{float(order.get('total') or 0):.2f}")

    p.showPage()
    p.save()
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True, download_name=f"invoice_{invoice_number}.pdf")
