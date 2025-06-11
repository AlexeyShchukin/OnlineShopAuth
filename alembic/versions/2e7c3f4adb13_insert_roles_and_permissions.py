"""insert roles and permissions

Revision ID: 2e7c3f4adb13
Revises: 647bb39177dc
Create Date: 2025-06-07 18:53:52.437665

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2e7c3f4adb13'
down_revision: Union[str, None] = '647bb39177dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():

    op.execute("""
        INSERT INTO permissions (name, description) VALUES
        ('product:create:own', 'Allows to create own product'),
        ('product:create:any', 'Allows to create any product'),
        ('product:read:own', 'Allows to read own product'),
        ('product:read:any', 'Allows to read any product'),
        ('product:update:own', 'Allows to update own product'),
        ('product:update:any', 'Allows to update any product'),
        ('product:delete:own', 'Allows to delete own product'),
        ('product:delete:any', 'Allows to delete any product'),

        ('order:create:own', 'Allows to create own order'),
        ('order:create:any', 'Allows to create any order'),
        ('order:read:own', 'Allows to read own order'),
        ('order:read:any', 'Allows to read any order'),
        ('order:update:own', 'Allows to update own order'),
        ('order:update:any', 'Allows to update any order'),
        ('order:delete:own', 'Allows to delete own order'),
        ('order:delete:any', 'Allows to delete any order'),

        ('user:read:own', 'Allows to read own user'),
        ('user:read:any', 'Allows to read any user'),
        ('user:update:own', 'Allows to update own user'),
        ('user:update:any', 'Allows to update any user'),
        ('user:delete:own', 'Allows to delete own user'),
        ('user:delete:any', 'Allows to delete any user'),

        ('cart:create:own', 'Allows to create own cart'),
        ('cart:create:any', 'Allows to create any cart'),
        ('cart:read:own', 'Allows to read own cart'),
        ('cart:read:any', 'Allows to read any cart'),
        ('cart:update:own', 'Allows to update own cart'),
        ('cart:update:any', 'Allows to update any cart'),
        ('cart:delete:own', 'Allows to delete own cart'),
        ('cart:delete:any', 'Allows to delete any cart'),

        ('category:create:own', 'Allows to create own category'),
        ('category:create:any', 'Allows to create any category'),
        ('category:read:own', 'Allows to read own category'),
        ('category:read:any', 'Allows to read any category'),
        ('category:update:own', 'Allows to update own category'),
        ('category:update:any', 'Allows to update any category'),
        ('category:delete:own', 'Allows to delete own category'),
        ('category:delete:any', 'Allows to delete any category'),

        ('payment:read:own', 'Allows to read own payment'),
        ('payment:read:any', 'Allows to read any payment'),
        ('payment:update:own', 'Allows to update own payment'),
        ('payment:update:any', 'Allows to update any payment'),

        ('shipment:read:own', 'Allows to read own shipment'),
        ('shipment:read:any', 'Allows to read any shipment'),
        ('shipment:update:own', 'Allows to update own shipment'),
        ('shipment:update:any', 'Allows to update any shipment'),

        ('review:create:own', 'Allows to create own review'),
        ('review:create:any', 'Allows to create any review'),
        ('review:read:own', 'Allows to read own review'),
        ('review:read:any', 'Allows to read any review'),
        ('review:update:own', 'Allows to update own review'),
        ('review:update:any', 'Allows to update any review'),
        ('review:delete:own', 'Allows to delete own review'),
        ('review:delete:any', 'Allows to delete any review'),

        ('wishlist:create:own', 'Allows to create own wishlist'),
        ('wishlist:create:any', 'Allows to create any wishlist'),
        ('wishlist:read:own', 'Allows to read own wishlist'),
        ('wishlist:read:any', 'Allows to read any wishlist'),
        ('wishlist:delete:own', 'Allows to delete own wishlist'),
        ('wishlist:delete:any', 'Allows to delete any wishlist'),

        ('role:read:own', 'Allows to read own role'),
        ('role:read:any', 'Allows to read any role'),
        ('role:update:own', 'Allows to update own role'),
        ('role:update:any', 'Allows to update any role')
    """)

    op.execute("""
        INSERT INTO roles (name, description) VALUES
        ('admin', 'Administrator with full access'),
        ('moderator', 'Moderator with management permissions'),
        ('customer', 'Regular customer')
    """)


def downgrade():
    op.execute("DELETE FROM roles WHERE name IN ('admin', 'moderator', 'customer')")
    op.execute("DELETE FROM permissions WHERE name LIKE '%:%:%'")
