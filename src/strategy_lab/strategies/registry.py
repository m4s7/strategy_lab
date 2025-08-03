"""Strategy registry for dynamic loading and management."""

import importlib
import inspect
import logging
from pathlib import Path
from typing import Any, Optional

from .protocol import StrategyMetadata, StrategyProtocol

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """Registry for managing and loading strategies dynamically."""

    _instance: Optional["StrategyRegistry"] = None

    def __new__(cls) -> "StrategyRegistry":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the strategy registry."""
        if not hasattr(self, "_initialized"):
            self._strategies: dict[str, type[StrategyProtocol]] = {}
            self._metadata: dict[str, StrategyMetadata] = {}
            self._initialized = True
            logger.info("Strategy registry initialized")

    def register(
        self,
        strategy_class: type[StrategyProtocol],
        metadata: StrategyMetadata | None = None,
    ) -> None:
        """Register a strategy class with the registry.

        Args:
            strategy_class: Strategy class implementing StrategyProtocol
            metadata: Optional strategy metadata
        """
        # Validate strategy implements protocol
        if not isinstance(strategy_class, type):
            raise TypeError("Strategy must be a class")

        # Check required methods
        required_methods = ["initialize", "process_tick", "cleanup"]
        for method in required_methods:
            if not hasattr(strategy_class, method):
                raise AttributeError(
                    f"Strategy {strategy_class.__name__} missing required method: {method}"
                )

        # Get strategy name from metadata or class
        if metadata:
            name = metadata.name
        elif hasattr(strategy_class, "name"):
            name = strategy_class.name
        else:
            name = strategy_class.__name__

        # Store strategy and metadata
        self._strategies[name] = strategy_class

        if metadata:
            self._metadata[name] = metadata
        else:
            # Create default metadata
            self._metadata[name] = StrategyMetadata(
                name=name,
                version=getattr(strategy_class, "version", "1.0.0"),
                description=getattr(
                    strategy_class,
                    "description",
                    strategy_class.__doc__ or "No description",
                ),
            )

        logger.info(f"Registered strategy: {name}")

    def unregister(self, name: str) -> None:
        """Remove a strategy from the registry.

        Args:
            name: Strategy name to unregister
        """
        if name in self._strategies:
            del self._strategies[name]
            del self._metadata[name]
            logger.info(f"Unregistered strategy: {name}")

    def get_strategy(self, name: str) -> type[StrategyProtocol]:
        """Get a strategy class by name.

        Args:
            name: Strategy name

        Returns:
            Strategy class

        Raises:
            KeyError: If strategy not found
        """
        if name not in self._strategies:
            raise KeyError(f"Strategy not found: {name}")
        return self._strategies[name]

    def get_metadata(self, name: str) -> StrategyMetadata:
        """Get strategy metadata by name.

        Args:
            name: Strategy name

        Returns:
            Strategy metadata

        Raises:
            KeyError: If strategy not found
        """
        if name not in self._metadata:
            raise KeyError(f"Strategy metadata not found: {name}")
        return self._metadata[name]

    def list_strategies(self) -> list[str]:
        """List all registered strategy names.

        Returns:
            List of strategy names
        """
        return list(self._strategies.keys())

    def get_strategies_by_tag(self, tag: str) -> list[str]:
        """Get strategies with a specific tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of strategy names with the tag
        """
        results = []
        for name, metadata in self._metadata.items():
            if tag in metadata.tags:
                results.append(name)
        return results

    def create_strategy(self, name: str, **kwargs) -> StrategyProtocol:
        """Create a strategy instance by name.

        Args:
            name: Strategy name
            **kwargs: Strategy initialization parameters

        Returns:
            Initialized strategy instance
        """
        strategy_class = self.get_strategy(name)

        # Get default parameters from metadata
        metadata = self.get_metadata(name)
        params = metadata.parameters.copy()
        params.update(kwargs)

        # Create instance
        try:
            strategy = strategy_class(**params)
            logger.info(f"Created strategy instance: {name}")
            return strategy
        except Exception as e:
            logger.error(f"Failed to create strategy {name}: {e}")
            raise

    def discover_strategies(self, path: Path) -> int:
        """Discover and register strategies from a directory.

        Args:
            path: Directory path to search for strategies

        Returns:
            Number of strategies discovered
        """
        if not path.exists():
            logger.warning(f"Strategy path does not exist: {path}")
            return 0

        count = 0

        # Search for Python files
        for file_path in path.glob("*.py"):
            if file_path.name.startswith("_"):
                continue

            # Import module
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find strategy classes
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and hasattr(obj, "process_tick")
                        and obj.__module__ == module_name
                    ):
                        try:
                            self.register(obj)
                            count += 1
                        except Exception as e:
                            logger.error(f"Failed to register {name}: {e}")

        logger.info(f"Discovered {count} strategies from {path}")
        return count

    def validate_strategy(self, name: str) -> dict[str, Any]:
        """Validate a strategy's implementation and requirements.

        Args:
            name: Strategy name

        Returns:
            Validation results with any issues found
        """
        results = {"valid": True, "errors": [], "warnings": []}

        try:
            strategy_class = self.get_strategy(name)
            metadata = self.get_metadata(name)

            # Check required methods
            required_methods = ["initialize", "process_tick", "cleanup"]
            for method in required_methods:
                if not hasattr(strategy_class, method):
                    results["errors"].append(f"Missing required method: {method}")
                    results["valid"] = False

            # Check metadata completeness
            if not metadata.description:
                results["warnings"].append("No description provided")

            if not metadata.parameters:
                results["warnings"].append("No parameters defined")

            # Check instantiation
            try:
                test_instance = self.create_strategy(name)
                del test_instance
            except Exception as e:
                results["errors"].append(f"Failed to instantiate: {e}")
                results["valid"] = False

        except Exception as e:
            results["errors"].append(f"Validation error: {e}")
            results["valid"] = False

        return results


# Module-level registry instance
registry = StrategyRegistry()


def register_strategy(metadata: StrategyMetadata | None = None):
    """Decorator for registering strategies.

    Args:
        metadata: Optional strategy metadata

    Example:
        @register_strategy(StrategyMetadata(
            name="MyStrategy",
            version="1.0.0",
            description="My trading strategy"
        ))
        class MyStrategy:
            ...
    """

    def decorator(cls: type[StrategyProtocol]) -> type[StrategyProtocol]:
        registry.register(cls, metadata)
        return cls

    # Handle both @register_strategy and @register_strategy()
    if metadata is None or isinstance(metadata, type):
        # Called without parentheses
        cls = metadata
        registry.register(cls)
        return cls

    return decorator
