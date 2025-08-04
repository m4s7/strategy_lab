"""Configuration management with hot-reloading and versioning."""

import hashlib
import json
import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    FileSystemEventHandler = object  # Dummy for type hints
    Observer = None

from .loader import ConfigLoader
from .models import ConfigurationSet
from .validation import ConfigValidator, ValidationResult


class ConfigSnapshot:
    """Represents a configuration snapshot."""

    def __init__(self, config: dict[str, Any], timestamp: datetime, version: str):
        """Initialize configuration snapshot.

        Args:
            config: Configuration dictionary
            timestamp: Snapshot timestamp
            version: Configuration version
        """
        self.config = config
        self.timestamp = timestamp
        self.version = version
        self.hash = self._calculate_hash(config)

    def _calculate_hash(self, config: dict[str, Any]) -> str:
        """Calculate hash of configuration."""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()[:16]


class ConfigChangeHandler(FileSystemEventHandler):
    """Handles file system events for configuration files."""

    def __init__(self, manager: "ConfigManager"):
        """Initialize change handler.

        Args:
            manager: Parent ConfigManager instance
        """
        self.manager = manager
        self._last_event_time = {}
        self._debounce_seconds = 0.5

    def on_modified(self, event):
        """Handle file modification event."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Check if it's a configuration file
        if file_path.suffix.lower() not in ConfigLoader.SUPPORTED_FORMATS:
            return

        # Debounce events
        current_time = time.time()
        last_time = self._last_event_time.get(file_path, 0)

        if current_time - last_time < self._debounce_seconds:
            return

        self._last_event_time[file_path] = current_time

        # Notify manager
        self.manager._on_file_changed(file_path)


class ConfigManager:
    """Manages configuration with hot-reloading, versioning, and validation."""

    def __init__(
        self, config_path: Path, auto_reload: bool = True, max_history: int = 50
    ):
        """Initialize configuration manager.

        Args:
            config_path: Path to main configuration file
            auto_reload: Enable automatic configuration reloading
            max_history: Maximum number of snapshots to keep
        """
        self.config_path = config_path
        self.auto_reload = auto_reload
        self.max_history = max_history

        self.loader = ConfigLoader(config_path.parent)
        self.validator = ConfigValidator()

        # Current configuration
        self._config: ConfigurationSet | None = None
        self._config_dict: dict[str, Any] = {}
        self._lock = threading.RLock()

        # History and versioning
        self._history: deque[ConfigSnapshot] = deque(maxlen=max_history)
        self._version_counter = 0

        # Change callbacks
        self._callbacks: list[Callable[[ConfigurationSet], None]] = []

        # File watching
        self._observer: Observer | None = None
        self._watched_files: set[Path] = set()

        # Load initial configuration
        self.reload()

        # Start file watching if enabled
        if auto_reload and WATCHDOG_AVAILABLE:
            self._start_watching()
        elif auto_reload and not WATCHDOG_AVAILABLE:
            print("Warning: watchdog not installed, auto-reload disabled")

    @property
    def config(self) -> ConfigurationSet:
        """Get current configuration."""
        with self._lock:
            if self._config is None:
                raise RuntimeError("Configuration not loaded")
            return self._config

    @property
    def config_dict(self) -> dict[str, Any]:
        """Get current configuration as dictionary."""
        with self._lock:
            return self._config_dict.copy()

    def reload(self, validate: bool = True) -> ValidationResult:
        """Reload configuration from file.

        Args:
            validate: Whether to validate configuration

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        try:
            # Load configuration
            config_dict = self.loader.load_with_environment(self.config_path)

            # Validate if requested
            if validate:
                result = self.validator.validate(config_dict)
                if not result.is_valid:
                    result.add_error("Configuration validation failed")
                    return result

            # Parse into ConfigurationSet
            new_config = ConfigurationSet(**config_dict)

            # Update configuration
            with self._lock:
                old_config = self._config
                self._config = new_config
                self._config_dict = config_dict

                # Create snapshot
                self._version_counter += 1
                version = f"v{self._version_counter}"
                snapshot = ConfigSnapshot(config_dict, datetime.now(), version)
                self._history.append(snapshot)

            # Notify callbacks
            if old_config is not None:
                self._notify_callbacks(new_config)

            result.add_info(f"Configuration reloaded successfully (version: {version})")

        except Exception as e:
            result.add_error(f"Failed to reload configuration: {e}")

        return result

    def update(
        self, updates: dict[str, Any], validate: bool = True
    ) -> ValidationResult:
        """Update configuration with partial updates.

        Args:
            updates: Dictionary of updates to apply
            validate: Whether to validate changes

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        with self._lock:
            # Merge updates with current configuration
            merged = self.loader._deep_merge(self._config_dict.copy(), updates)

            # Validate if requested
            if validate:
                result = self.validator.validate_parameter_update(
                    self._config_dict, updates
                )
                if not result.is_valid:
                    return result

            try:
                # Parse merged configuration
                new_config = ConfigurationSet(**merged)

                # Update configuration
                self._config = new_config
                self._config_dict = merged

                # Create snapshot
                self._version_counter += 1
                version = f"v{self._version_counter}"
                snapshot = ConfigSnapshot(merged, datetime.now(), version)
                self._history.append(snapshot)

                # Notify callbacks
                self._notify_callbacks(new_config)

                result.add_info(
                    f"Configuration updated successfully (version: {version})"
                )

            except Exception as e:
                result.add_error(f"Failed to update configuration: {e}")

        return result

    def rollback(self, version: str | None = None) -> ValidationResult:
        """Rollback to a previous configuration version.

        Args:
            version: Version to rollback to (None for previous)

        Returns:
            ValidationResult
        """
        result = ValidationResult()

        with self._lock:
            if not self._history:
                result.add_error("No configuration history available")
                return result

            # Find target snapshot
            if version is None:
                # Rollback to previous version
                if len(self._history) < 2:
                    result.add_error("No previous version available")
                    return result
                snapshot = self._history[-2]
            else:
                # Find specific version
                snapshot = None
                for s in self._history:
                    if s.version == version:
                        snapshot = s
                        break

                if snapshot is None:
                    result.add_error(f"Version not found: {version}")
                    return result

            try:
                # Restore configuration
                new_config = ConfigurationSet(**snapshot.config)
                self._config = new_config
                self._config_dict = snapshot.config

                # Create new snapshot for the rollback
                self._version_counter += 1
                new_version = f"v{self._version_counter}"
                new_snapshot = ConfigSnapshot(
                    snapshot.config, datetime.now(), new_version
                )
                self._history.append(new_snapshot)

                # Notify callbacks
                self._notify_callbacks(new_config)

                result.add_info(
                    f"Rolled back to {snapshot.version} "
                    f"(new version: {new_version})"
                )

            except Exception as e:
                result.add_error(f"Failed to rollback: {e}")

        return result

    def get_history(self) -> list[dict[str, Any]]:
        """Get configuration history.

        Returns:
            List of history entries
        """
        with self._lock:
            return [
                {
                    "version": snapshot.version,
                    "timestamp": snapshot.timestamp.isoformat(),
                    "hash": snapshot.hash,
                }
                for snapshot in self._history
            ]

    def get_version(self, version: str) -> dict[str, Any] | None:
        """Get configuration for a specific version.

        Args:
            version: Version to retrieve

        Returns:
            Configuration dictionary or None
        """
        with self._lock:
            for snapshot in self._history:
                if snapshot.version == version:
                    return snapshot.config
        return None

    def register_callback(self, callback: Callable[[ConfigurationSet], None]) -> None:
        """Register a callback for configuration changes.

        Args:
            callback: Function to call on configuration change
        """
        self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[ConfigurationSet], None]) -> None:
        """Unregister a configuration change callback.

        Args:
            callback: Callback to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _notify_callbacks(self, config: ConfigurationSet) -> None:
        """Notify all registered callbacks of configuration change."""
        for callback in self._callbacks:
            try:
                callback(config)
            except Exception as e:
                print(f"Error in configuration callback: {e}")

    def _start_watching(self) -> None:
        """Start watching configuration files for changes."""
        if not WATCHDOG_AVAILABLE or self._observer is not None:
            return

        self._observer = Observer()
        handler = ConfigChangeHandler(self)

        # Watch configuration directory
        config_dir = self.config_path.parent
        self._observer.schedule(handler, str(config_dir), recursive=True)

        self._observer.start()

    def _stop_watching(self) -> None:
        """Stop watching configuration files."""
        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None

    def _on_file_changed(self, file_path: Path) -> None:
        """Handle configuration file change.

        Args:
            file_path: Path to changed file
        """
        # Check if it's the main config file or a related file
        if file_path == self.config_path or file_path in self._watched_files:
            print(f"Configuration file changed: {file_path}")
            result = self.reload()
            if not result.is_valid:
                print(f"Configuration reload failed:\n{result}")
            else:
                print("Configuration reloaded successfully")

    def export_config(self, output_path: Path, format: str = "yaml") -> None:
        """Export current configuration to file.

        Args:
            output_path: Path for exported configuration
            format: Export format ('yaml' or 'json')
        """
        with self._lock:
            config_dict = self._config_dict.copy()

        with open(output_path, "w") as f:
            if format == "yaml":
                import yaml

                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
            else:  # json
                json.dump(config_dict, f, indent=2)

    def close(self) -> None:
        """Close configuration manager and stop watching."""
        self._stop_watching()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
