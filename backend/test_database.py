#!/usr/bin/env python3
"""
Database test script to verify CRUD operations.
"""

import asyncio
import json
from datetime import datetime

from app.database.connection import async_session_factory
from app.database.operations import BacktestOperations, DatabaseHealthOperations
from app.database.models import BacktestCreate, BacktestStatus


async def test_database_operations():
    """Test database operations."""
    print("Database Operations Test")
    print("=" * 40)

    async with async_session_factory() as session:
        try:
            # Test database health
            print("1. Testing database connection...")
            connected = await DatabaseHealthOperations.check_connection(session)
            print(f"   Database connected: {connected}")

            if not connected:
                print("   Database not connected, aborting tests")
                return

            # Test table counts
            print("\n2. Getting table counts...")
            counts = await DatabaseHealthOperations.get_table_counts(session)
            print(f"   Table counts: {json.dumps(counts, indent=2)}")

            # Test creating a backtest
            print("\n3. Creating a test backtest...")
            backtest_data = BacktestCreate(
                strategy_id="test_strategy",
                config={
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "symbol": "MNQ",
                    "parameters": {"fast_ma": 10, "slow_ma": 20},
                },
            )

            backtest = await BacktestOperations.create_backtest(session, backtest_data)
            print(f"   Created backtest: {backtest.id}")
            print(f"   Status: {backtest.status}")
            print(f"   Created at: {backtest.created_at}")

            # Test getting backtest
            print("\n4. Retrieving backtest...")
            retrieved = await BacktestOperations.get_backtest(session, backtest.id)
            print(f"   Retrieved backtest: {retrieved.id}")
            print(f"   Strategy ID: {retrieved.strategy_id}")

            # Test updating backtest status
            print("\n5. Updating backtest status...")
            updated = await BacktestOperations.update_backtest_status(
                session, backtest.id, BacktestStatus.RUNNING
            )
            print(f"   Updated status: {updated.status}")
            print(f"   Started at: {updated.started_at}")

            # Test getting list of backtests
            print("\n6. Getting list of backtests...")
            backtests = await BacktestOperations.get_backtests(session, limit=10)
            print(f"   Found {len(backtests)} backtests")
            for bt in backtests:
                print(f"   - {bt.id}: {bt.strategy_id} ({bt.status})")

            # Test recent activity
            print("\n7. Getting recent activity...")
            activity = await DatabaseHealthOperations.get_recent_activity(
                session, limit=5
            )
            print(
                f"   Recent activity: {len(activity.get('recent_backtests', []))} items"
            )

            # Final table counts
            print("\n8. Final table counts...")
            final_counts = await DatabaseHealthOperations.get_table_counts(session)
            print(f"   Final counts: {json.dumps(final_counts, indent=2)}")

            print("\n✅ All database tests completed successfully!")

        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_database_operations())
