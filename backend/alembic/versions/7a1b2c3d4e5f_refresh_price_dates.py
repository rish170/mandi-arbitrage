"""refresh price dates to current

Revision ID: 7a1b2c3d4e5f
Revises: 6853b4ad5bae
Create Date: 2026-10-24 10:15:00.000000

"""
from typing import Sequence, Union
from datetime import date
from alembic import op
import sqlalchemy as sa

revision: str = '7a1b2c3d4e5f'
down_revision: Union[str, None] = '6853b4ad5bae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    
    # Check max arrival date in prices table
    res = bind.execute(sa.text("SELECT MAX(arrival_date) FROM prices")).scalar()
    if res:
        if isinstance(res, str):
            max_d = date.fromisoformat(res)
        else:
            max_d = res
        
        today = date.today()
        if max_d < today:
            diff_days = (today - max_d).days
            if dialect == 'postgresql':
                bind.execute(sa.text(f"UPDATE prices SET arrival_date = arrival_date + INTERVAL '{diff_days} days'"))
            elif dialect == 'sqlite':
                bind.execute(sa.text(f"UPDATE prices SET arrival_date = date(arrival_date, '+{diff_days} days')"))
            else:
                bind.execute(sa.text(f"UPDATE prices SET arrival_date = date(arrival_date, '+{diff_days} days')"))

def downgrade() -> None:
    pass
