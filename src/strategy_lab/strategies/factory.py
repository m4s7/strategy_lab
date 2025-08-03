"""Strategy factory for creating and managing strategy instances."""

import copy
import logging
from typing import Any

from .protocol import StrategyProtocol
from .registry import registry

logger = logging.getLogger(__name__)


class StrategyFactory:
    """Factory for creating and managing strategy instances with hot-swapping support."""

    def __init__(self):
        """Initialize the strategy factory."""
        self._active_strategies: dict[str, StrategyProtocol] = {}
        self._strategy_states: dict[str, dict[str, Any]] = {}
        self._strategy_configs: dict[str, dict[str, Any]] = {}

    def create_strategy(
        self, strategy_name: str, instance_id: str | None = None, **kwargs
    ) -> StrategyProtocol:
        """Create a new strategy instance.

        Args:
            strategy_name: Name of the strategy to create
            instance_id: Unique identifier for this instance
            **kwargs: Strategy parameters

        Returns:
            Initialized strategy instance
        """
        if instance_id is None:
            instance_id = f"{strategy_name}_{len(self._active_strategies)}"

        # Create strategy through registry
        strategy = registry.create_strategy(strategy_name, **kwargs)

        # Store instance and configuration
        self._active_strategies[instance_id] = strategy
        self._strategy_configs[instance_id] = {
            "strategy_name": strategy_name,
            "parameters": kwargs,
        }

        # Initialize the strategy
        strategy.initialize(**kwargs)

        logger.info(f"Created strategy instance: {instance_id}")
        return strategy

    def get_strategy(self, instance_id: str) -> StrategyProtocol | None:
        """Get an active strategy instance.

        Args:
            instance_id: Strategy instance identifier

        Returns:
            Strategy instance or None if not found
        """
        return self._active_strategies.get(instance_id)

    def list_active_strategies(self) -> dict[str, str]:
        """List all active strategy instances.

        Returns:
            Dictionary of instance_id -> strategy_name
        """
        result = {}
        for instance_id, config in self._strategy_configs.items():
            result[instance_id] = config["strategy_name"]
        return result

    def hot_swap_strategy(
        self,
        instance_id: str,
        new_strategy_name: str,
        preserve_state: bool = True,
        **kwargs,
    ) -> StrategyProtocol:
        """Replace a running strategy with a new one.

        Args:
            instance_id: Instance to replace
            new_strategy_name: Name of new strategy
            preserve_state: Whether to preserve current state
            **kwargs: New strategy parameters

        Returns:
            New strategy instance

        Raises:
            KeyError: If instance not found
        """
        if instance_id not in self._active_strategies:
            raise KeyError(f"Strategy instance not found: {instance_id}")

        old_strategy = self._active_strategies[instance_id]

        # Save current state if requested
        if preserve_state:
            try:
                state = old_strategy.get_state()
                self._strategy_states[instance_id] = state
                logger.info(f"Saved state for {instance_id}")
            except Exception as e:
                logger.warning(f"Failed to save state: {e}")

        # Cleanup old strategy
        try:
            old_strategy.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        # Create new strategy
        new_strategy = registry.create_strategy(new_strategy_name, **kwargs)

        # Restore state if available and requested
        if preserve_state and instance_id in self._strategy_states:
            try:
                new_strategy.set_state(self._strategy_states[instance_id])
                logger.info(f"Restored state for {instance_id}")
            except Exception as e:
                logger.warning(f"Failed to restore state: {e}")

        # Initialize new strategy
        new_strategy.initialize(**kwargs)

        # Update tracking
        self._active_strategies[instance_id] = new_strategy
        self._strategy_configs[instance_id] = {
            "strategy_name": new_strategy_name,
            "parameters": kwargs,
        }

        logger.info(f"Hot-swapped {instance_id} to {new_strategy_name}")
        return new_strategy

    def remove_strategy(self, instance_id: str) -> None:
        """Remove and cleanup a strategy instance.

        Args:
            instance_id: Strategy instance to remove
        """
        if instance_id not in self._active_strategies:
            return

        strategy = self._active_strategies[instance_id]

        # Cleanup
        try:
            strategy.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

        # Remove from tracking
        del self._active_strategies[instance_id]
        del self._strategy_configs[instance_id]

        if instance_id in self._strategy_states:
            del self._strategy_states[instance_id]

        logger.info(f"Removed strategy instance: {instance_id}")

    def save_all_states(self) -> dict[str, dict[str, Any]]:
        """Save states of all active strategies.

        Returns:
            Dictionary of instance_id -> state
        """
        states = {}

        for instance_id, strategy in self._active_strategies.items():
            try:
                states[instance_id] = strategy.get_state()
            except Exception as e:
                logger.error(f"Failed to save state for {instance_id}: {e}")

        self._strategy_states.update(states)
        return states

    def cleanup_all(self) -> None:
        """Cleanup all active strategies."""
        for instance_id in list(self._active_strategies.keys()):
            self.remove_strategy(instance_id)

        logger.info("All strategies cleaned up")

    def get_strategy_config(self, instance_id: str) -> dict[str, Any] | None:
        """Get configuration for a strategy instance.

        Args:
            instance_id: Strategy instance identifier

        Returns:
            Configuration dictionary or None
        """
        return self._strategy_configs.get(instance_id)

    def clone_strategy(
        self, instance_id: str, new_instance_id: str | None = None
    ) -> StrategyProtocol:
        """Create a clone of an existing strategy instance.

        Args:
            instance_id: Instance to clone
            new_instance_id: ID for the new instance

        Returns:
            Cloned strategy instance
        """
        if instance_id not in self._active_strategies:
            raise KeyError(f"Strategy instance not found: {instance_id}")

        # Get configuration
        config = self._strategy_configs[instance_id]
        strategy_name = config["strategy_name"]
        parameters = config["parameters"].copy()

        # Create new instance
        if new_instance_id is None:
            new_instance_id = f"{instance_id}_clone"

        new_strategy = self.create_strategy(
            strategy_name, new_instance_id, **parameters
        )

        # Copy state
        try:
            state = self._active_strategies[instance_id].get_state()
            new_strategy.set_state(copy.deepcopy(state))
        except Exception as e:
            logger.warning(f"Failed to copy state: {e}")

        return new_strategy


# Global factory instance
factory = StrategyFactory()
