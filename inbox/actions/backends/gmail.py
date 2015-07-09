""" Operations for syncing back local datastore changes to Gmail. """

from inbox.crispin import writable_connection_pool
from inbox.actions.backends.generic import (set_remote_starred,
                                            set_remote_unread,
                                            remote_delete_draft,
                                            remote_save_draft,
                                            uids_by_folder)
from inbox.mailsync.backends.imap.generic import uidvalidity_cb

PROVIDER = 'gmail'

__all__ = ['set_remote_starred', 'set_remote_unread', 'remote_save_draft',
           'remote_change_labels', 'remote_delete_draft']


def remote_change_labels(account, message_id, db_session, removed_labels,
                         added_labels):
    uids_for_message = uids_by_folder(message_id, db_session)
    with writable_connection_pool(account.id).get() as crispin_client:
        for folder_name, uids in uids_for_message.items():
            crispin_client.select_folder(folder_name, uidvalidity_cb)
            crispin_client.conn.add_gmail_labels(uids, added_labels)
            crispin_client.conn.remove_gmail_labels(uids, removed_labels)
