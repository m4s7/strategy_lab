"""Tests for backtest results management."""

from datetime import datetime

import pandas as pd

from strategy_lab.backtesting.engine.config import ConfigTemplate
from strategy_lab.backtesting.engine.results import (
    BacktestResult,
    TradeRecord,
    load_results,
    query_results,
    save_results,
)


class TestTradeRecord:
    """Test TradeRecord functionality."""

    def test_trade_record_creation(self):
        """Test creating a trade record."""
        trade = TradeRecord(
            symbol="MNQ",
            side="BUY",
            entry_time=pd.Timestamp("2024-01-01 10:00:00"),
            entry_price=100.0,
            exit_time=pd.Timestamp("2024-01-01 11:00:00"),
            exit_price=105.0,
            quantity=10,
            pnl=48.0,
            commission=2.0,
        )

        assert trade.symbol == "MNQ"
        assert trade.side == "BUY"
        assert trade.pnl == 48.0

    def test_trade_record_to_dict(self):
        """Test converting trade record to dict."""
        trade = TradeRecord(
            symbol="MNQ",
            side="SELL",
            entry_time=pd.Timestamp("2024-01-01 10:00:00"),
            entry_price=100.0,
            exit_time=pd.Timestamp("2024-01-01 11:00:00"),
            exit_price=95.0,
            quantity=10,
            pnl=48.0,
            commission=2.0,
        )

        trade_dict = trade.to_dict()

        assert isinstance(trade_dict, dict)
        assert trade_dict["symbol"] == "MNQ"
        assert trade_dict["side"] == "SELL"
        assert "entry_time" in trade_dict
        assert isinstance(trade_dict["entry_time"], str)


class TestBacktestResult:
    """Test BacktestResult functionality."""

    def create_test_result(self):
        """Create a test backtest result."""
        config = ConfigTemplate.default_config("TestStrategy", "test.strategy")

        return BacktestResult(
            config=config,
            start_time=datetime(2024, 1, 1, 9, 0),
            end_time=datetime(2024, 1, 1, 16, 0),
            total_pnl=500.0,
            total_trades=10,
            winning_trades=6,
            losing_trades=4,
            win_rate=60.0,
            profit_factor=2.5,
            max_drawdown=0.05,
            sharpe_ratio=1.8,
            total_ticks=100000,
            execution_time=10.5,
        )

    def test_result_creation(self):
        """Test creating backtest result."""
        result = self.create_test_result()

        assert result.total_pnl == 500.0
        assert result.win_rate == 60.0
        assert result.sharpe_ratio == 1.8
        assert result.backtest_id is not None

    def test_result_properties(self):
        """Test result calculated properties."""
        result = self.create_test_result()

        # Duration
        assert result.duration == 7 * 3600  # 7 hours in seconds

        # Processing speed
        expected_speed = 100000 / 10.5
        assert abs(result.ticks_per_second - expected_speed) < 1

    def test_result_to_dict(self):
        """Test converting result to dict."""
        result = self.create_test_result()

        # Add some trades
        result.trades = [
            TradeRecord(
                symbol="MNQ",
                side="BUY",
                entry_time=pd.Timestamp("2024-01-01 10:00:00"),
                entry_price=100.0,
                exit_time=pd.Timestamp("2024-01-01 11:00:00"),
                exit_price=105.0,
                quantity=1,
                pnl=5.0,
                commission=0.5,
            )
        ]

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["backtest_id"] == result.backtest_id
        assert "config" in result_dict
        assert "performance" in result_dict
        assert result_dict["performance"]["total_pnl"] == 500.0
        assert "risk" in result_dict
        assert result_dict["risk"]["sharpe_ratio"] == 1.8

    def test_result_summary(self):
        """Test getting result summary."""
        result = self.create_test_result()

        summary = result.get_summary()

        assert isinstance(summary, str)
        assert "Backtest Results Summary" in summary
        assert "TestStrategy" in summary
        assert "Total P&L: $500.00" in summary
        assert "Sharpe Ratio: 1.80" in summary


class TestResultsPersistence:
    """Test saving and loading results."""

    def test_save_results(self, tmp_path):
        """Test saving backtest results."""
        # Create result
        config = ConfigTemplate.default_config("TestStrategy", "test.strategy")
        config.output_dir = tmp_path

        result = BacktestResult(
            config=config,
            start_time=datetime(2024, 1, 1, 9, 0),
            end_time=datetime(2024, 1, 1, 16, 0),
            total_pnl=1000.0,
            total_trades=20,
            winning_trades=12,
            losing_trades=8,
            win_rate=60.0,
        )

        # Add some data
        result.trades = [
            TradeRecord(
                symbol="MNQ",
                side="BUY",
                entry_time=pd.Timestamp("2024-01-01 10:00:00"),
                entry_price=100.0,
                exit_time=pd.Timestamp("2024-01-01 11:00:00"),
                exit_price=105.0,
                quantity=1,
                pnl=5.0,
                commission=0.5,
            )
        ]

        result.equity_curve = [100000, 100500, 101000]
        result.timestamps = [
            pd.Timestamp("2024-01-01 09:00:00"),
            pd.Timestamp("2024-01-01 10:00:00"),
            pd.Timestamp("2024-01-01 11:00:00"),
        ]

        # Save results
        result_dir = save_results(result, tmp_path)

        # Check files created
        assert result_dir.exists()
        assert (result_dir / "metadata.json").exists()
        assert (result_dir / "trades.parquet").exists()
        assert (result_dir / "equity_curve.parquet").exists()
        assert (result_dir / "summary.txt").exists()

    def test_load_results(self, tmp_path):
        """Test loading saved results."""
        # First save a result
        config = ConfigTemplate.default_config("TestStrategy", "test.strategy")
        config.output_dir = tmp_path

        original = BacktestResult(
            config=config,
            start_time=datetime(2024, 1, 1, 9, 0),
            end_time=datetime(2024, 1, 1, 16, 0),
            backtest_id="test_12345",
            total_pnl=1000.0,
            sharpe_ratio=2.0,
        )

        result_dir = save_results(original, tmp_path)

        # Load it back
        loaded = load_results(result_dir)

        assert loaded.backtest_id == original.backtest_id
        assert loaded.total_pnl == original.total_pnl
        assert loaded.sharpe_ratio == original.sharpe_ratio
        assert loaded.config.strategy.name == original.config.strategy.name

    def test_query_results(self, tmp_path):
        """Test querying saved results."""
        # Save multiple results
        configs = [
            ConfigTemplate.default_config("Strategy1", "test.strategy1"),
            ConfigTemplate.default_config("Strategy2", "test.strategy2"),
            ConfigTemplate.default_config("Strategy1", "test.strategy1"),
        ]

        for i, config in enumerate(configs):
            config.output_dir = tmp_path

            result = BacktestResult(
                config=config,
                start_time=datetime(2024, 1, i + 1, 9, 0),
                end_time=datetime(2024, 1, i + 1, 16, 0),
                backtest_id=f"test_{i}",
                sharpe_ratio=float(i),
            )

            save_results(result, tmp_path)

        # Query all results
        all_results = query_results(tmp_path)
        assert len(all_results) == 3

        # Query by strategy name
        strategy1_results = query_results(tmp_path, strategy_name="Strategy1")
        assert len(strategy1_results) == 2

        # Query by Sharpe ratio
        good_results = query_results(tmp_path, min_sharpe=1.5)
        assert len(good_results) == 1
        assert good_results[0].sharpe_ratio == 2.0

    def test_save_without_optional_data(self, tmp_path):
        """Test saving results without trades or equity curve."""
        config = ConfigTemplate.default_config("TestStrategy", "test.strategy")
        config.output_dir = tmp_path
        config.save_trades = False
        config.save_equity_curve = False

        result = BacktestResult(
            config=config,
            start_time=datetime.now(),
            end_time=datetime.now(),
            total_pnl=100.0,
        )

        # Add data that shouldn't be saved
        result.trades = [
            TradeRecord(
                symbol="MNQ",
                side="BUY",
                entry_time=pd.Timestamp.now(),
                entry_price=100.0,
                exit_time=pd.Timestamp.now(),
                exit_price=105.0,
                quantity=1,
                pnl=5.0,
                commission=0.5,
            )
        ]
        result.equity_curve = [100000, 100100]

        # Save
        result_dir = save_results(result, tmp_path)

        # Check files NOT created
        assert (result_dir / "metadata.json").exists()
        assert not (result_dir / "trades.parquet").exists()
        assert not (result_dir / "equity_curve.parquet").exists()
