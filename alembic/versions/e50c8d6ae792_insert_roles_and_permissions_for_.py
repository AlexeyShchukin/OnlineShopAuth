"""insert roles and permissions for addresses

Revision ID: e50c8d6ae792
Revises: d7c640485c92
Create Date: 2025-06-15 11:28:39.541592

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e50c8d6ae792'
down_revision: Union[str, None] = 'd7c640485c92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("""
        INSERT INTO permissions (name, description) VALUES
        ('address:create:own', 'Allows to create own address'),
        ('address:create:any', 'Allows to create any address'),
        ('address:read:own', 'Allows to read own address'),
        ('address:read:any', 'Allows to read any address'),
        ('address:update:own', 'Allows to update own address'),
        ('address:update:any', 'Allows to update any address'),
        ('address:delete:own', 'Allows to delete own address'),
        ('address:delete:any', 'Allows to delete any address')
    """)


def downgrade():
    op.execute("""
        DELETE FROM permissions WHERE name IN (
            'address:create:own',
            'address:create:any',
            'address:read:own',
            'address:read:any',
            'address:update:own',
            'address:update:any',
            'address:delete:own',
            'address:delete:any'
        )
    """)
