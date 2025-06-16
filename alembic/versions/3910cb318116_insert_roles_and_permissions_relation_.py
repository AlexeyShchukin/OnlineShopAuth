"""insert roles and permissions relation for addresses

Revision ID: 3910cb318116
Revises: e50c8d6ae792
Create Date: 2025-06-15 13:19:14.092049

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3910cb318116'
down_revision: Union[str, None] = 'e50c8d6ae792'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
            INSERT INTO roles_permissions (role_id, permission_id)
            SELECT roles.id, permissions.id
            FROM roles, permissions
            WHERE roles.name = 'admin'
              AND permissions.name LIKE 'address%any'
        """)

    op.execute("""
        INSERT INTO roles_permissions (role_id, permission_id)
        SELECT roles.id, permissions.id
        FROM roles, permissions
        WHERE roles.name = 'moderator'
          AND permissions.name LIKE 'address%any'
    """)

    op.execute("""
        INSERT INTO roles_permissions (role_id, permission_id)
        SELECT roles.id, permissions.id
        FROM roles, permissions
        WHERE roles.name = 'customer'
          AND permissions.name LIKE 'address%own'
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM roles_permissions
        WHERE role_id IN (
            SELECT id FROM roles WHERE name IN ('admin', 'moderator', 'customer')
        )
        AND permission_id IN (
            SELECT id FROM permissions
            WHERE name LIKE 'address%own' OR name LIKE 'address%any'
        )
    """)
