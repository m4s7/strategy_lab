#!/usr/bin/env python3
"""
Database seeding script for development.
"""

import asyncio
import uuid
from datetime import datetime, timedelta

from app.database.connection import async_session_factory
from app.database.operations import BacktestOperations, BacktestResultOperations
from app.database.models import BacktestCreate, BacktestResultCreate, BacktestStatus


async def seed_database():
    """Seed database with sample data."""
    print("Database Seeding Script")
    print("=" * 30)

    async with async_session_factory() as session:
        try:
            # Create sample backtests
            sample_strategies = [
                "Order Book Scalper",
                "Bid-Ask Bounce",
                "Volume Imbalance",
                "Mean Reversion",
                "Momentum Breakout",
            ]

            statuses = [
                BacktestStatus.COMPLETED,
                BacktestStatus.RUNNING,
                BacktestStatus.PENDING,
                BacktestStatus.FAILED,
            ]

            print(f"Creating {len(sample_strategies)} sample backtests...")

            created_backtests = []
            for i, strategy in enumerate(sample_strategies):
                # Create backtest
                backtest_data = BacktestCreate(
                    strategy_id=strategy.lower().replace(" ", "_"),
                    config={
                        "start_date": "2024-01-01",
                        "end_date": "2024-03-31",
                        "symbol": "MNQ",
                        "parameters": {
                            "fast_ma": 10 + (i * 2),
                            "slow_ma": 20 + (i * 5),
                            "stop_loss": 0.02 + (i * 0.001),
                            "take_profit": 0.04 + (i * 0.002),
                        },
                        "initial_capital": 100000,
                        "commission": 2.50,
                    },
                )

                backtest = await BacktestOperations.create_backtest(
                    session, backtest_data
                )

                # Update status and timing based on index
                status = statuses[i % len(statuses)]
                if status in [BacktestStatus.COMPLETED, BacktestStatus.FAILED]:
                    await BacktestOperations.update_backtest_status(
                        session, backtest.id, BacktestStatus.RUNNING
                    )
                    # Simulate completion
                    await BacktestOperations.update_backtest_status(
                        session,
                        backtest.id,
                        status,
                        error_message=f"Sample error for {strategy}"
                        if status == BacktestStatus.FAILED
                        else None,
                    )
                elif status == BacktestStatus.RUNNING:
                    await BacktestOperations.update_backtest_status(
                        session, backtest.id, status
                    )

                created_backtests.append((backtest, status))
                print(f"  ✓ Created: {strategy} ({status})")

            # Create sample results for completed backtests
            print("\nCreating sample backtest results...")
            for backtest, status in created_backtests:
                if status == BacktestStatus.COMPLETED:
                    result_data = BacktestResultCreate(
                        backtest_id=backtest.id,
                        metrics={
                            "total_return": round(
                                0.05 + (hash(backtest.id) % 100) / 1000, 4
                            ),
                            "sharpe_ratio": round(
                                1.2 + (hash(backtest.id) % 50) / 100, 2
                            ),
                            "max_drawdown": round(
                                -0.08 - (hash(backtest.id) % 30) / 1000, 4
                            ),
                            "win_rate": round(0.55 + (hash(backtest.id) % 30) / 100, 3),
                            "profit_factor": round(
                                1.3 + (hash(backtest.id) % 20) / 100, 2
                            ),
                            "avg_trade_duration": f"{2 + (hash(backtest.id) % 10)}m",
                            "total_trades": 150 + (hash(backtest.id) % 200),
                            "winning_trades": 85 + (hash(backtest.id) % 100),
                            "losing_trades": 65 + (hash(backtest.id) % 100),
                        },
                        trades_count=150 + (hash(backtest.id) % 200),
                    )

                    await BacktestResultOperations.create_result(session, result_data)
                    print(f"  ✓ Created results for: {backtest.strategy_id}")

            # Get final counts
            print("\nFinal database state:")
            from app.database.operations import DatabaseHealthOperations

            counts = await DatabaseHealthOperations.get_table_counts(session)
            for table, count in counts.items():
                print(f"  {table}: {count} records")

            print("\n✅ Database seeding completed successfully!")

        except Exception as e:
            print(f"\n❌ Seeding failed: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(seed_database())
