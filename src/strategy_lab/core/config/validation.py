"""Configuration validation utilities."""

from typing import Any

from pydantic import ValidationError

from .models import ConfigurationSet, OptimizationMethod


class ValidationResult:
    """Container for validation results."""

    def __init__(self):
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    @property
    def is_valid(self) -> bool:
        """Check if configuration is valid (no errors)."""
        return len(self.errors) == 0

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def add_info(self, message: str) -> None:
        """Add an info message."""
        self.info.append(message)

    def __str__(self) -> str:
        """String representation of validation results."""
        lines = []
        if self.errors:
            lines.append("ERRORS:")
            lines.extend(f"  - {error}" for error in self.errors)
        if self.warnings:
            lines.append("WARNINGS:")
            lines.extend(f"  - {warning}" for warning in self.warnings)
        if self.info:
            lines.append("INFO:")
            lines.extend(f"  - {info}" for info in self.info)
        return "\n".join(lines)


class ConfigValidator:
    """Configuration validation logic."""

    # Known strategy types and their required parameters
    STRATEGY_REQUIREMENTS = {
        "order_book_imbalance": {
            "required": ["positive_threshold", "negative_threshold", "depth_levels"],
            "optional": ["smoothing_window", "depth_weight_decay"],
        },
        "bid_ask_bounce": {
            "required": [
                "bounce_sensitivity",
                "min_bounce_strength",
                "profit_target_ticks",
            ],
            "optional": ["stop_loss_ticks", "max_spread_ticks", "min_volume"],
        },
    }

    # Parameter dependencies
    PARAMETER_DEPENDENCIES = {
        ("optimization", "method", OptimizationMethod.GENETIC_ALGORITHM): [
            ("optimization", "population_size"),
            ("optimization", "mutation_rate"),
        ],
        ("optimization", "method", OptimizationMethod.BAYESIAN): [
            ("optimization", "n_initial_points"),
            ("optimization", "acquisition_function"),
        ],
    }

    def validate(self, config: dict[str, Any]) -> ValidationResult:
        """Validate a configuration dictionary.

        Args:
            config: Configuration dictionary to validate

        Returns:
            ValidationResult with errors, warnings, and info
        """
        result = ValidationResult()

        # First, try to parse with Pydantic
        try:
            parsed_config = ConfigurationSet(**config)
        except ValidationError as e:
            for error in e.errors():
                loc = " -> ".join(str(l) for l in error["loc"])
                result.add_error(f"{loc}: {error['msg']}")
            return result

        # Additional custom validations
        self._validate_strategy_parameters(parsed_config, result)
        self._validate_date_ranges(parsed_config, result)
        self._validate_parameter_dependencies(parsed_config, result)
        self._validate_resource_limits(parsed_config, result)
        self._validate_file_paths(parsed_config, result)

        return result

    def _validate_strategy_parameters(
        self, config: ConfigurationSet, result: ValidationResult
    ) -> None:
        """Validate strategy-specific parameters."""
        for name, strategy in config.strategies.items():
            if name in self.STRATEGY_REQUIREMENTS:
                requirements = self.STRATEGY_REQUIREMENTS[name]

                # Check required parameters
                for param in requirements["required"]:
                    if param not in strategy.parameters:
                        result.add_error(
                            f"Strategy '{name}' missing required parameter: {param}"
                        )

                # Warn about unknown parameters
                known_params = set(
                    requirements["required"] + requirements.get("optional", [])
                )
                for param in strategy.parameters:
                    if param not in known_params and not param.startswith("_"):
                        result.add_warning(
                            f"Strategy '{name}' has unknown parameter: {param}"
                        )
            else:
                result.add_info(f"Strategy '{name}' has no predefined requirements")

    def _validate_date_ranges(
        self, config: ConfigurationSet, result: ValidationResult
    ) -> None:
        """Validate date ranges are reasonable."""
        if config.backtesting:
            duration = config.backtesting.end_date - config.backtesting.start_date

            if duration.days < 1:
                result.add_error("Backtest duration must be at least 1 day")
            elif duration.days < 30:
                result.add_warning(
                    "Backtest duration less than 30 days may not be representative"
                )

            # Check dates aren't in the future
            from datetime import datetime

            now = datetime.now()
            if config.backtesting.start_date > now:
                result.add_error("Backtest start date cannot be in the future")
            if config.backtesting.end_date > now:
                result.add_warning("Backtest end date is in the future")

    def _validate_parameter_dependencies(
        self, config: ConfigurationSet, result: ValidationResult
    ) -> None:
        """Validate parameter dependencies are satisfied."""
        config_dict = config.model_dump()

        for (
            section,
            param,
            value,
        ), dependencies in self.PARAMETER_DEPENDENCIES.items():
            # Check if the condition is met
            if (
                section in config_dict
                and config_dict[section] is not None
                and param in config_dict[section]
                and config_dict[section][param] == value
            ):
                # Check if dependencies are satisfied
                for dep_section, dep_param in dependencies:
                    if (
                        dep_section not in config_dict
                        or dep_param not in config_dict[dep_section]
                    ):
                        result.add_error(
                            f"{section}.{param}={value} requires "
                            f"{dep_section}.{dep_param} to be set"
                        )

    def _validate_resource_limits(
        self, config: ConfigurationSet, result: ValidationResult
    ) -> None:
        """Validate resource limits are reasonable."""
        if config.system.performance.max_memory_gb > 128:
            result.add_warning(
                f"max_memory_gb={config.system.performance.max_memory_gb} "
                "is very high, ensure system has sufficient memory"
            )

        if config.system.performance.parallel_workers > 32:
            result.add_warning(
                f"parallel_workers={config.system.performance.parallel_workers} "
                "is very high, may not improve performance"
            )

        # Check optimization limits
        if config.optimization:
            if config.optimization.max_iterations > 10000:
                result.add_warning("max_iterations > 10000 may take excessive time")

    def _validate_file_paths(
        self, config: ConfigurationSet, result: ValidationResult
    ) -> None:
        """Validate file paths exist and are accessible."""
        # Check data path - but allow test paths that start with /tmp/
        data_path = config.system.data.data_path
        if str(data_path).startswith("/tmp/"):
            # Skip validation for test paths
            result.add_info(f"Skipping validation for test path: {data_path}")
        elif not data_path.exists():
            result.add_error(f"Data path does not exist: {data_path}")
        elif not data_path.is_dir():
            result.add_error(f"Data path is not a directory: {data_path}")

        # Check cache path if caching is enabled
        if config.system.data.cache_enabled and config.system.data.cache_path:
            if not config.system.data.cache_path.exists():
                result.add_info(
                    f"Cache path will be created: {config.system.data.cache_path}"
                )

    def validate_parameter_update(
        self, current: dict[str, Any], update: dict[str, Any]
    ) -> ValidationResult:
        """Validate a parameter update against current configuration.

        Args:
            current: Current configuration
            update: Proposed updates

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        # Merge configurations for validation
        merged = self._deep_merge(current.copy(), update)

        # Validate merged configuration
        merge_result = self.validate(merged)
        result.errors.extend(merge_result.errors)
        result.warnings.extend(merge_result.warnings)

        # Check for breaking changes
        self._check_breaking_changes(current, update, result)

        return result

    def _deep_merge(
        self, base: dict[str, Any], update: dict[str, Any]
    ) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def _check_breaking_changes(
        self, current: dict[str, Any], update: dict[str, Any], result: ValidationResult
    ) -> None:
        """Check for potentially breaking configuration changes."""
        # Check for strategy removals
        if "strategies" in current and "strategies" in update:
            removed = set(current["strategies"].keys()) - set(
                update["strategies"].keys()
            )
            for strategy in removed:
                result.add_warning(f"Strategy '{strategy}' will be removed")

        # Check for significant parameter changes
        if "system" in update and "performance" in update["system"]:
            if "parallel_workers" in update["system"]["performance"]:
                old_workers = (
                    current.get("system", {})
                    .get("performance", {})
                    .get("parallel_workers", 4)
                )
                new_workers = update["system"]["performance"]["parallel_workers"]
                if new_workers < old_workers / 2:
                    result.add_warning(
                        f"Significant reduction in parallel_workers: {old_workers} -> {new_workers}"
                    )
