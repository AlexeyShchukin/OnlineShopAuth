"""insert role-permission relationship

Revision ID: d7c640485c92
Revises: 2e7c3f4adb13
Create Date: 2025-06-07 19:46:10.192348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd7c640485c92'
down_revision: Union[str, None] = '2e7c3f4adb13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    INSERT INTO roles_permissions (role_id, permission_id)
    SELECT roles.id, permissions.id
    FROM roles, permissions
    WHERE roles.name = 'admin' AND permissions.name LIKE '%any'
    """)

    op.execute("""
            INSERT INTO roles_permissions (role_id, permission_id)
            SELECT roles.id, permissions.id
            FROM roles, permissions
            WHERE roles.name = 'moderator'
              AND (permissions.name LIKE 'product:%any'
              OR permissions.name LIKE 'order:%any'
              OR permissions.name LIKE 'category:%any'
              OR permissions.name LIKE 'review:%any')
        """)

    op.execute("""
            INSERT INTO roles_permissions (role_id, permission_id)
            SELECT roles.id, permissions.id
            FROM roles, permissions
            WHERE roles.name = 'customer'
              AND (permissions.name = 'product:read:any'
               OR permissions.name LIKE 'cart:%own'
               OR permissions.name LIKE 'wishlist:%own'
               OR permissions.name LIKE 'order:%own'
               OR permissions.name LIKE 'review:%own'
               OR permissions.name = 'review:read:any'
               OR permissions.name = 'user:read:own'
               OR permissions.name = 'user:update:own'
               OR permissions.name = 'user:delete:own'
               OR permissions.name = 'role:read:own'
               OR permissions.name = 'shipment:read:own'
               OR permissions.name = 'shipment:update:own')
        """)


def downgrade() -> None:
    op.execute("""
            DELETE FROM roles_permissions
            WHERE role_id IN (
                SELECT id FROM roles WHERE name IN ('admin', 'moderator', 'customer')
            )
            AND permission_id IN (
                SELECT id FROM permissions
                WHERE name LIKE '%:own' OR name LIKE '%any'
            )
        """)
