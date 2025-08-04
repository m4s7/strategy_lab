"""Tests for configuration manager."""

import tempfile
import time
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml

from strategy_lab.core.config.manager import ConfigManager, ConfigSnapshot
from strategy_lab.core.config.models import ConfigurationSet


class TestConfigSnapshot:
    """Test ConfigSnapshot class."""

    def test_snapshot_creation(self):
        """Test creating configuration snapshot."""
        config = {"test": "value", "nested": {"key": "value"}}
        snapshot = ConfigSnapshot(config, timestamp=time.time(), version="v1")

        assert snapshot.config == config
        assert snapshot.version == "v1"
        assert len(snapshot.hash) == 16  # Truncated hash

    def test_snapshot_hash(self):
        """Test snapshot hash calculation."""
        config1 = {"a": 1, "b": 2}
        config2 = {"b": 2, "a": 1}  # Same content, different order
        config3 = {"a": 1, "b": 3}  # Different content

        snapshot1 = ConfigSnapshot(config1, time.time(), "v1")
        snapshot2 = ConfigSnapshot(config2, time.time(), "v2")
        snapshot3 = ConfigSnapshot(config3, time.time(), "v3")

        # Same content should have same hash
        assert snapshot1.hash == snapshot2.hash
        # Different content should have different hash
        assert snapshot1.hash != snapshot3.hash


class TestConfigManager:
    """Test ConfigManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for tests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration."""
        return {
            "system": {
                "version": "1.0.0",
                "environment": "test",
                "data": {"data_path": "/tmp/data"},
                "logging": {"level": "INFO"},
            },
            "strategies": {
                "test_strategy": {
                    "name": "test_strategy",
                    "parameters": {"threshold": 0.5},
                }
            },
        }

    @pytest.fixture
    def config_file(self, temp_dir, sample_config):
        """Create configuration file."""
        config_path = temp_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(sample_config, f)
        return config_path

    @pytest.fixture
    def manager(self, config_file):
        """Create ConfigManager instance."""
        return ConfigManager(config_file, auto_reload=False)

    def test_initialization(self, manager, sample_config):
        """Test manager initialization."""
        assert manager.config is not None
        assert isinstance(manager.config, ConfigurationSet)
        assert manager.config.system.version == "1.0.0"
        assert len(manager._history) == 1

    def test_config_access(self, manager):
        """Test accessing configuration."""
        # Access as ConfigurationSet
        config = manager.config
        assert config.system.logging.level.value == "INFO"

        # Access as dictionary
        config_dict = manager.config_dict
        assert config_dict["system"]["logging"]["level"] == "INFO"

    def test_reload(self, manager, config_file, sample_config):
        """Test configuration reload."""
        # Modify configuration file
        sample_config["system"]["logging"]["level"] = "DEBUG"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Reload
        result = manager.reload()
        assert result.is_valid
        assert manager.config.system.logging.level.value == "DEBUG"
        assert len(manager._history) == 2

    def test_reload_with_invalid_config(self, manager, config_file):
        """Test reload with invalid configuration."""
        # Write invalid configuration
        with open(config_file, "w") as f:
            yaml.dump({"invalid": "config"}, f)

        # Reload should fail
        result = manager.reload()
        assert not result.is_valid
        # Original config should remain
        assert manager.config.system.version == "1.0.0"

    def test_update(self, manager):
        """Test configuration update."""
        updates = {
            "system": {"logging": {"level": "DEBUG"}},
            "strategies": {"test_strategy": {"parameters": {"threshold": 0.7}}},
        }

        result = manager.update(updates)
        assert result.is_valid
        assert manager.config.system.logging.level.value == "DEBUG"
        assert manager.config.strategies["test_strategy"].parameters["threshold"] == 0.7
        assert len(manager._history) == 2

    def test_update_validation(self, manager):
        """Test update validation."""
        # Invalid update
        updates = {"system": {"environment": "invalid_env"}}

        result = manager.update(updates)
        assert not result.is_valid
        # Config should not change
        assert manager.config.system.environment == "test"

    def test_rollback_to_previous(self, manager):
        """Test rollback to previous version."""
        # Make a change
        manager.update({"system": {"logging": {"level": "DEBUG"}}})
        assert manager.config.system.logging.level.value == "DEBUG"

        # Rollback
        result = manager.rollback()
        assert result.is_valid
        assert manager.config.system.logging.level.value == "INFO"
        assert len(manager._history) == 3  # Original + update + rollback

    def test_rollback_to_specific_version(self, manager):
        """Test rollback to specific version."""
        # Make multiple changes
        manager.update({"system": {"logging": {"level": "DEBUG"}}})
        manager.update({"system": {"logging": {"level": "WARNING"}}})

        # Get version history
        history = manager.get_history()
        first_version = history[0]["version"]

        # Rollback to first version
        result = manager.rollback(first_version)
        assert result.is_valid
        assert manager.config.system.logging.level.value == "INFO"

    def test_rollback_errors(self, manager):
        """Test rollback error cases."""
        # No previous version
        result = manager.rollback()
        assert not result.is_valid
        assert "No previous version" in str(result)

        # Invalid version
        result = manager.rollback("v999")
        assert not result.is_valid
        assert "Version not found" in str(result)

    def test_history_management(self, manager):
        """Test configuration history."""
        # Make changes
        for i in range(5):
            manager.update(
                {"system": {"logging": {"level": "DEBUG" if i % 2 else "INFO"}}}
            )

        history = manager.get_history()
        assert len(history) == 6  # Original + 5 updates

        # Check history structure
        for entry in history:
            assert "version" in entry
            assert "timestamp" in entry
            assert "hash" in entry

    def test_max_history_limit(self):
        """Test maximum history limit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(
                yaml.dump({"system": {"data": {"data_path": "/tmp"}}})
            )

            # Create manager with small history limit
            manager = ConfigManager(config_path, auto_reload=False, max_history=3)

            # Make more changes than limit
            for i in range(5):
                manager.update({"system": {"version": f"1.0.{i}"}})

            # History should be limited
            assert len(manager._history) == 3

    def test_callbacks(self, manager):
        """Test configuration change callbacks."""
        callback_mock = Mock()
        manager.register_callback(callback_mock)

        # Update should trigger callback
        manager.update({"system": {"logging": {"level": "DEBUG"}}})
        callback_mock.assert_called_once()

        # Check callback argument
        call_args = callback_mock.call_args[0]
        assert isinstance(call_args[0], ConfigurationSet)
        assert call_args[0].system.logging.level.value == "DEBUG"

        # Unregister callback
        manager.unregister_callback(callback_mock)
        callback_mock.reset_mock()

        # Should not be called after unregistering
        manager.update({"system": {"logging": {"level": "INFO"}}})
        callback_mock.assert_not_called()

    def test_callback_error_handling(self, manager):
        """Test callback error handling."""

        def failing_callback(config):
            raise Exception("Callback error")

        manager.register_callback(failing_callback)

        # Update should not fail despite callback error
        result = manager.update({"system": {"logging": {"level": "DEBUG"}}})
        assert result.is_valid

    def test_get_version(self, manager):
        """Test retrieving specific version."""
        # Make changes
        manager.update({"system": {"logging": {"level": "DEBUG"}}})
        manager.update({"system": {"logging": {"level": "WARNING"}}})

        history = manager.get_history()

        # Get specific versions
        v1_config = manager.get_version(history[0]["version"])
        assert v1_config["system"]["logging"]["level"] == "INFO"

        v2_config = manager.get_version(history[1]["version"])
        assert v2_config["system"]["logging"]["level"] == "DEBUG"

        # Non-existent version
        assert manager.get_version("v999") is None

    def test_export_config(self, manager, temp_dir):
        """Test configuration export."""
        # Export as YAML
        yaml_path = temp_dir / "exported.yaml"
        manager.export_config(yaml_path, format="yaml")

        with open(yaml_path) as f:
            exported = yaml.safe_load(f)
        assert exported["system"]["version"] == "1.0.0"

        # Export as JSON
        json_path = temp_dir / "exported.json"
        manager.export_config(json_path, format="json")

        import json

        with open(json_path) as f:
            exported = json.load(f)
        assert exported["system"]["version"] == "1.0.0"

    def test_context_manager(self, config_file):
        """Test using manager as context manager."""
        with ConfigManager(config_file, auto_reload=False) as manager:
            assert manager.config is not None
            manager.update({"system": {"logging": {"level": "DEBUG"}}})

        # Manager should be closed after context
        assert manager._observer is None

    def test_hot_reload_disabled(self, config_file):
        """Test with hot reload disabled."""
        manager = ConfigManager(config_file, auto_reload=False)
        assert manager._observer is None

        # Modify file
        with open(config_file) as f:
            config = yaml.safe_load(f)
        config["system"]["logging"]["level"] = "DEBUG"
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        # Config should not auto-reload
        time.sleep(0.1)
        assert manager.config.system.logging.level.value == "INFO"

        manager.close()
