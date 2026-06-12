from typing import List, Optional

from backend.embeddings.manager import index_product_embedding
from backend.storage.database import get_db_session
from backend.storage.models import Product
from backend.storage.repositories.inventory_repository import InventoryRepository


class InventoryService:
    def __init__(self, session):
        self.session = session
        self.repository = InventoryRepository(session)

    def list_products(self) -> List[dict]:
        return [product.to_dict() for product in self.repository.list_all()]

    def get_low_stock_products(self) -> List[dict]:
        return [product.to_dict() for product in self.repository.list_low_stock()]

    def find_by_name(self, name: str) -> Optional[Product]:
        return self.repository.get_by_name(name)

    def create_or_update_product(
        self,
        name: str,
        sku: str,
        price: float,
        qty: float,
        unit: str = 'pcs',
        description: str | None = None,
        low_stock_threshold: float = 10.0,
    ) -> Product:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError('Product name is required')

        existing = self.repository.get_by_name(normalized_name)
        if existing:
            existing.price = price
            existing.quantity = existing.quantity + qty
            existing.unit = unit or existing.unit
            existing.sku = sku or existing.sku
            existing.description = description or existing.description
            existing.low_stock_threshold = low_stock_threshold
            updated = self.repository.create(existing)
            index_product_embedding(self.session, updated)
            return updated

        product = Product(
            name=normalized_name,
            sku=sku.strip() if sku else normalized_name[:3].upper() + '001',
            price=price,
            quantity=qty,
            unit=unit or 'pcs',
            description=description,
            low_stock_threshold=low_stock_threshold,
        )
        created = self.repository.create(product)
        index_product_embedding(self.session, created)
        return created

    def adjust_stock(self, name: str, qty_change: float) -> Optional[Product]:
        product = self.repository.get_by_name(name)
        if not product:
            return None
        product.quantity = max(0.0, product.quantity + qty_change)
        return self.repository.create(product)

    def delete_product(self, name: str) -> bool:
        product = self.repository.get_by_name(name)
        if not product:
            return False
        self.repository.delete(product)
        return True

    def update_product_by_id(self, product_id: int, name: str | None = None, sku: str | None = None,
                             price: float | None = None, qty: float | None = None,
                             unit: str | None = None, description: str | None = None,
                             low_stock_threshold: float | None = None):
        product = self.repository.get_by_id(product_id)
        if not product:
            raise ValueError('Product not found')

        if name is not None:
            product.name = name.strip() or product.name
        if sku is not None:
            product.sku = sku.strip() or product.sku
        if price is not None:
            product.price = float(price)
        if qty is not None:
            product.quantity = float(product.quantity or 0.0) + float(qty)
        if unit is not None:
            product.unit = unit or product.unit
        if description is not None:
            product.description = description or product.description
        if low_stock_threshold is not None:
            product.low_stock_threshold = low_stock_threshold

        updated = self.repository.create(product)
        try:
            from backend.embeddings.manager import index_product_embedding
            index_product_embedding(self.session, updated)
        except Exception:
            pass
        return updated

    def delete_product_by_id(self, product_id: int) -> bool:
        product = self.repository.get_by_id(product_id)
        if not product:
            return False
        self.repository.delete(product)
        return True
