"""outbox

Revision ID: 418d02fbee4a
Revises: 982fda178dca
Create Date: 2026-03-31 11:57:28.197032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '418d02fbee4a'
down_revision: Union[str, Sequence[str], None] = '982fda178dca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'outbox',
        sa.Column('event_type', sa.Enum('PAYMENT_NEW', name='event_type'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SENT', name='outbox_status_enum'), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('outbox')
