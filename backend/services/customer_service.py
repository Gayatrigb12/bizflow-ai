from typing import List, Optional

from backend.embeddings.manager import index_customer_embedding
from backend.storage.models import Customer
from backend.storage.repositories.customer_repository import CustomerRepository


class CustomerService:
    def __init__(self, session):
        self.session = session
        self.repository = CustomerRepository(session)

    def list_customers(self) -> List[dict]:
        return [customer.to_dict() for customer in self.repository.list_all()]

    def get_customer_profile(self, customer_id: int) -> Optional[dict]:
        from backend.storage.repositories.order_repository import OrderRepository

        customer = self.repository.get_by_id(customer_id)
        if not customer:
            return None

        profile = customer.to_dict()
        orders = OrderRepository(self.session).list_by_customer_id(customer_id)
        profile['orders'] = [order.to_dict() for order in orders]
        return profile

    def get_by_name(self, name: str) -> Optional[Customer]:
        return self.repository.get_by_name(name)

    def create_customer(
        self,
        name: str,
        phone: str = '',
        email: str = '',
        address: str = '',
    ) -> Customer:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError('Customer name is required')

        existing = self.repository.get_by_name(normalized_name)
        if existing:
            existing.phone = phone or existing.phone
            existing.email = email or existing.email
            existing.address = address or existing.address
            updated = self.repository.update(existing)
            index_customer_embedding(self.session, updated)
            return updated

        customer = Customer(
            name=normalized_name,
            phone=phone,
            email=email,
            address=address,
        )
        created = self.repository.create(customer)
        index_customer_embedding(self.session, created)
        return created

    def update_stats(self, customer: Customer, order_total: float) -> Customer:
        customer.total_spent += order_total
        customer.order_count += 1
        return self.repository.update(customer)
