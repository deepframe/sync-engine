"""MAD-1100 - table message - add indexes on fields reply_to_message_id and thread_id

Revision ID: 3999dc24642d
Revises: 731019fd024
Create Date: 2018-07-10 19:59:41.517156

"""

# revision identifiers, used by Alembic.
revision = '3999dc24642d'
down_revision = '731019fd024'

from alembic import op
from sqlalchemy.sql import text


def upgrade():
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE message "
                      " ADD INDEX ix_message_reply_to_message_id(reply_to_message_id), "
                      " ADD INDEX ix_message_thread_id(thread_id)"))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("ALTER TABLE message "
                      " DROP INDEX ix_message_reply_to_message_id, "
                      " DROP INDEX ix_message_thread_id"))