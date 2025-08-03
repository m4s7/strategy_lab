"""Tests for configuration validation."""

from datetime import datetime, timedelta

import pytest

from strategy_lab.core.config.models import OptimizationMethod
from strategy_lab.core.config.validation import ConfigValidator, ValidationResult


class TestValidationResult:
    """Test ValidationResult class."""

    def test_empty_result(self):
        """Test empty validation result."""
        result = ValidationResult()
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.info) == 0

    def test_with_errors(self):
        """Test result with errors."""
        result = ValidationResult()
        result.add_error("Test error 1")
        result.add_error("Test error 2")

        assert not result.is_valid
        assert len(result.errors) == 2
        assert "Test error 1" in result.errors

    def test_with_warnings(self):
        """Test result with warnings."""
        result = ValidationResult()
        result.add_warning("Test warning")

        assert result.is_valid  # Warnings don't affect validity
        assert len(result.warnings) == 1

    def test_string_representation(self):
        """Test string representation."""
        result = ValidationResult()
        result.add_error("Error message")
        result.add_warning("Warning message")
        result.add_info("Info message")

        str_repr = str(result)
        assert "ERRORS:" in str_repr
        assert "WARNINGS:" in str_repr
        assert "INFO:" in str_repr
        assert "Error message" in str_repr


class TestConfigValidator:
    """Test ConfigValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a validator instance."""
        return ConfigValidator()

    @pytest.fixture
    def valid_config(self):
        """Create a valid configuration."""
        return {
            "system": {
                "version": "1.0.0",
                "environment": "development",
                "data": {"data_path": "/tmp/test_data"},
                "performance": {"max_memory_gb": 16.0, "parallel_workers": 4},
            },
            "strategies": {
                "order_book_imbalance": {
                    "name": "order_book_imbalance",
                    "parameters": {
                        "positive_threshold": 0.3,
                        "negative_threshold": -0.3,
                        "depth_levels": 5,
                    },
                }
            },
        }

    def test_valid_configuration(self, validator, valid_config):
        """Test validation of valid configuration."""
        result = validator.validate(valid_config)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_missing_required_field(self, validator):
        """Test validation with missing required field."""
        config = {
            "system": {
                # Missing data field
                "version": "1.0.0"
            }
        }
        result = validator.validate(config)
        assert not result.is_valid
        assert any("data" in error for error in result.errors)

    def test_invalid_enum_value(self, validator, valid_config):
        """Test validation with invalid enum value."""
        valid_config["system"]["environment"] = "invalid_env"
        result = validator.validate(valid_config)
        assert not result.is_valid
        assert any("environment" in error for error in result.errors)

    def test_strategy_missing_parameters(self, validator, valid_config):
        """Test strategy with missing required parameters."""
        # Remove required parameter
        del valid_config["strategies"]["order_book_imbalance"]["parameters"][
            "positive_threshold"
        ]

        result = validator.validate(valid_config)
        assert not result.is_valid
        assert any("positive_threshold" in error for error in result.errors)

    def test_strategy_unknown_parameters(self, validator, valid_config):
        """Test strategy with unknown parameters."""
        # Add unknown parameter
        valid_config["strategies"]["order_book_imbalance"]["parameters"][
            "unknown_param"
        ] = 123

        result = validator.validate(valid_config)
        assert result.is_valid  # Unknown params generate warnings, not errors
        assert any("unknown_param" in warning for warning in result.warnings)

    def test_date_range_validation(self, validator, valid_config):
        """Test date range validation."""
        # Add backtesting with invalid dates
        valid_config["backtesting"] = {
            "start_date": datetime.now() - timedelta(days=1),
            "end_date": datetime.now() - timedelta(days=2),  # End before start
        }

        result = validator.validate(valid_config)
        assert not result.is_valid
        assert any("end_date" in error for error in result.errors)

    def test_future_dates_warning(self, validator, valid_config):
        """Test warning for future dates."""
        # Add backtesting with future dates
        valid_config["backtesting"] = {
            "start_date": datetime.now() - timedelta(days=30),
            "end_date": datetime.now() + timedelta(days=30),  # Future date
        }

        result = validator.validate(valid_config)
        assert result.is_valid
        assert any("future" in warning.lower() for warning in result.warnings)

    def test_parameter_dependencies(self, validator, valid_config):
        """Test parameter dependency validation."""
        # Add optimization with genetic algorithm but missing required params
        valid_config["optimization"] = {
            "method": "genetic_algorithm"
            # Missing population_size and mutation_rate
        }

        result = validator.validate(valid_config)
        assert not result.is_valid
        assert any("population_size" in error for error in result.errors)
        assert any("mutation_rate" in error for error in result.errors)

    def test_resource_limit_warnings(self, validator, valid_config):
        """Test resource limit warnings."""
        # Set very high resource limits
        valid_config["system"]["performance"]["max_memory_gb"] = 256.0
        valid_config["system"]["performance"]["parallel_workers"] = 64

        result = validator.validate(valid_config)
        assert result.is_valid
        assert any("max_memory_gb" in warning for warning in result.warnings)
        assert any("parallel_workers" in warning for warning in result.warnings)

    def test_file_path_validation(self, validator, valid_config):
        """Test file path validation."""
        # Set non-existent path
        valid_config["system"]["data"]["data_path"] = "/non/existent/path"

        result = validator.validate(valid_config)
        assert not result.is_valid
        assert any("does not exist" in error for error in result.errors)

    def test_parameter_update_validation(self, validator, valid_config):
        """Test validation of parameter updates."""
        update = {
            "strategies": {
                "order_book_imbalance": {
                    "parameters": {"positive_threshold": 0.5}  # Valid update
                }
            }
        }

        result = validator.validate_parameter_update(valid_config, update)
        assert result.is_valid

    def test_breaking_change_detection(self, validator, valid_config):
        """Test detection of breaking changes."""
        # Remove a strategy
        update = {"strategies": {}}  # Empty strategies

        result = validator.validate_parameter_update(valid_config, update)
        assert result.is_valid  # Removal is valid but generates warning
        assert any("removed" in warning for warning in result.warnings)

    def test_deep_merge(self, validator):
        """Test deep merge functionality."""
        base = {"a": 1, "b": {"c": 2, "d": 3}}
        update = {"b": {"c": 4, "e": 5}, "f": 6}

        merged = validator._deep_merge(base, update)

        assert merged["a"] == 1
        assert merged["b"]["c"] == 4  # Updated
        assert merged["b"]["d"] == 3  # Preserved
        assert merged["b"]["e"] == 5  # Added
        assert merged["f"] == 6  # Added
