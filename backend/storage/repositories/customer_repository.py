from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.storage.models import Customer


class CustomerRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> List[Customer]:
        result = self.session.execute(select(Customer).order_by(Customer.name))
        return result.scalars().all()

    def get_by_id(self, customer_id: int) -> Optional[Customer]:
        return self.session.get(Customer, customer_id)

    def get_by_name(self, name: str) -> Optional[Customer]:
        return self.session.execute(
            select(Customer).where(Customer.name.ilike(name.strip()))
        ).scalars().first()

    def create(self, customer: Customer) -> Customer:
        self.session.add(customer)
        self.session.flush()
        return customer

    def update(self, customer: Customer) -> Customer:
        self.session.add(customer)
        self.session.flush()
        return customer

    def list_new_customers(self, limit: int = 20) -> List[Customer]:
        result = self.session.execute(select(Customer).order_by(Customer.created_at.desc()).limit(limit))
        return result.scalars().all()
