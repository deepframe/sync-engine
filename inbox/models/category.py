from sqlalchemy import Column, String, Integer, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from inbox.models.base import MailSyncBase
from inbox.models.mixins import HasRevisions, HasPublicID
from inbox.models.constants import MAX_INDEXABLE_LENGTH
from inbox.sqlalchemy_ext.util import generate_public_id
from inbox.log import get_logger
log = get_logger()


class Category(MailSyncBase, HasRevisions, HasPublicID):
    @property
    def API_OBJECT_NAME(self):
        return self.type_

    # Need `use_alter` here to avoid circular dependencies
    namespace_id = Column(Integer,
                          ForeignKey('namespace.id', use_alter=True,
                                     name='category_fk1',
                                     ondelete='CASCADE'), nullable=False)
    namespace = relationship('Namespace', load_on_pending=True)

    #public_id = Column(String(MAX_INDEXABLE_LENGTH), nullable=False,
    #                   default=generate_public_id, index=True)

    # STOPSHIP(emfree): need to index properly for API filtering performance.
    name = Column(String(MAX_INDEXABLE_LENGTH), nullable=True)
    display_name = Column(String(MAX_INDEXABLE_LENGTH,
                                 collation='utf8mb4_bin'), nullable=False)

    type_ = Column(Enum('folder', 'label'), nullable=False, default='folder')

    @classmethod
    def find_or_create(cls, session, namespace_id, name, display_name, type_):
        try:
            obj = session.query(cls).filter(
                cls.namespace_id == namespace_id,
                cls.name == name,
                cls.display_name == display_name).one()
        except NoResultFound:
            obj = cls(namespace_id=namespace_id, name=name,
                      display_name=display_name, type_=type_)
            session.add(obj)
        except MultipleResultsFound:
            log.error('Duplicate category rows for namespace_id {}, '
                      'name {}, display_name: {}'.
                      format(namespace_id, name, display_name))
            raise

        return obj

    @property
    def account(self):
        return self.namespace.account

    @property
    def type(self):
        return self.account.category_type

    __table_args__ = (UniqueConstraint('namespace_id', 'name', 'display_name'),
                      UniqueConstraint('namespace_id', 'public_id'))
