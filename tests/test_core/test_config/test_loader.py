"""Tests for configuration loader."""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from strategy_lab.core.config.loader import ConfigLoader
from strategy_lab.core.config.models import ConfigurationSet


class TestConfigLoader:
    """Test ConfigLoader class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def loader(self, temp_dir):
        """Create a loader instance."""
        return ConfigLoader(temp_dir)

    @pytest.fixture
    def sample_config(self):
        """Create sample configuration data."""
        return {
            "system": {
                "version": "1.0.0",
                "environment": "test",
                "data": {"data_path": "/tmp/data"},
            },
            "strategies": {
                "test_strategy": {
                    "name": "test_strategy",
                    "parameters": {"param1": 10, "param2": 0.5},
                }
            },
        }

    def test_load_yaml_file(self, loader, temp_dir, sample_config):
        """Test loading YAML configuration file."""
        # Write YAML file
        config_file = temp_dir / "test_config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Load configuration
        loaded = loader.load_file(config_file)

        assert loaded["system"]["version"] == "1.0.0"
        assert loaded["strategies"]["test_strategy"]["parameters"]["param1"] == 10

    def test_load_json_file(self, loader, temp_dir, sample_config):
        """Test loading JSON configuration file."""
        # Write JSON file
        config_file = temp_dir / "test_config.json"
        with open(config_file, "w") as f:
            json.dump(sample_config, f)

        # Load configuration
        loaded = loader.load_file(config_file)

        assert loaded["system"]["version"] == "1.0.0"
        assert loaded["strategies"]["test_strategy"]["parameters"]["param1"] == 10

    def test_file_not_found(self, loader, temp_dir):
        """Test loading non-existent file."""
        with pytest.raises(FileNotFoundError):
            loader.load_file(temp_dir / "non_existent.yaml")

    def test_unsupported_format(self, loader, temp_dir):
        """Test loading unsupported file format."""
        # Create file with unsupported extension
        config_file = temp_dir / "config.txt"
        config_file.write_text("some text")

        with pytest.raises(ValueError, match="Unsupported file format"):
            loader.load_file(config_file)

    def test_invalid_yaml(self, loader, temp_dir):
        """Test loading invalid YAML file."""
        config_file = temp_dir / "invalid.yaml"
        config_file.write_text("invalid: yaml: content:")

        with pytest.raises(ValueError, match="Failed to parse"):
            loader.load_file(config_file)

    def test_caching(self, loader, temp_dir, sample_config):
        """Test configuration caching."""
        config_file = temp_dir / "cached.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Load file twice
        loaded1 = loader.load_file(config_file)
        loaded2 = loader.load_file(config_file)

        # Should return cached copy
        assert loaded1 == loaded2

        # Modify returned dict shouldn't affect cache
        loaded1["new_key"] = "new_value"
        loaded3 = loader.load_file(config_file)
        assert "new_key" not in loaded3

    def test_load_directory(self, loader, temp_dir, sample_config):
        """Test loading all configs from directory."""
        # Create multiple config files
        configs_dir = temp_dir / "configs"
        configs_dir.mkdir()

        for i in range(3):
            config_file = configs_dir / f"config{i}.yaml"
            config = sample_config.copy()
            config["system"]["version"] = f"1.0.{i}"
            with open(config_file, "w") as f:
                yaml.dump(config, f)

        # Load directory
        configs = loader.load_directory(configs_dir)

        assert len(configs) == 3
        assert "config0" in configs
        assert configs["config1"]["system"]["version"] == "1.0.1"

    def test_load_directory_recursive(self, loader, temp_dir, sample_config):
        """Test recursive directory loading."""
        # Create nested structure
        base_dir = temp_dir / "configs"
        sub_dir = base_dir / "strategies"
        sub_dir.mkdir(parents=True)

        # Create files at different levels
        (base_dir / "base.yaml").write_text(yaml.dump(sample_config))
        (sub_dir / "strategy1.yaml").write_text(yaml.dump(sample_config))

        # Load recursively
        configs = loader.load_directory(base_dir, recursive=True)

        assert len(configs) == 2
        assert "base" in configs
        assert "strategies/strategy1" in configs

    def test_load_with_environment(self, loader, temp_dir, sample_config):
        """Test loading with environment-specific overrides."""
        # Create base config
        base_file = temp_dir / "config.yaml"
        with open(base_file, "w") as f:
            yaml.dump(sample_config, f)

        # Create environment override
        env_config = {
            "system": {
                "environment": "production",
                "performance": {"parallel_workers": 8},
            }
        }
        env_file = temp_dir / "config.production.yaml"
        with open(env_file, "w") as f:
            yaml.dump(env_config, f)

        # Load with environment
        loaded = loader.load_with_environment(base_file, "production")

        assert loaded["system"]["environment"] == "production"
        assert loaded["system"]["performance"]["parallel_workers"] == 8
        assert loaded["system"]["version"] == "1.0.0"  # From base

    def test_validate_file(self, loader, temp_dir):
        """Test file validation."""
        # Create valid config
        valid_config = {"system": {"data": {"data_path": "/tmp/data"}}}
        valid_file = temp_dir / "valid.yaml"
        with open(valid_file, "w") as f:
            yaml.dump(valid_config, f)

        result = loader.validate_file(valid_file)
        assert result.is_valid

        # Create invalid config
        invalid_config = {"system": {"environment": "invalid_env"}}
        invalid_file = temp_dir / "invalid.yaml"
        with open(invalid_file, "w") as f:
            yaml.dump(invalid_config, f)

        result = loader.validate_file(invalid_file)
        assert not result.is_valid

    def test_load_and_validate(self, loader, temp_dir):
        """Test loading and validating configuration."""
        # Valid configuration
        config = {"system": {"data": {"data_path": "/tmp/data"}}}
        config_file = temp_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config, f)

        # Should return ConfigurationSet
        config_set = loader.load_and_validate(config_file)
        assert isinstance(config_set, ConfigurationSet)
        assert config_set.system.data.data_path == Path("/tmp/data")

        # Invalid configuration
        invalid_config = {"invalid": "config"}
        invalid_file = temp_dir / "invalid.yaml"
        with open(invalid_file, "w") as f:
            yaml.dump(invalid_config, f)

        with pytest.raises(ValueError, match="validation failed"):
            loader.load_and_validate(invalid_file)

    def test_deep_merge(self, loader):
        """Test deep merge functionality."""
        base = {"a": 1, "b": {"c": 2, "d": {"e": 3}}, "list": [1, 2, 3]}

        override = {"b": {"c": 4, "d": {"f": 5}}, "list": [4, 5], "new": 6}

        merged = loader._deep_merge(base, override)

        assert merged["a"] == 1  # Preserved
        assert merged["b"]["c"] == 4  # Overridden
        assert merged["b"]["d"]["e"] == 3  # Preserved nested
        assert merged["b"]["d"]["f"] == 5  # Added nested
        assert merged["list"] == [4, 5]  # Replaced list
        assert merged["new"] == 6  # Added

    def test_clear_cache(self, loader, temp_dir, sample_config):
        """Test cache clearing."""
        config_file = temp_dir / "cached.yaml"
        with open(config_file, "w") as f:
            yaml.dump(sample_config, f)

        # Load to populate cache
        loader.load_file(config_file)
        assert len(loader._cache) > 0

        # Clear cache
        loader.clear_cache()
        assert len(loader._cache) == 0
