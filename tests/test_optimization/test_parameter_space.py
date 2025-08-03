"""Tests for parameter space definitions."""

import pytest

from strategy_lab.optimization.core.parameter_space import (
    CategoricalParameter,
    ContinuousParameter,
    DiscreteParameter,
    ParameterSpace,
)


class TestContinuousParameter:
    """Test ContinuousParameter class."""

    def test_basic_continuous(self):
        """Test basic continuous parameter."""
        param = ContinuousParameter(
            name="threshold", min_value=0.1, max_value=0.9, step=0.1
        )

        values = param.get_values()
        assert len(values) == 9
        assert values[0] == 0.1
        assert values[-1] == 0.9
        assert all(
            abs(values[i + 1] - values[i] - 0.1) < 1e-10 for i in range(len(values) - 1)
        )

    def test_continuous_no_endpoint(self):
        """Test continuous parameter without endpoint."""
        param = ContinuousParameter(
            name="alpha",
            min_value=0.0,
            max_value=1.0,
            step=0.25,
            include_endpoint=False,
        )

        values = param.get_values()
        assert len(values) == 4
        assert 1.0 not in values

    def test_validation(self):
        """Test parameter validation."""
        param = ContinuousParameter("test", 0.0, 1.0, 0.1)

        assert param.validate(0.5) is True
        assert param.validate(0.0) is True
        assert param.validate(1.0) is True
        assert param.validate(1.1) is False
        assert param.validate(-0.1) is False
        assert param.validate("string") is False

    def test_invalid_range(self):
        """Test invalid parameter range."""
        with pytest.raises(ValueError):
            ContinuousParameter("test", 1.0, 0.0, 0.1)

        with pytest.raises(ValueError):
            ContinuousParameter("test", 0.0, 1.0, -0.1)


class TestDiscreteParameter:
    """Test DiscreteParameter class."""

    def test_basic_discrete(self):
        """Test basic discrete parameter."""
        param = DiscreteParameter(
            name="position_size", min_value=1, max_value=10, step=1
        )

        values = param.get_values()
        assert len(values) == 10
        assert values == list(range(1, 11))

    def test_discrete_with_step(self):
        """Test discrete parameter with custom step."""
        param = DiscreteParameter(name="lookback", min_value=10, max_value=50, step=5)

        values = param.get_values()
        assert values == [10, 15, 20, 25, 30, 35, 40, 45, 50]

    def test_validation(self):
        """Test parameter validation."""
        param = DiscreteParameter("test", 0, 10, 2)

        assert param.validate(0) is True
        assert param.validate(2) is True
        assert param.validate(10) is True
        assert param.validate(1) is False  # Not on step
        assert param.validate(11) is False
        assert param.validate(-1) is False
        assert param.validate(2.5) is False


class TestCategoricalParameter:
    """Test CategoricalParameter class."""

    def test_basic_categorical(self):
        """Test basic categorical parameter."""
        param = CategoricalParameter(
            name="strategy_type", values=["mean_reversion", "momentum", "breakout"]
        )

        values = param.get_values()
        assert len(values) == 3
        assert "mean_reversion" in values
        assert "momentum" in values
        assert "breakout" in values

    def test_numeric_categorical(self):
        """Test categorical with numeric values."""
        param = CategoricalParameter(name="fibonacci", values=[1, 2, 3, 5, 8, 13])

        values = param.get_values()
        assert values == [1, 2, 3, 5, 8, 13]

    def test_validation(self):
        """Test parameter validation."""
        param = CategoricalParameter("test", ["a", "b", "c"])

        assert param.validate("a") is True
        assert param.validate("b") is True
        assert param.validate("d") is False
        assert param.validate(1) is False

    def test_empty_values(self):
        """Test empty values list."""
        with pytest.raises(ValueError):
            CategoricalParameter("test", [])

    def test_duplicate_values(self):
        """Test duplicate values."""
        with pytest.raises(ValueError):
            CategoricalParameter("test", ["a", "b", "a"])


class TestParameterSpace:
    """Test ParameterSpace class."""

    @pytest.fixture
    def sample_space(self):
        """Create sample parameter space."""
        return ParameterSpace(
            [
                ContinuousParameter("threshold", 0.1, 0.5, 0.1),
                DiscreteParameter("window", 5, 15, 5),
                CategoricalParameter("method", ["fast", "slow"]),
            ]
        )

    def test_basic_properties(self, sample_space):
        """Test basic parameter space properties."""
        assert sample_space.dimensions == 3
        assert sample_space.total_combinations == 5 * 3 * 2  # 30

    def test_generate_combinations(self, sample_space):
        """Test combination generation."""
        combinations = list(sample_space.generate_combinations())

        assert len(combinations) == 30

        # Check first combination
        first = combinations[0]
        assert "threshold" in first
        assert "window" in first
        assert "method" in first

        # Check all thresholds are present
        thresholds = set(c["threshold"] for c in combinations)
        assert len(thresholds) == 5
        assert all(0.1 <= t <= 0.5 for t in thresholds)

    def test_get_parameter(self, sample_space):
        """Test getting parameter by name."""
        param = sample_space.get_parameter("threshold")
        assert param.name == "threshold"
        assert param.min_value == 0.1

        with pytest.raises(KeyError):
            sample_space.get_parameter("nonexistent")

    def test_duplicate_names(self):
        """Test duplicate parameter names."""
        with pytest.raises(ValueError):
            ParameterSpace(
                [DiscreteParameter("param", 1, 10), DiscreteParameter("param", 20, 30)]
            )

    def test_validate_combination(self, sample_space):
        """Test combination validation."""
        # Valid combination
        valid_combo = {"threshold": 0.3, "window": 10, "method": "fast"}
        is_valid, errors = sample_space.validate_combination(valid_combo)
        assert is_valid is True
        assert len(errors) == 0

        # Missing parameter
        missing_combo = {"threshold": 0.3, "window": 10}
        is_valid, errors = sample_space.validate_combination(missing_combo)
        assert is_valid is False
        assert any("Missing parameter: method" in e for e in errors)

        # Invalid value
        invalid_combo = {
            "threshold": 0.6,  # Out of range
            "window": 10,
            "method": "fast",
        }
        is_valid, errors = sample_space.validate_combination(invalid_combo)
        assert is_valid is False
        assert any("Invalid value for threshold" in e for e in errors)

        # Extra parameter
        extra_combo = {"threshold": 0.3, "window": 10, "method": "fast", "extra": 123}
        is_valid, errors = sample_space.validate_combination(extra_combo)
        assert is_valid is False
        assert any("Unknown parameters" in e for e in errors)

    def test_random_combination(self, sample_space):
        """Test random combination generation."""
        # Single combination
        combo = sample_space.get_random_combination()
        assert isinstance(combo, dict)
        is_valid, _ = sample_space.validate_combination(combo)
        assert is_valid

        # Multiple combinations
        combos = sample_space.get_random_combination(n=10)
        assert len(combos) == 10
        for combo in combos:
            is_valid, _ = sample_space.validate_combination(combo)
            assert is_valid

    def test_subset(self, sample_space):
        """Test parameter space subset."""
        subset = sample_space.subset(["threshold", "method"])

        assert subset.dimensions == 2
        assert subset.total_combinations == 5 * 2  # 10

        combinations = list(subset.generate_combinations())
        assert len(combinations) == 10
        assert all("window" not in c for c in combinations)

        # Invalid parameter name
        with pytest.raises(KeyError):
            sample_space.subset(["threshold", "nonexistent"])

    def test_summary(self, sample_space):
        """Test parameter space summary."""
        summary = sample_space.get_summary()

        assert summary["dimensions"] == 3
        assert summary["total_combinations"] == 30
        assert "parameters" in summary
        assert "threshold" in summary["parameters"]
        assert summary["parameters"]["threshold"]["type"] == "continuous"

    def test_iteration(self, sample_space):
        """Test iterating over parameter space."""
        count = 0
        for combo in sample_space:
            count += 1
            assert isinstance(combo, dict)
            assert len(combo) == 3

        assert count == 30
