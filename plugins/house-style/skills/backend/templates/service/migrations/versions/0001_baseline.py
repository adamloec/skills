"""Baseline — create the service's tables from the live models.

Every later revision is existence-guarded against this one, so a database built by the baseline
and one migrated step by step converge on the same schema.
"""

from collections.abc import Sequence

from alembic import op
from sqlmodel import SQLModel

from {{pkg}}.models.note import Note

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create every owned table that does not exist yet."""
    SQLModel.metadata.create_all(op.get_bind(), tables=[Note.__table__], checkfirst=True)


def downgrade() -> None:
    """Drop every owned table."""
    op.drop_table("notes")
