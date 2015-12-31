import random
from tests.util.base import (add_fake_account, add_fake_thread, add_fake_message,
                             add_fake_calendar, add_fake_event, add_fake_folder,
                             add_fake_imapuid, add_fake_gmail_account,
                             add_fake_contact, add_fake_msg_with_calendar_part)


def random_range(start, end):
    return range(random.randrange(start, end))


def add_completely_fake_account(db, email='test@nylas.com'):
    from inbox.models.backends.gmail import GmailAuthCredentials
    fake_account = add_fake_gmail_account(db.session, email_address=email)
    calendar = add_fake_calendar(db.session, fake_account.namespace.id)
    for i in random_range(1, 10):
        ev = add_fake_event(db.session, fake_account.namespace.id,
                            calendar=calendar, title='%s' % i)

    # Add fake Threads, Messages and ImapUids.
    folder = add_fake_folder(db.session, fake_account)
    for i in random_range(1, 4):
        th = add_fake_thread(db.session, fake_account.namespace.id)

        for j in random_range(1, 3):
            msg = add_fake_msg_with_calendar_part(db.session,
                                                  fake_account,
                                                  'fake part', thread=th)
            db.session.add(msg)
            db.session.flush()

            for k in random_range(1, 2):
                uid = add_fake_imapuid(db.session, fake_account.id, msg,
                                       folder, int('%s%s' % (msg.id, k)))
    # Add fake contacts
    for i in random_range(1, 5):
        add_fake_contact(db.session, fake_account.namespace.id, uid=str(i))

    auth_creds = GmailAuthCredentials()
    auth_creds.gmailaccount = fake_account
    auth_creds.scopes = "email"
    auth_creds.g_id_token = "test"
    auth_creds.client_id = "test"
    auth_creds.client_secret = "test"
    auth_creds.refresh_token = "test"
    auth_creds.is_valid = True
    db.session.add(auth_creds)
    db.session.commit()

    return fake_account


def test_namespace_deletion(db, default_account):
    from inbox.models import (Account, Thread, Message, Block,
                              Contact, Event, Transaction)
    from inbox.models.util import delete_namespace

    models = [Thread, Message]

    namespace = default_account.namespace
    namespace_id = namespace.id
    account_id = default_account.id

    account = db.session.query(Account).get(account_id)
    assert account

    thread = add_fake_thread(db.session, namespace_id)

    message = add_fake_message(db.session, namespace_id, thread)

    for m in models:
        c = db.session.query(m).filter(
            m.namespace_id == namespace_id).count()
        print "count for", m, ":", c
        assert c != 0

    fake_account = add_fake_account(db.session)
    fake_account_id = fake_account.id

    assert fake_account_id != account.id and \
        fake_account.namespace.id != namespace_id

    thread = add_fake_thread(db.session, fake_account.namespace.id)
    thread_id = thread.id

    message = add_fake_message(db.session, fake_account.namespace.id, thread)
    message_id = message.id

    # Delete namespace, verify data corresponding to this namespace /only/
    # is deleted
    delete_namespace(account_id, namespace_id)
    db.session.commit()

    account = db.session.query(Account).get(account_id)
    assert not account

    for m in models:
        assert db.session.query(m).filter(
            m.namespace_id == namespace_id).count() == 0

    fake_account = db.session.query(Account).get(fake_account_id)
    assert fake_account

    thread = db.session.query(Thread).get(thread_id)
    message = db.session.query(Message).get(message_id)
    assert thread and message


def test_fake_accounts(empty_db):
    from inbox.models import (Account, Thread, Message, Block, Part,
                              Secret, Contact, Event, Transaction)
    from inbox.models.backends.imap import ImapUid
    from inbox.models.backends.gmail import GmailAuthCredentials
    from inbox.models.util import delete_namespace

    models = [Thread, Message, Event, Transaction, Contact, Block]

    db = empty_db
    account = add_completely_fake_account(db)

    for m in models:
        c = db.session.query(m).filter(
            m.namespace_id == account.namespace.id).count()
        assert c != 0

    assert db.session.query(ImapUid).count() != 0
    assert db.session.query(Secret).count() != 0
    assert db.session.query(GmailAuthCredentials).count() != 0
    assert db.session.query(Account).filter(
        Account.id == account.id).count() == 1

    # Try the dry-run mode:
    delete_namespace(account.id, account.namespace.id, dry_run=True)

    for m in models:
        c = db.session.query(m).filter(
            m.namespace_id == account.namespace.id).count()
        assert c != 0

    assert db.session.query(Account).filter(
        Account.id == account.id).count() != 0

    assert db.session.query(Secret).count() != 0
    assert db.session.query(GmailAuthCredentials).count() != 0
    assert db.session.query(ImapUid).count() != 0

    # Now delete the account for reals.
    delete_namespace(account.id, account.namespace.id)

    for m in models:
        c = db.session.query(m).filter(
            m.namespace_id == account.namespace.id).count()
        assert c == 0

    assert db.session.query(Account).filter(
        Account.id == account.id).count() == 0

    assert db.session.query(Secret).count() == 0
    assert db.session.query(GmailAuthCredentials).count() == 0
    assert db.session.query(ImapUid).count() == 0


def test_multiple_fake_accounts(empty_db):
    # Add three fake accounts, check that removing one doesn't affect
    # the two others.
    from inbox.models import (Account, Thread, Message, Block, Part,
                              Secret, Contact, Event, Transaction)
    from inbox.models.backends.imap import ImapUid
    from inbox.models.backends.gmail import GmailAuthCredentials
    from inbox.models.util import delete_namespace

    db = empty_db
    accounts = []
    accounts.append(add_completely_fake_account(db, 'test1@nylas.com'))
    accounts.append(add_completely_fake_account(db, 'test2@nylas.com'))

    # Count secrets and authcredentials now. We can't do it after adding
    # the third account because our object model is a bit cumbersome.
    secret_count = db.session.query(Secret).count()
    authcredentials_count = db.session.query(GmailAuthCredentials).count()
    assert secret_count != 0
    assert authcredentials_count != 0

    accounts.append(add_completely_fake_account(db, 'test3@nylas.com'))

    stats = {}
    models = [Thread, Message, Event, Transaction, Contact, Block]

    for account in accounts:
        stats[account.email_address] = {}
        for model in models:
            clsname = model.__name__
            stats[account.email_address][clsname] = db.session.query(model).filter(
                model.namespace_id == account.namespace.id).count()

    # now delete the third account.
    last_account_id = accounts[2].id
    last_namespace_id = accounts[2].namespace.id

    delete_namespace(last_account_id, last_namespace_id)
    for account in accounts[:2]:
        for model in models:
            clsname = model.__name__
            assert stats[account.email_address][clsname] == db.session.query(model).filter(
                model.namespace_id == account.namespace.id).count()

    # check that no model from the last account is present.
    for model in models:
        clsname = model.__name__
        assert db.session.query(model).filter(
            model.namespace_id == last_namespace_id).count() == 0

    # check that we didn't delete a secret that wasn't ours.
    assert db.session.query(Secret).count() == secret_count
    assert db.session.query(GmailAuthCredentials).count() == authcredentials_count
