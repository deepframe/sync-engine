import enum

from inbox.models.thread import Thread
from inbox.models.folder import Folder, FolderItem
from inbox.util.file import Lock
from inbox.log import get_logger
log = get_logger()


class NotFound(Exception):
    pass


class EncryptionScheme(enum.Enum):
    # No encryption
    NULL = 0

    # nacl.secret.SecretBox with a static key
    SECRETBOX_WITH_STATIC_KEY = 1


# Namespace Utils


def _db_write_lockfile_name(account_id):
    return "/var/lock/inbox_datastore/{0}.lock".format(account_id)


def db_write_lock(namespace_id):
    """ Protect updating this namespace's Inbox datastore data.

    Note that you should also use this to wrap any code that _figures
    out_ what to update the datastore with, because outside the lock
    you can't guarantee no one is updating the data behind your back.
    """
    return Lock(_db_write_lockfile_name(namespace_id), block=True)


def threads_for_folder(namespace_id, session, folder_name):
    """ NOTE: Does not work for shared folders. """
    return session.query(Thread).join(FolderItem).join(Folder).filter(
        Thread.namespace_id == namespace_id,
        Folder.name == folder_name)
