"""Tests for main backtest engine."""


import pytest

from strategy_lab.backtesting.engine import (
    BacktestEngine,
    BacktestStatus,
    ConfigTemplate,
)


class TestBacktestEngine:
    """Test BacktestEngine functionality."""

    def test_engine_initialization(self, tmp_path):
        """Test creating backtest engine."""
        engine = BacktestEngine(output_dir=tmp_path)

        assert engine.output_dir == tmp_path
        assert len(engine.jobs) == 0
        assert tmp_path.exists()

    def test_create_backtest_job(self, tmp_path):
        """Test creating a backtest job."""
        engine = BacktestEngine(output_dir=tmp_path)

        # Create config
        config = ConfigTemplate.default_config("TestStrategy", "test.strategy")
        config.data.data_path = tmp_path  # Use tmp_path to avoid validation error

        # Create job
        job_id = engine.create_backtest(config)

        assert job_id in engine.jobs
        assert engine.jobs[job_id].status == BacktestStatus.PENDING
        assert engine.jobs[job_id].config.strategy.name == "TestStrategy"

    def test_create_backtest_from_dict(self, tmp_path):
        """Test creating backtest from dictionary config."""
        engine = BacktestEngine(output_dir=tmp_path)

        # Create config dict
        config_dict = {
            "name": "Test",
            "strategy": {"name": "TestStrat", "module": "test.module"},
            "data": {"symbol": "MNQ", "data_path": str(tmp_path)},
            "execution": {"initial_capital": 50000},
        }

        # Create job
        job_id = engine.create_backtest(config_dict)

        assert job_id in engine.jobs
        assert engine.jobs[job_id].config.name == "Test"

    def test_job_status_tracking(self, tmp_path):
        """Test tracking job status."""
        engine = BacktestEngine(output_dir=tmp_path)

        # Create config
        config = ConfigTemplate.default_config("TestStrategy", "test.strategy")
        config.data.data_path = tmp_path

        # Create job
        job_id = engine.create_backtest(config)

        # Check status
        assert engine.get_job_status(job_id) == BacktestStatus.PENDING

        # Check invalid job
        with pytest.raises(ValueError, match="Job .* not found"):
            engine.get_job_status("invalid_job")

    def test_cancel_job(self, tmp_path):
        """Test cancelling a job."""
        engine = BacktestEngine(output_dir=tmp_path)

        # Create job
        config = ConfigTemplate.default_config("TestStrategy", "test.strategy")
        config.data.data_path = tmp_path
        job_id = engine.create_backtest(config)

        # Cancel job
        engine.cancel_job(job_id)
        assert engine.get_job_status(job_id) == BacktestStatus.CANCELLED

        # Try to cancel non-pending job
        with pytest.raises(ValueError, match="Can only cancel pending jobs"):
            engine.cancel_job(job_id)

    def test_list_jobs(self, tmp_path):
        """Test listing jobs."""
        engine = BacktestEngine(output_dir=tmp_path)

        # Create multiple jobs
        config = ConfigTemplate.default_config("TestStrategy", "test.strategy")
        config.data.data_path = tmp_path

        job1 = engine.create_backtest(config)
        job2 = engine.create_backtest(config)
        job3 = engine.create_backtest(config)

        # Cancel one job
        engine.cancel_job(job2)

        # List all jobs
        all_jobs = engine.list_jobs()
        assert len(all_jobs) == 3

        # List by status
        pending_jobs = engine.list_jobs(status=BacktestStatus.PENDING)
        assert len(pending_jobs) == 2
        assert job2 not in pending_jobs

        cancelled_jobs = engine.list_jobs(status=BacktestStatus.CANCELLED)
        assert len(cancelled_jobs) == 1
        assert job2 in cancelled_jobs

    def test_optimization_batch_creation(self, tmp_path):
        """Test creating optimization batch."""
        engine = BacktestEngine(output_dir=tmp_path)

        # Define parameter grid
        param_grid = {"threshold": [0.1, 0.2, 0.3], "lookback": [10, 20]}

        # Create batch
        job_ids = engine.create_optimization_batch(
            strategy_name="OptStrategy",
            strategy_module="test.opt",
            param_grid=param_grid,
        )

        # Should create 3 * 2 = 6 jobs
        assert len(job_ids) == 6

        # Check jobs created with different parameters
        params_seen = set()
        for job_id in job_ids:
            job = engine.jobs[job_id]
            params = job.config.strategy.parameters
            param_tuple = (params.get("threshold"), params.get("lookback"))
            params_seen.add(param_tuple)

        assert len(params_seen) == 6  # All combinations unique

    def test_get_best_result(self, tmp_path):
        """Test finding best result from jobs."""
        engine = BacktestEngine(output_dir=tmp_path)

        # Create some mock completed jobs
        from datetime import datetime

        from strategy_lab.backtesting.engine.results import BacktestResult

        config = ConfigTemplate.default_config("TestStrategy", "test.strategy")

        # Create jobs with different Sharpe ratios
        job_ids = []
        sharpe_ratios = [1.5, 2.0, 1.8, 0.5]

        for sharpe in sharpe_ratios:
            job_id = engine.create_backtest(config)
            job = engine.jobs[job_id]

            # Mock completion
            job.status = BacktestStatus.COMPLETED
            job.result = BacktestResult(
                config=config,
                start_time=datetime.now(),
                end_time=datetime.now(),
                sharpe_ratio=sharpe,
            )

            job_ids.append(job_id)

        # Find best by Sharpe ratio
        best_result = engine.get_best_result(job_ids, metric="sharpe_ratio")

        assert best_result is not None
        assert best_result.sharpe_ratio == 2.0

        # Test with no completed jobs
        pending_job = engine.create_backtest(config)
        assert engine.get_best_result([pending_job]) is None
