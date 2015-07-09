from inbox.mailsync.backends.imap.generic import uidvalidity_cb
from inbox.crispin import writable_connection_pool
from inbox.models.session import session_scope
from inbox.models import Account
import IPython


def user_console(user_email_address):
    with session_scope() as db_session:
        account = db_session.query(Account).filter_by(
            email_address=user_email_address).one()

        with writable_connection_pool(account.id, pool_size=1).get()\
                as crispin_client:
            if account.provider == 'gmail' \
                    and 'all' in crispin_client.folder_names():
                crispin_client.select_folder(
                    crispin_client.folder_names()['all'][0],
                    uidvalidity_cb)

                banner = """
        You can access the crispin instance with the 'crispin_client' variable.

        IMAPClient docs are at:

            http://imapclient.readthedocs.org/en/latest/#imapclient-class-reference
        """

                IPython.embed(banner1=banner)


def start_console(user_email_address=None):
    # You can also do this with
    # $ python -m imapclient.interact -H <host> -u <user> ...
    # but we want to use our session and crispin so we're not.
    if user_email_address:
        user_console(user_email_address)
    else:
        IPython.embed()


def start_client_console(user_email_address=None):
    from tests.system.client import InboxTestClient
    client = InboxTestClient(user_email_address)
    IPython.embed(banner1=("You can access an Inbox API client "
                           "using the 'client' variable."))
