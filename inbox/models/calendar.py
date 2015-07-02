from sqlalchemy import (Column, String, Text, Boolean,
                        UniqueConstraint, ForeignKey, DateTime)
from sqlalchemy.orm import relationship

from inbox.models.base import MailSyncBase
from inbox.models.namespace import Namespace

from inbox.models.mixins import HasPublicID, HasRevisions


class Calendar(MailSyncBase, HasPublicID, HasRevisions):
    API_OBJECT_NAME = 'calendar'
    namespace_id = Column(ForeignKey(Namespace.id, ondelete='CASCADE'),
                          nullable=False)

    namespace = relationship(Namespace, load_on_pending=True)

    name = Column(String(128), nullable=True)
    provider_name = Column(String(128), nullable=True, default='DEPRECATED')
    description = Column(Text, nullable=True)

    # A server-provided unique ID.
    uid = Column(String(767, collation='ascii_general_ci'), nullable=False)

    read_only = Column(Boolean, nullable=False, default=False)

    last_synced = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint('namespace_id', 'provider_name',
                                       'name', 'uid', name='uuid'),)

    def update(self, calendar):
        self.uid = calendar.uid
        self.name = calendar.name
        self.read_only = calendar.read_only
        self.description = calendar.description
