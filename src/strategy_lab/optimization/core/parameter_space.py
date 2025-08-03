"""Parameter space definitions for optimization."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Tuple, Union

import numpy as np


class Parameter(ABC):
    """Abstract base class for optimization parameters."""

    # Subclasses must define name and description attributes

    @abstractmethod
    def get_values(self) -> List[Any]:
        """Get all possible values for this parameter."""
        pass

    @abstractmethod
    def get_range_info(self) -> Dict[str, Any]:
        """Get information about the parameter range."""
        pass

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate if a value is valid for this parameter."""
        pass


@dataclass
class ContinuousParameter(Parameter):
    """Continuous (float) parameter with defined range and step."""

    name: str
    min_value: float
    max_value: float
    step: float
    description: str = ""
    include_endpoint: bool = True

    def __post_init__(self):
        """Validate parameter configuration."""
        if self.min_value >= self.max_value:
            raise ValueError(f"min_value must be less than max_value for {self.name}")
        if self.step <= 0:
            raise ValueError(f"step must be positive for {self.name}")

    def get_values(self) -> List[float]:
        """Get all values in the range."""
        if self.include_endpoint:
            # Use np.arange with adjusted endpoint
            n_steps = int(np.round((self.max_value - self.min_value) / self.step)) + 1
            values = [self.min_value + i * self.step for i in range(n_steps)]
            # Ensure we don't exceed max_value due to floating point errors
            # Round to avoid floating point precision issues
            decimal_places = max(0, -int(np.floor(np.log10(abs(self.step))))) + 2
            return [
                round(v, decimal_places)
                for v in values
                if v <= self.max_value + self.step * 0.1
            ]
        else:
            values = list(np.arange(self.min_value, self.max_value, self.step))
            decimal_places = max(0, -int(np.floor(np.log10(abs(self.step))))) + 2
            return [round(v, decimal_places) for v in values]

    def get_range_info(self) -> Dict[str, Any]:
        """Get range information."""
        return {
            "type": "continuous",
            "min": self.min_value,
            "max": self.max_value,
            "step": self.step,
            "n_values": len(self.get_values()),
        }

    def validate(self, value: Any) -> bool:
        """Validate value is within range."""
        if not isinstance(value, (int, float)):
            return False
        return self.min_value <= value <= self.max_value


@dataclass
class DiscreteParameter(Parameter):
    """Discrete (integer) parameter with defined range and step."""

    name: str
    min_value: int
    max_value: int
    step: int = 1
    description: str = ""

    def __post_init__(self):
        """Validate parameter configuration."""
        if self.min_value >= self.max_value:
            raise ValueError(f"min_value must be less than max_value for {self.name}")
        if self.step <= 0:
            raise ValueError(f"step must be positive for {self.name}")

    def get_values(self) -> List[int]:
        """Get all values in the range."""
        return list(range(self.min_value, self.max_value + 1, self.step))

    def get_range_info(self) -> Dict[str, Any]:
        """Get range information."""
        return {
            "type": "discrete",
            "min": self.min_value,
            "max": self.max_value,
            "step": self.step,
            "n_values": len(self.get_values()),
        }

    def validate(self, value: Any) -> bool:
        """Validate value is within range."""
        if not isinstance(value, int):
            return False
        if value < self.min_value or value > self.max_value:
            return False
        return (value - self.min_value) % self.step == 0


@dataclass
class CategoricalParameter(Parameter):
    """Categorical parameter with finite set of values."""

    name: str
    values: List[Any]
    description: str = ""

    def __post_init__(self):
        """Validate parameter configuration."""
        if not self.values:
            raise ValueError(f"values list cannot be empty for {self.name}")
        if len(set(self.values)) != len(self.values):
            raise ValueError(f"values must be unique for {self.name}")

    def get_values(self) -> List[Any]:
        """Get all possible values."""
        return self.values.copy()

    def get_range_info(self) -> Dict[str, Any]:
        """Get range information."""
        return {
            "type": "categorical",
            "values": self.values,
            "n_values": len(self.values),
        }

    def validate(self, value: Any) -> bool:
        """Validate value is in the set."""
        return value in self.values


class ParameterSpace:
    """Multi-dimensional parameter space for optimization."""

    def __init__(self, parameters: List[Parameter]):
        """Initialize parameter space.

        Args:
            parameters: List of parameter definitions
        """
        self.parameters = parameters
        self.parameter_dict = {p.name: p for p in parameters}

        # Validate no duplicate names
        if len(self.parameter_dict) != len(parameters):
            raise ValueError("Parameter names must be unique")

        # Pre-compute total combinations
        self._total_combinations = self._calculate_total_combinations()

    def _calculate_total_combinations(self) -> int:
        """Calculate total number of parameter combinations."""
        total = 1
        for param in self.parameters:
            total *= len(param.get_values())
        return total

    @property
    def total_combinations(self) -> int:
        """Get total number of parameter combinations."""
        return self._total_combinations

    @property
    def dimensions(self) -> int:
        """Get number of dimensions in parameter space."""
        return len(self.parameters)

    def get_parameter(self, name: str) -> Parameter:
        """Get parameter by name."""
        if name not in self.parameter_dict:
            raise KeyError(f"Parameter '{name}' not found")
        return self.parameter_dict[name]

    def generate_combinations(self) -> Iterator[Dict[str, Any]]:
        """Generate all parameter combinations.

        Yields:
            Dictionary mapping parameter names to values
        """
        # Get all parameter values
        param_names = [p.name for p in self.parameters]
        param_values = [p.get_values() for p in self.parameters]

        # Generate cartesian product
        import itertools

        for combination in itertools.product(*param_values):
            yield dict(zip(param_names, combination))

    def get_random_combination(self, n: int = 1) -> List[Dict[str, Any]]:
        """Get random parameter combinations.

        Args:
            n: Number of random combinations to generate

        Returns:
            List of parameter combinations
        """
        combinations = []
        for _ in range(n):
            combo = {}
            for param in self.parameters:
                values = param.get_values()
                combo[param.name] = np.random.choice(values)
            combinations.append(combo)

        return combinations if n > 1 else combinations[0]

    def validate_combination(
        self, combination: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate a parameter combination.

        Args:
            combination: Parameter combination to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check all required parameters are present
        for param in self.parameters:
            if param.name not in combination:
                errors.append(f"Missing parameter: {param.name}")
                continue

            # Validate parameter value
            if not param.validate(combination[param.name]):
                errors.append(
                    f"Invalid value for {param.name}: {combination[param.name]}"
                )

        # Check for extra parameters
        extra_params = set(combination.keys()) - set(self.parameter_dict.keys())
        if extra_params:
            errors.append(f"Unknown parameters: {extra_params}")

        return len(errors) == 0, errors

    def get_summary(self) -> Dict[str, Any]:
        """Get parameter space summary."""
        return {
            "dimensions": self.dimensions,
            "total_combinations": self.total_combinations,
            "parameters": {
                param.name: param.get_range_info() for param in self.parameters
            },
        }

    def subset(self, parameter_names: List[str]) -> "ParameterSpace":
        """Create a subset of the parameter space.

        Args:
            parameter_names: Names of parameters to include

        Returns:
            New ParameterSpace with subset of parameters
        """
        subset_params = []
        for name in parameter_names:
            if name not in self.parameter_dict:
                raise KeyError(f"Parameter '{name}' not found")
            subset_params.append(self.parameter_dict[name])

        return ParameterSpace(subset_params)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ParameterSpace(dimensions={self.dimensions}, "
            f"combinations={self.total_combinations})"
        )

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over all combinations."""
        return self.generate_combinations()
