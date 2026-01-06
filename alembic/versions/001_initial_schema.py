"""Initial schema for PiPool database

Revision ID: 001_initial
Revises:
Create Date: 2025-12-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema tables.

    Safe to run on existing databases - checks for table existence before creating.
    """
    # Check if tables exist by querying information_schema
    conn = op.get_bind()

    # Create device_runtime table if not exists
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'device_runtime')"
    ))
    if not result.scalar():
        op.create_table(
            'device_runtime',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('topic', sa.String(), nullable=True),
            sa.Column('start_time', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
            sa.Column('elapsed_seconds', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )

    # Create sensor table if not exists
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'sensor')"
    ))
    if not result.scalar():
        op.create_table(
            'sensor',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('sensor', sa.String(), nullable=True),
            sa.Column('reading', sa.Float(), nullable=True),
            sa.Column('time', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # Create event table if not exists
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'event')"
    ))
    if not result.scalar():
        op.create_table(
            'event',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('state_from', sa.String(), nullable=True),
            sa.Column('state_to', sa.String(), nullable=True),
            sa.Column('opaque', sa.String(), nullable=True),
            sa.Column('time', sa.DateTime(), server_default=sa.text('NOW()'), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    """Drop all tables (destructive operation)."""
    op.drop_table('event')
    op.drop_table('sensor')
    op.drop_table('device_runtime')
