# UV Package Manager Usage Guide

## Overview
uv is an extremely fast Python package and project manager, written in Rust. It serves as a unified replacement for pip, pip-tools, pipx, poetry, pyenv, twine, virtualenv, and more. uv provides both a pip-compatible CLI and a modern project management interface with lockfiles and workspace support.

## Installation

### Standalone Installers (Recommended)
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Via Package Managers
```bash
# With pip
pip install uv

# With pipx
pipx install uv
```

### Self-Update
```bash
uv self update
```

## Core Commands Overview

### Project Management
- `uv init` - Initialize a new Python project
- `uv add` - Add dependencies to project
- `uv remove` - Remove dependencies from project
- `uv sync` - Install project dependencies
- `uv lock` - Generate/update lockfile
- `uv run` - Run commands in project environment
- `uv build` - Build project distributions
- `uv publish` - Publish to PyPI

### Python Version Management
- `uv python install` - Install Python versions
- `uv python list` - List available Python versions
- `uv python pin` - Pin Python version for project

### Virtual Environment Management
- `uv venv` - Create virtual environment
- `uv venv --python 3.11` - Create venv with specific Python

### pip Interface (Drop-in Replacement)
- `uv pip install` - Install packages
- `uv pip uninstall` - Remove packages
- `uv pip freeze` - List installed packages
- `uv pip compile` - Generate requirements.txt
- `uv pip sync` - Install from requirements.txt

### Tool Management
- `uv tool install` - Install CLI tools globally
- `uv tool run` / `uvx` - Run tools in isolated environments
- `uv tool list` - List installed tools
- `uv tool uninstall` - Remove tools

## Project Workflow Examples

### Starting a New Project
```bash
# Initialize new project
uv init my-project
cd my-project

# Add dependencies
uv add requests pandas
uv add pytest --dev  # Development dependency

# Run commands in project environment
uv run python script.py
uv run pytest

# Generate lockfile
uv lock

# Install all dependencies (including from lockfile)
uv sync
```

### Working with Existing Projects
```bash
# Clone/enter existing project
cd existing-project

# Install dependencies from pyproject.toml and lockfile
uv sync

# Add new dependency
uv add numpy

# Run in project environment
uv run python main.py
```

### Python Version Management
```bash
# Install Python versions
uv python install 3.11 3.12

# List available versions
uv python list

# Pin Python version for project
uv python pin 3.11

# Create venv with specific Python
uv venv --python 3.12
```

## pip Interface (Migration from pip)

### Direct pip Replacements
```bash
# Old pip commands → New uv commands
pip install requests → uv pip install requests
pip uninstall requests → uv pip uninstall requests
pip freeze → uv pip freeze
pip list → uv pip list
```

### Requirements File Workflow
```bash
# Compile requirements.in to requirements.txt
uv pip compile requirements.in --output-file requirements.txt

# Install from requirements.txt
uv pip sync requirements.txt

# Create virtual environment first
uv venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows

# Install in virtual environment
uv pip install -r requirements.txt
```

### Advanced pip Features
```bash
# Universal resolution (platform-independent)
uv pip compile requirements.in --universal

# Install with specific index
uv pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install with constraints
uv pip install requests --constraint constraints.txt
```

## Tool Management (pipx Replacement)

### Running Tools Temporarily
```bash
# Run tool without installing (ephemeral)
uvx black .
uvx --from requests python -c "import requests; print(requests.get('https://httpbin.org/json').json())"
```

### Installing Tools Globally
```bash
# Install tools globally
uv tool install black
uv tool install ruff
uv tool install jupyter

# List installed tools
uv tool list

# Run installed tool
black .
ruff check .

# Update tool
uv tool install black --upgrade

# Uninstall tool
uv tool uninstall black
```

## Script Management

### Inline Dependencies
Create a script with inline dependency metadata:
```python
# script.py
# /// script
# dependencies = ["requests", "rich"]
# ///

import requests
from rich import print

response = requests.get("https://api.github.com/user", headers={"User-Agent": "my-script"})
print(response.json())
```

Run with dependencies automatically managed:
```bash
uv run script.py
```

### Adding Dependencies to Scripts
```bash
# Add dependency to existing script
uv add --script script.py beautifulsoup4
```

## Configuration

### Global Configuration
uv looks for configuration in:
- `pyproject.toml` (project-specific)
- `uv.toml` (global or project)
- Environment variables (prefixed with `UV_`)

### Common Configuration Options
```toml
# pyproject.toml
[tool.uv]
# Package indexes
index-url = "https://pypi.org/simple"
extra-index-url = ["https://download.pytorch.org/whl/cpu"]

# Python preferences
python-preference = "managed"  # "only-managed", "managed", "system", "only-system"

# Resolution strategy
resolution = "highest"  # "highest", "lowest", "lowest-direct"

# Cache directory
cache-dir = "~/.cache/uv"

# Development dependencies
dev-dependencies = [
    "pytest>=6.0",
    "black",
    "ruff",
]
```

### Environment Variables
```bash
# Common environment variables
export UV_INDEX_URL="https://pypi.org/simple"
export UV_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"
export UV_PYTHON_PREFERENCE="managed"
export UV_RESOLUTION="highest"
export UV_COMPILE_BYTECODE="1"
```

## Advanced Features

### Workspaces
```toml
# Root pyproject.toml
[tool.uv.workspace]
members = ["packages/*", "apps/web"]
```

### Dependency Groups
```toml
# pyproject.toml
[dependency-groups]
test = ["pytest", "coverage"]
lint = ["black", "ruff"]
docs = ["sphinx", "furo"]
```

Install specific groups:
```bash
uv sync --group test
uv sync --group lint --group test
```

### Platform-Specific Dependencies
```toml
[project]
dependencies = [
    "requests",
    "pywin32; sys_platform == 'win32'",
    "uvloop; sys_platform != 'win32'",
]
```

### Index Configuration
```toml
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cu118"

[[tool.uv.index]]
name = "private"
url = "https://private.pypi.com/simple"
```

## Performance Features

### Caching
- Global cache shared across projects
- Network cache for package metadata
- Built distributions cached for reuse

### Parallel Operations
- Concurrent downloads
- Parallel installation
- Parallel builds

### Optimizations
- Fast dependency resolution with PubGrub
- Optimized wheel installation
- Copy-on-write linking when possible

## Common Workflows

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Install uv
  uses: astral-sh/setup-uv@v3

- name: Install dependencies
  run: uv sync --frozen

- name: Run tests
  run: uv run pytest
```

### Docker Integration
```dockerfile
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache
```

### Migration from Other Tools

#### From pip + venv
```bash
# Old workflow
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# New workflow
uv venv
uv pip sync requirements.txt
# or for projects: uv sync
```

#### From Poetry
```bash
# Poetry commands → uv equivalents
poetry install → uv sync
poetry add requests → uv add requests
poetry remove requests → uv remove requests
poetry run python script.py → uv run python script.py
poetry shell → source .venv/bin/activate (after uv sync)
```

#### From pipx
```bash
# pipx commands → uv equivalents
pipx install black → uv tool install black
pipx run black → uvx black
pipx list → uv tool list
pipx uninstall black → uv tool uninstall black
```

## Troubleshooting

### Common Issues

1. **Python Not Found**
   ```bash
   # Install Python with uv
   uv python install 3.11
   
   # Or specify Python path
   uv venv --python /usr/bin/python3.11
   ```

2. **Package Not Found**
   ```bash
   # Check index configuration
   uv pip install --dry-run package-name
   
   # Try different index
   uv pip install package-name --index-url https://pypi.org/simple
   ```

3. **Lock File Issues**
   ```bash
   # Regenerate lock file
   uv lock --upgrade
   
   # Force refresh
   uv sync --refresh
   ```

4. **Cache Issues**
   ```bash
   # Clear cache
   uv cache clean
   
   # Install without cache
   uv pip install package --no-cache
   ```

### Getting Help
```bash
# General help
uv --help

# Command-specific help
uv pip install --help
uv add --help

# Check version
uv --version
```

## Best Practices

1. **Use `uv sync` for reproducible installations**
2. **Pin Python versions with `uv python pin`**
3. **Use development dependencies appropriately**
4. **Leverage dependency groups for different environments**
5. **Keep lockfiles in version control**
6. **Use `uv run` instead of activating virtual environments**
7. **Configure indexes in `pyproject.toml` for team consistency**
8. **Use `uvx` for one-off tool executions**
9. **Prefer `uv tool install` for global CLI tools**
10. **Use `--frozen` in CI for speed and reproducibility**