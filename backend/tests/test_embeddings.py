from sqlalchemy import select

from backend.embeddings.retriever import similarity_search
from backend.storage.models import KnowledgeEmbedding
from backend.services.customer_service import CustomerService
from backend.services.inventory_service import InventoryService
from backend.services.order_service import OrderService


def test_embedding_records_created_for_entities(db_session):
    inventory_service = InventoryService(db_session)
    customer_service = CustomerService(db_session)
    order_service = OrderService(db_session)

    product = inventory_service.create_or_update_product(
        name='Sugar',
        sku='SUG001',
        price=30.0,
        qty=50,
        unit='kg',
    )

    customer = customer_service.create_customer('Anita', phone='555-1234')
    order = order_service.create_order(
        customer_name='Anita',
        items=[{'name': 'Sugar', 'qty': 5}],
        status='paid',
        payment_status='paid',
    )

    product_embedding = db_session.execute(
        select(KnowledgeEmbedding).where(
            KnowledgeEmbedding.object_type == 'product',
            KnowledgeEmbedding.object_id == product.id,
        )
    ).scalar_one_or_none()
    assert product_embedding is not None
    assert product_embedding.object_type == 'product'
    assert product_embedding.object_id == product.id
    assert isinstance(product_embedding.embedding, list)
    assert product_embedding.meta['type'] == 'product'

    customer_embedding = db_session.execute(
        select(KnowledgeEmbedding).where(
            KnowledgeEmbedding.object_type == 'customer',
            KnowledgeEmbedding.object_id == customer.id,
        )
    ).scalar_one_or_none()
    assert customer_embedding is not None
    assert customer_embedding.meta['type'] == 'customer'

    order_embedding = db_session.execute(
        select(KnowledgeEmbedding).where(
            KnowledgeEmbedding.object_type == 'order',
            KnowledgeEmbedding.object_id == order.id,
        )
    ).scalar_one_or_none()
    assert order_embedding is not None
    assert order_embedding.meta['type'] == 'order'


def test_similarity_search_returns_best_match(db_session):
    inventory_service = InventoryService(db_session)

    first = inventory_service.create_or_update_product(
        name='Alpha Wheat',
        sku='ALP001',
        price=25.0,
        qty=20,
        unit='kg',
    )
    second = inventory_service.create_or_update_product(
        name='Beta Rice',
        sku='BET002',
        price=35.0,
        qty=20,
        unit='kg',
    )

    first_embedding = db_session.execute(
        select(KnowledgeEmbedding).where(
            KnowledgeEmbedding.object_type == 'product',
            KnowledgeEmbedding.object_id == first.id,
        )
    ).scalar_one()

    results = similarity_search(db_session, first_embedding.embedding, top_k=2)
    assert len(results) >= 1
    assert results[0]['object_type'] == 'product'
    assert results[0]['object_id'] == first.id


def test_context_builder_includes_retrieval_snippets(db_session):
    from backend.ai.context_builder import ContextBuilder
    from backend.services.inventory_service import InventoryService

    inventory_service = InventoryService(db_session)
    product = inventory_service.create_or_update_product(
        name='Gamma Sugar',
        sku='GAM003',
        price=45.0,
        qty=15,
        unit='kg',
    )

    state = ContextBuilder(db_session).build('Gamma Sugar')

    assert 'retrieval_snippets' in state
    assert isinstance(state['retrieval_snippets'], list)
    assert len(state['retrieval_snippets']) >= 1
    snippet = state['retrieval_snippets'][0]
    assert 'snippet' in snippet
    assert isinstance(snippet['snippet'], str)
    assert len(snippet['snippet'].strip()) > 0
