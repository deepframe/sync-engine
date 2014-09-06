""" Revert encryption

Revision ID: 2c577a8a01b7
Revises: 2b89164aa9cd
Create Date: 2014-09-06 03:24:54.292086

"""

# revision identifiers, used by Alembic.
revision = '2c577a8a01b7'
down_revision = '24e9afe91349'#31dc0411eecf'


from alembic import op
import sqlalchemy as sa

import nacl.secret
import nacl.utils


def upgrade():
    print '\nUpgrading...'

    # Block table
    #op.drop_column('block', 'encryption_scheme')

    print '\nDone with Block table'

    # Secret table
    op.add_column('secret', sa.Column('acl_id', sa.Integer(), nullable=False))

    op.alter_column('secret', 'type', type_=sa.Integer(),
                    existing_server_default=None,
                    existing_nullable=False)

    op.add_column('secret',
                  sa.Column('secret', sa.String(length=512), nullable=True))

    print '\nDone with Secret table, now migrating data'

    from inbox.ignition import main_engine
    from inbox.models.session import session_scope
    from inbox.config import config

    engine = main_engine(pool_size=1, max_overflow=0)
    Base = sa.ext.declarative.declarative_base()
    Base.metadata.reflect(engine)
        
    key = config.get_required('SECRET_ENCRYPTION_KEY')
    print '\nkey: ', key

    class Secret(Base):
        __table__ = Base.metadata.tables['secret']

    with session_scope(ignore_soft_deletes=False, versioned=False) as \
            db_session:
        secrets = db_session.query(Secret).filter(
            Secret.encryption_scheme == 1,
            Secret._secret.isnot(None)).order_by(Secret.id).all()
        
        for s in secrets:
            encrypted = s._secret

            s.secret = nacl.secret.SecretBox(
                key=key,
                encoder=nacl.encoding.HexEncoder
            ).decrypt(encrypted)

            # Picked arbitrarily
            s.acl_id = 0
            s.type = 0

            db_session.add(s)
            print '\ns.id: ', s.id
            
        db_session.commit()

    op.drop_column('secret', '_secret')
    op.drop_column('secret', 'encryption_scheme')


def downgrade():
    pass
