from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.storage.models import Order


class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> List[Order]:
        result = self.session.execute(select(Order).order_by(Order.created_at.desc()))
        return result.scalars().all()

    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self.session.get(Order, order_id)

    def get_by_invoice_number(self, invoice_number: str) -> Optional[Order]:
        return self.session.execute(
            select(Order).where(Order.invoice_number == invoice_number.strip())
        ).scalars().first()

    def create(self, order: Order) -> Order:
        self.session.add(order)
        self.session.flush()
        return order

    def update(self, order: Order) -> Order:
        self.session.add(order)
        self.session.flush()
        return order

    def list_recent(self, limit: int = 10) -> List[Order]:
        result = self.session.execute(select(Order).order_by(Order.created_at.desc()).limit(limit))
        return result.scalars().all()

    def list_by_customer_id(self, customer_id: int) -> List[Order]:
        result = self.session.execute(
            select(Order)
            .where(Order.customer_id == customer_id)
            .order_by(Order.created_at.desc())
        )
        return result.scalars().all()

    def get_latest_invoice(self) -> Optional[str]:
        result = self.session.execute(select(Order.invoice_number).order_by(desc(Order.id)).limit(1))
        row = result.scalar_one_or_none()
        return row

    def delete(self, order: Order) -> None:
        self.session.delete(order)
