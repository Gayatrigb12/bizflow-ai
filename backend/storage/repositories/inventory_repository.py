from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.storage.models import Product


class InventoryRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_all(self) -> List[Product]:
        result = self.session.execute(select(Product).order_by(Product.name))
        return result.scalars().all()

    def get_by_id(self, product_id: int) -> Optional[Product]:
        return self.session.get(Product, product_id)

    def get_by_name(self, name: str) -> Optional[Product]:
        return self.session.execute(
            select(Product).where(Product.name.ilike(name.strip()))
        ).scalars().first()

    def get_by_sku(self, sku: str) -> Optional[Product]:
        return self.session.execute(
            select(Product).where(Product.sku == sku.strip())
        ).scalars().first()

    def create(self, product: Product) -> Product:
        self.session.add(product)
        self.session.flush()
        return product

    def delete(self, product: Product) -> None:
        self.session.delete(product)

    def list_low_stock(self) -> List[Product]:
        result = self.session.execute(
            select(Product).where(Product.quantity <= Product.low_stock_threshold).order_by(Product.quantity)
        )
        return result.scalars().all()

    def search_by_name(self, query: str) -> List[Product]:
        pattern = f"%{query.strip()}%"
        result = self.session.execute(
            select(Product).where(Product.name.ilike(pattern)).order_by(Product.name)
        )
        return result.scalars().all()
