from sqlalchemy import Column, Integer, Enum, ForeignKey
from sqlalchemy.orm import relationship, backref

from inbox.models.base import MailSyncBase
from inbox.models.mixins import HasPublicID


class Namespace(MailSyncBase, HasPublicID):
    """ A way to do grouping / permissions, basically. """
    # NOTE: only root namespaces have account backends
    account_id = Column(Integer,
                        ForeignKey('account.id', ondelete='CASCADE'),
                        nullable=True)
    # really the root_namespace
    account = relationship('Account',
                           lazy='joined',
                           single_parent=True,
                           backref=backref('namespace',
                                           uselist=False,
                                           lazy='joined',
                                           passive_deletes=True,
                                           cascade='all,delete-orphan'),
                           uselist=False)

    # invariant: imapaccount is non-null iff type is root
    type = Column(Enum('root', 'shared_folder'), nullable=False,
                  server_default='root')

    @property
    def email_address(self):
        if self.account is not None:
            return self.account.email_address
