"""Add performance indexes

Revision ID: 66b9d6348fb2
Revises: c04e9f1de405
Create Date: 2025-08-07 08:48:37.747779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66b9d6348fb2'
down_revision: Union[str, Sequence[str], None] = 'c04e9f1de405'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes."""
    op.create_index('idx_backtests_status', 'backtests', ['status'])
    op.create_index('idx_backtests_created_desc', 'backtests', ['created_at'])
    op.create_index('idx_backtests_strategy', 'backtests', ['strategy_id'])
    op.create_index('idx_results_backtest', 'backtest_results', ['backtest_id'])
    op.create_index('idx_optimization_status', 'optimization_jobs', ['status'])


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index('idx_optimization_status', 'optimization_jobs')
    op.drop_index('idx_results_backtest', 'backtest_results')
    op.drop_index('idx_backtests_strategy', 'backtests')
    op.drop_index('idx_backtests_created_desc', 'backtests')
    op.drop_index('idx_backtests_status', 'backtests')
