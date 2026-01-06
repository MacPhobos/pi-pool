"""Convert event.opaque column from varchar to jsonb

Revision ID: 002_opaque_json
Revises: 001_initial
Create Date: 2025-12-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '002_opaque_json'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert opaque column from varchar to jsonb.

    This allows storing Python dicts directly without manual JSON serialization.
    Existing varchar values will be cast to jsonb (nulls and simple strings work).
    """
    # Check if column exists and is varchar
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT data_type
        FROM information_schema.columns
        WHERE table_name = 'event'
        AND column_name = 'opaque'
    """))

    row = result.fetchone()
    if row and row[0] in ('character varying', 'varchar', 'text'):
        # Convert varchar to jsonb using USING clause for safe casting
        # Simple strings and NULLs will cast correctly
        op.execute("""
            ALTER TABLE event
            ALTER COLUMN opaque TYPE jsonb
            USING CASE
                WHEN opaque IS NULL THEN NULL
                WHEN opaque = '' THEN NULL
                ELSE opaque::jsonb
            END
        """)


def downgrade() -> None:
    """Convert opaque column back from jsonb to varchar.

    JSON data will be serialized to text representation.
    """
    # Convert jsonb back to varchar
    op.execute("""
        ALTER TABLE event
        ALTER COLUMN opaque TYPE varchar
        USING opaque::text
    """)
