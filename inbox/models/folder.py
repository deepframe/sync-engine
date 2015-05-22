from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.schema import UniqueConstraint

from inbox.models.base import MailSyncBase
from inbox.models.tag import Tag
from inbox.models.constants import MAX_FOLDER_NAME_LENGTH, MAX_INDEXABLE_LENGTH
from inbox.log import get_logger
log = get_logger()


class Folder(MailSyncBase):
    """ Folders and labels from the remote account backend (IMAP/Exchange). """
    # `use_alter` required here to avoid circular dependency w/Account
    account_id = Column(Integer,
                        ForeignKey('account.id', use_alter=True,
                                   name='folder_fk1',
                                   ondelete='CASCADE'), nullable=False)

    # TOFIX this causes an import error due to circular dependencies
    # from inbox.models.account import Account
    account = relationship(
        'Account', backref=backref('folders', cascade='delete'),
        foreign_keys=[account_id])

    # Set the name column to be case sensitive, which isn't the default for
    # MySQL. This is a requirement since IMAP allows users to create both a
    # 'Test' and a 'test' (or a 'tEST' for what we care) folders.
    # NOTE: this doesn't hold for EAS, which is case insensitive for non-Inbox
    # folders (see
    # https://msdn.microsoft.com/en-us/library/ee624913(v=exchg.80).aspx).
    name = Column(String(MAX_FOLDER_NAME_LENGTH,
                         collation='utf8mb4_bin'), nullable=True)
    canonical_name = Column(String(MAX_FOLDER_NAME_LENGTH), nullable=True)

    # We use an additional identifier for certain providers,
    # for e.g. EAS uses it to store the eas_folder_id
    identifier = Column(String(MAX_FOLDER_NAME_LENGTH), nullable=True)

    __table_args__ = (UniqueConstraint('account_id', 'name',
                                       name='account_id_2'),)

    @property
    def lowercase_name(self):
        if self.name is None:
            return None
        return self.name.lower()

    @property
    def namespace(self):
        return self.account.namespace

    @classmethod
    def create(cls, account, name, session, canonical_name=None):
        if name is not None and len(name) > MAX_FOLDER_NAME_LENGTH:
            log.warning("Truncating long folder name for account {}; "
                        "original name was '{}'" .format(account.id, name))
            name = name[:MAX_FOLDER_NAME_LENGTH]
        obj = cls(account=account, name=name, canonical_name=canonical_name)
        session.add(obj)
        return obj

    @classmethod
    def find_or_create(cls, session, account, name, canonical_name=None):
        q = session.query(cls).filter_by(account_id=account.id)
        if name is not None:
            # Remove trailing whitespace and truncate to max folder name
            # length. Not ideal but necessary to work around MySQL limitations.
            name = name.rstrip()
            name = name[:MAX_FOLDER_NAME_LENGTH]
            q = q.filter_by(name=name)
        if canonical_name is not None:
            q = q.filter_by(canonical_name=canonical_name)
        try:
            obj = q.one()
        except NoResultFound:
            obj = cls.create(account, name, session, canonical_name)
        except MultipleResultsFound:
            log.info("Duplicate folder rows for folder {} for account {}"
                     .format(name, account.id))
            raise
        return obj

    def get_associated_tag(self, db_session, create_if_missing=True):
        if self.canonical_name is not None:
            try:
                return db_session.query(Tag). \
                    filter(Tag.namespace_id == self.namespace.id,
                           Tag.public_id == self.canonical_name).one()
            except NoResultFound:
                # Explicitly set the namespace_id instead of the namespace
                # attribute to avoid autoflush-induced IntegrityErrors where
                # the namespace_id is null on flush.
                if create_if_missing:
                    tag = Tag(namespace_id=self.account.namespace.id,
                              name=self.canonical_name,
                              public_id=self.canonical_name)
                    db_session.add(tag)
                    return tag

        else:
            tag_name = self.name.lower()[:MAX_INDEXABLE_LENGTH]
            if tag_name in Tag.CANONICAL_TAG_NAMES:
                tag_name = 'imap/{}'.format(tag_name)
            try:
                # In looking for a non-canonical tag, we want to make sure we
                # don't return a canonical tag with the same name (e.g. a
                # user-created 'spam' or 'important' folder), so we exclude
                # tags with the public_id set to the tag name.
                return db_session.query(Tag). \
                    filter(Tag.namespace_id == self.namespace.id,
                           Tag.public_id != tag_name,
                           Tag.name == tag_name).one()
            except NoResultFound:
                # Explicitly set the namespace_id instead of the namespace
                # attribute to avoid autoflush-induced IntegrityErrors where
                # the namespace_id is null on flush.
                if create_if_missing:
                    tag = Tag(namespace_id=self.account.namespace.id,
                              name=tag_name)
                    db_session.add(tag)
                    return tag


class FolderItem(MailSyncBase):
    """ Mapping of threads to account backend folders.

    Used to provide a read-only copy of these backend folders/labels and,
    (potentially), to sync local datastore changes to these folders back to
    the IMAP/Exchange server.

    Note that a thread may appear in more than one folder, as may be the case
    with Gmail labels.
    """
    thread_id = Column(Integer, ForeignKey('thread.id', ondelete='CASCADE'),
                       nullable=False)
    # thread relationship is on Thread to make delete-orphan cascade work

    # Might be different from what we've synced from IMAP. (Local datastore
    # changes.)
    folder_id = Column(Integer, ForeignKey(Folder.id, ondelete='CASCADE'),
                       nullable=False)

    # We almost always need the folder name too, so eager load by default.
    folder = relationship(
        'Folder', uselist=False,
        backref=backref('threads',
                        # If associated folder is deleted, don't load child
                        # objects and let database-level cascade do its thing.
                        passive_deletes=True),
        lazy='joined')

    @property
    def account(self):
        return self.folder.account

    @property
    def namespace(self):
        return self.thread.namespace
