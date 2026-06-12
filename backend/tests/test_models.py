from backend.storage.models import Customer, Product


def test_product_to_dict():
    product = Product(
        sku='ABC001',
        name='Rice',
        price=45.0,
        quantity=100,
        unit='kg',
        low_stock_threshold=10,
    )
    result = product.to_dict()

    assert result['sku'] == 'ABC001'
    assert result['name'] == 'Rice'
    assert result['price'] == 45.0
    assert result['quantity'] == 100


def test_customer_to_dict():
    customer = Customer(name='Meena', phone='9876543210', email='meena@example.com')
    result = customer.to_dict()

    assert result['name'] == 'Meena'
    assert result['phone'] == '9876543210'
    assert result['email'] == 'meena@example.com'
