from sqlalchemy import desc
from inbox.models import Transaction, Calendar
from inbox.models.mixins import HasRevisions
from inbox.models.util import transaction_objects
from tests.util.base import add_fake_message, add_fake_thread, add_fake_event


def get_latest_transaction(db_session, object_type, record_id, namespace_id):
    return db_session.query(Transaction).filter(
        Transaction.namespace_id == namespace_id,
        Transaction.object_type == object_type,
        Transaction.record_id == record_id). \
        order_by(desc(Transaction.id)).first()


def test_thread_insert_creates_transaction(db, default_namespace):
    thr = add_fake_thread(db.session, default_namespace.id)
    transaction = get_latest_transaction(db.session, 'thread', thr.id,
                                         default_namespace.id)
    assert transaction.command == 'insert'


def test_message_insert_creates_transaction(db, default_namespace):
    with db.session.no_autoflush:
        thr = add_fake_thread(db.session, default_namespace.id)
        msg = add_fake_message(db.session, default_namespace.id, thr)
        transaction = get_latest_transaction(db.session, 'message', msg.id,
                                             default_namespace.id)
        assert transaction.command == 'insert'

        # Test that the thread gets revised too
        transaction = get_latest_transaction(db.session, 'thread', thr.id,
                                             default_namespace.id)
        assert transaction.command == 'update'


def test_message_updates_create_transaction(db, default_namespace):
    with db.session.no_autoflush:
        thr = add_fake_thread(db.session, default_namespace.id)
        msg = add_fake_message(db.session, default_namespace.id, thr)

        msg.is_read = True
        db.session.commit()
        transaction = get_latest_transaction(db.session, 'message', msg.id,
                                             default_namespace.id)
        assert transaction.record_id == msg.id
        assert transaction.object_type == 'message'
        assert transaction.command == 'update'


def test_message_updates_create_thread_transaction(db, default_namespace):
    with db.session.no_autoflush:
        thr = add_fake_thread(db.session, default_namespace.id)
        msg = add_fake_message(db.session, default_namespace.id, thr)

        transaction = get_latest_transaction(db.session, 'thread', thr.id,
                                             default_namespace.id)
        assert (transaction.record_id == thr.id and
                transaction.object_type == 'thread')
        assert transaction.command == 'update'

        # An update to one of the message's propagated_attributes creates a
        # revision for the thread
        msg.is_read = True
        db.session.commit()

        new_transaction = get_latest_transaction(db.session, 'thread', thr.id,
                                                 default_namespace.id)
        assert new_transaction.id != transaction.id
        assert (new_transaction.record_id == thr.id and
                new_transaction.object_type == 'thread')
        assert new_transaction.command == 'update'

        # An update to one of its other attributes does not
        msg.subject = 'Ice cubes and dogs'
        db.session.commit()

        same_transaction = get_latest_transaction(db.session, 'thread', thr.id,
                                                  default_namespace.id)
        assert same_transaction.id == new_transaction.id


def test_object_type_distinguishes_messages_and_drafts(db, default_namespace):
    with db.session.no_autoflush:
        thr = add_fake_thread(db.session, default_namespace.id)
        msg = add_fake_message(db.session, default_namespace.id, thr)
        msg.is_draft = 1
        db.session.commit()
        transaction = get_latest_transaction(db.session, 'draft', msg.id,
                                             default_namespace.id)
        assert transaction.command == 'update'
        db.session.delete(msg)
        db.session.commit()
        transaction = get_latest_transaction(db.session, 'draft', msg.id,
                                             default_namespace.id)
        assert transaction.command == 'delete'


def test_event_insert_creates_transaction(db, default_namespace):
    with db.session.no_autoflush:
        event = add_fake_event(db.session, default_namespace.id)
        transaction = get_latest_transaction(db.session, 'event',
                                             event.id, default_namespace.id)
        assert transaction.record_id == event.id
        assert transaction.object_type == 'event'
        assert transaction.command == 'insert'


def test_transactions_created_for_calendars(db, default_namespace):
    calendar = Calendar(
        namespace_id=default_namespace.id,
        name='New Calendar',
        uid='uid')
    db.session.add(calendar)
    db.session.commit()
    transaction = get_latest_transaction(db.session, 'calendar',
                                         calendar.id, default_namespace.id)
    assert transaction.record_id == calendar.id
    assert transaction.object_type == 'calendar'
    assert transaction.command == 'insert'

    calendar.name = 'Updated Calendar'
    db.session.commit()
    transaction = get_latest_transaction(db.session, 'calendar',
                                         calendar.id, default_namespace.id)
    assert transaction.record_id == calendar.id
    assert transaction.object_type == 'calendar'
    assert transaction.command == 'update'

    db.session.delete(calendar)
    db.session.commit()
    transaction = get_latest_transaction(db.session, 'calendar',
                                         calendar.id, default_namespace.id)
    assert transaction.record_id == calendar.id
    assert transaction.object_type == 'calendar'
    assert transaction.command == 'delete'


def test_object_deletions_create_transaction(db, default_namespace):
    with db.session.no_autoflush:
        thr = add_fake_thread(db.session, default_namespace.id)
        msg = add_fake_message(db.session, default_namespace.id, thr)
        db.session.delete(msg)
        db.session.commit()
        transaction = get_latest_transaction(db.session, 'message', msg.id,
                                             default_namespace.id)
        assert transaction.record_id == msg.id
        assert transaction.object_type == 'message'
        assert transaction.command == 'delete'

        db.session.delete(thr)
        db.session.commit()
        transaction = get_latest_transaction(db.session, 'thread', thr.id,
                                             default_namespace.id)
        assert transaction.record_id == thr.id
        assert transaction.object_type == 'thread'
        assert transaction.command == 'delete'


def test_transaction_objects_mapped_for_all_models(db, default_namespace):
    """
    Test that all subclasses of HasRevisions are mapped by the
    transaction_objects() function.

    """
    assert set(HasRevisions.__subclasses__()).issubset(
        transaction_objects().values())
