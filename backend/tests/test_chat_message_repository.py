from backend.storage.repositories.chat_message_repository import ChatMessageRepository


def test_chat_message_repository_add_and_list(db_session):
    repo = ChatMessageRepository(db_session)

    saved = repo.add(
        user_prompt='Add rice to inventory',
        ai_response='Rice has been added.',
        session_id='session-test-1',
        metadata={'actions': [{'type': 'add_product', 'name': 'Rice'}]},
        actor='1',
        context_type='inventory',
    )
    db_session.commit()

    assert saved.id is not None
    assert saved.user_prompt == 'Add rice to inventory'
    assert saved.ai_response == 'Rice has been added.'
    assert saved.session_id == 'session-test-1'
    assert saved.metadata_json['actions'][0]['type'] == 'add_product'

    messages = repo.list_recent(limit=10, session_id='session-test-1')
    assert len(messages) == 1
    assert messages[0].to_dict()['user_prompt'] == 'Add rice to inventory'


def test_chat_message_repository_list_without_session_filter(db_session):
    repo = ChatMessageRepository(db_session)

    repo.add(user_prompt='Hello', ai_response='Hi', session_id='a')
    repo.add(user_prompt='Bye', ai_response='Goodbye', session_id='b')
    db_session.commit()

    all_messages = repo.list_recent(limit=10)
    session_ids = {msg.session_id for msg in all_messages}
    assert 'a' in session_ids
    assert 'b' in session_ids

    session_a = repo.list_recent(limit=10, session_id='a')
    assert len(session_a) == 1
    assert session_a[0].user_prompt == 'Hello'
