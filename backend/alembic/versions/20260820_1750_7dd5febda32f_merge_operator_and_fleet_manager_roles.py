"""merge_operator_and_fleet_manager_roles

Revision ID: 7dd5febda32f
Revises: 0d0bb33da7ac
Create Date: 2026-08-20 17:50:30.132180+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7dd5febda32f'
down_revision: Union[str, None] = '0d0bb33da7ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()

    # 1. Rename or merge table fleet_manager_profiles to fleet_operator_profiles
    if 'fleet_manager_profiles' in tables:
        if 'fleet_operator_profiles' not in tables:
            op.rename_table('fleet_manager_profiles', 'fleet_operator_profiles')
        else:
            op.execute(
                "INSERT INTO fleet_operator_profiles (id, user_id, managed_fleet_size, region, created_at, updated_at) "
                "SELECT id, user_id, managed_fleet_size, region, created_at, updated_at FROM fleet_manager_profiles "
                "ON CONFLICT (user_id) DO NOTHING"
            )
            op.drop_table('fleet_manager_profiles')

    # 2. Update user roles to 'fleet_operator'
    op.execute("UPDATE users SET role = 'fleet_operator' WHERE role IN ('operator', 'fleet_manager')")

    # 3. Generate profile records for any users that don't have one
    import uuid
    from datetime import datetime, timezone
    
    # Query users that have 'fleet_operator' role but do not have a profile in fleet_operator_profiles
    users = connection.execute(
        sa.text("SELECT id FROM users WHERE role = 'fleet_operator' AND id NOT IN (SELECT user_id FROM fleet_operator_profiles)")
    ).fetchall()

    for row in users:
        u_id = row[0]
        p_id = str(uuid.uuid4())
        connection.execute(
            sa.text(
                "INSERT INTO fleet_operator_profiles (id, user_id, managed_fleet_size, region, created_at, updated_at) "
                "VALUES (:id, :user_id, 0, 'National', :now, :now)"
            ),
            {"id": p_id, "user_id": str(u_id), "now": datetime.now(timezone.utc)}
        )


def downgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = inspector.get_table_names()

    # Rename back if table exists
    if 'fleet_operator_profiles' in tables and 'fleet_manager_profiles' not in tables:
        op.rename_table('fleet_operator_profiles', 'fleet_manager_profiles')
    op.execute("UPDATE users SET role = 'fleet_manager' WHERE role = 'fleet_operator'")
