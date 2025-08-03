"""Configuration file loading and parsing."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import yaml
from pydantic import ValidationError

from .models import ConfigurationSet
from .validation import ConfigValidator, ValidationResult


class ConfigLoader:
    """Handles loading and parsing configuration files."""

    SUPPORTED_FORMATS = {".yaml", ".yml", ".json"}

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize configuration loader.

        Args:
            base_path: Base path for configuration files
        """
        self.base_path = base_path or Path.cwd()
        self.validator = ConfigValidator()
        self._cache: Dict[str, Dict[str, Any]] = {}

    def load_file(self, file_path: Path) -> Dict[str, Any]:
        """Load a configuration file.

        Args:
            file_path: Path to configuration file

        Returns:
            Parsed configuration dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported or parsing fails
        """
        # Resolve path relative to base_path if needed
        if not file_path.is_absolute():
            file_path = self.base_path / file_path

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        # Check cache
        cache_key = str(file_path.absolute())
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        # Check file format
        suffix = file_path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                f"Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            )

        # Load and parse file
        try:
            with open(file_path, "r") as f:
                if suffix in {".yaml", ".yml"}:
                    config = yaml.safe_load(f)
                else:  # .json
                    config = json.load(f)
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to parse {file_path}: {e}")

        # Cache the result
        self._cache[cache_key] = config

        return config

    def load_directory(
        self, directory: Path, pattern: str = "*.yaml", recursive: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """Load all configuration files from a directory.

        Args:
            directory: Directory to load from
            pattern: File pattern to match
            recursive: Whether to search recursively

        Returns:
            Dictionary mapping file names to configurations
        """
        if not directory.is_absolute():
            directory = self.base_path / directory

        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        configs = {}

        if recursive:
            files = directory.rglob(pattern)
        else:
            files = directory.glob(pattern)

        for file_path in files:
            if file_path.is_file():
                rel_path = file_path.relative_to(directory)
                name = str(rel_path.with_suffix(""))
                try:
                    configs[name] = self.load_file(file_path)
                except Exception as e:
                    # Log error but continue loading other files
                    print(f"Warning: Failed to load {file_path}: {e}")

        return configs

    def load_with_environment(
        self, base_file: Path, environment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Load configuration with environment-specific overrides.

        Args:
            base_file: Base configuration file
            environment: Environment name (e.g., 'development', 'production')

        Returns:
            Merged configuration dictionary
        """
        # Load base configuration
        base_config = self.load_file(base_file)

        # Determine environment
        if environment is None:
            environment = os.getenv("STRATEGY_LAB_ENV", "development")

        # Look for environment-specific file
        base_path = base_file.parent
        base_name = base_file.stem
        env_file = base_path / f"{base_name}.{environment}{base_file.suffix}"

        if env_file.exists():
            env_config = self.load_file(env_file)
            # Merge configurations
            return self._deep_merge(base_config, env_config)

        return base_config

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """Load a configuration template.

        Args:
            template_name: Name of the template

        Returns:
            Template configuration dictionary
        """
        template_dir = self.base_path / "configs" / "templates"
        template_file = template_dir / f"{template_name}.yaml"

        if not template_file.exists():
            # Try alternative locations
            alt_locations = [
                self.base_path / "templates" / f"{template_name}.yaml",
                Path(__file__).parent / "templates" / f"{template_name}.yaml",
            ]

            for alt_file in alt_locations:
                if alt_file.exists():
                    template_file = alt_file
                    break
            else:
                raise FileNotFoundError(f"Template not found: {template_name}")

        return self.load_file(template_file)

    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a configuration file.

        Args:
            file_path: Path to configuration file

        Returns:
            ValidationResult
        """
        try:
            config = self.load_file(file_path)
            return self.validator.validate(config)
        except Exception as e:
            result = ValidationResult()
            result.add_error(f"Failed to load file: {e}")
            return result

    def load_and_validate(self, file_path: Path) -> ConfigurationSet:
        """Load and validate a configuration file.

        Args:
            file_path: Path to configuration file

        Returns:
            Validated ConfigurationSet

        Raises:
            ValueError: If validation fails
        """
        config = self.load_file(file_path)
        result = self.validator.validate(config)

        if not result.is_valid:
            raise ValueError(f"Configuration validation failed:\n{result}")

        # Parse into ConfigurationSet
        return ConfigurationSet(**config)

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries, with override taking precedence.

        Args:
            base: Base dictionary
            override: Override dictionary

        Returns:
            Merged dictionary
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()

    def get_available_templates(self) -> List[str]:
        """Get list of available configuration templates.

        Returns:
            List of template names
        """
        templates = []

        # Check various template locations
        template_dirs = [
            self.base_path / "configs" / "templates",
            self.base_path / "templates",
            Path(__file__).parent / "templates",
        ]

        for template_dir in template_dirs:
            if template_dir.exists() and template_dir.is_dir():
                for file_path in template_dir.glob("*.yaml"):
                    if file_path.is_file():
                        templates.append(file_path.stem)

        return sorted(set(templates))

    def create_from_template(
        self,
        template_name: str,
        output_path: Path,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Create a new configuration file from a template.

        Args:
            template_name: Name of the template to use
            output_path: Path for the new configuration file
            overrides: Optional dictionary of values to override
        """
        # Load template
        template = self.load_template(template_name)

        # Apply overrides if provided
        if overrides:
            template = self._deep_merge(template, overrides)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write configuration
        with open(output_path, "w") as f:
            if output_path.suffix.lower() in {".yaml", ".yml"}:
                yaml.dump(template, f, default_flow_style=False, sort_keys=False)
            else:  # .json
                json.dump(template, f, indent=2)
