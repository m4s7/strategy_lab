"""Test project infrastructure setup."""

import importlib
import subprocess
import sys
from pathlib import Path

import pytest


def test_python_version():
    """Test that Python version meets minimum requirements."""
    assert sys.version_info >= (3, 12), f"Python 3.12+ required, got {sys.version}"


def test_project_dependencies():
    """Test that all required dependencies are available."""
    # Test core dependencies
    required_packages = [
        "pandas",
        "pyarrow",
        "numpy",
        "scipy",
        "deap",
        "matplotlib",
        "pydantic",
        "yaml",
        "click",
        "psutil",
    ]

    for package in required_packages:
        try:
            if package == "yaml":
                importlib.import_module("yaml")
            else:
                importlib.import_module(package)
        except ImportError:
            pytest.fail(f"Required package '{package}' not installed")


def test_development_tools():
    """Test development tool configuration."""
    # Test that dev tools are installed
    dev_tools = ["black", "ruff", "mypy", "pytest"]

    for tool in dev_tools:
        result = subprocess.run(
            [tool, "--version"], check=False, capture_output=True, text=True
        )
        assert result.returncode == 0, f"Dev tool '{tool}' not properly installed"


def test_project_structure():
    """Test that project directory structure is correct."""
    project_root = Path(__file__).parent.parent.parent.parent

    # Required directories
    required_dirs = [
        "src/strategy_lab",
        "src/strategy_lab/cli",
        "src/strategy_lab/core",
        "src/strategy_lab/data",
        "src/strategy_lab/strategies",
        "src/strategy_lab/backtesting",
        "src/strategy_lab/optimization",
        "src/strategy_lab/analysis",
        "src/strategy_lab/utils",
        "tests",
        "docs",
        "configs",
        "scripts",
        "notebooks",
    ]

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Required directory '{dir_path}' does not exist"
        assert full_path.is_dir(), f"'{dir_path}' is not a directory"


def test_configuration_files():
    """Test that configuration files are valid."""
    project_root = Path(__file__).parent.parent.parent.parent

    # Required configuration files
    config_files = [
        "pyproject.toml",
        ".gitignore",
        ".pre-commit-config.yaml",
        "README.md",
        "LICENSE",
    ]

    for config_file in config_files:
        file_path = project_root / config_file
        assert file_path.exists(), f"Configuration file '{config_file}' missing"
        assert (
            file_path.stat().st_size > 0
        ), f"Configuration file '{config_file}' is empty"


def test_package_importability():
    """Test that the package can be imported."""
    try:
        import strategy_lab

        assert hasattr(strategy_lab, "__version__")
        assert strategy_lab.__version__ == "0.1.0"
    except ImportError:
        pytest.fail("Cannot import strategy_lab package")


def test_git_repository():
    """Test git repository configuration."""
    project_root = Path(__file__).parent.parent.parent.parent
    git_dir = project_root / ".git"

    # Note: This test will be skipped if not in a git repository
    if git_dir.exists():
        # Check gitignore includes data directories
        gitignore_path = project_root / ".gitignore"
        with gitignore_path.open() as f:
            gitignore_content = f.read()

        assert "data/" in gitignore_content, "data/ not in .gitignore"
        assert "logs/" in gitignore_content, "logs/ not in .gitignore"
        assert "results/" in gitignore_content, "results/ not in .gitignore"
        assert "*.parquet" in gitignore_content, "*.parquet not in .gitignore"
