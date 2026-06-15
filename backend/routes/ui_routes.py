from flask import Blueprint, render_template

ui_bp = Blueprint('ui_bp', __name__, template_folder='../../templates')


@ui_bp.route('/')
def index():
    return render_template('login.html')


@ui_bp.route('/login')
def login():
    return render_template('login.html')


@ui_bp.route('/chat')
def chat():
    return render_template('chat.html')


@ui_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@ui_bp.route('/inventory')
def inventory():
    return render_template('inventory.html')


@ui_bp.route('/orders')
def orders():
    return render_template('orders.html')


@ui_bp.route('/customers')
def customers():
    return render_template('customers.html')


@ui_bp.route('/approvals')
def approvals():
    return render_template('approvals.html')


@ui_bp.route('/reports')
def reports():
    return render_template('reports.html')
