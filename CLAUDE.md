# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Strategy Lab is a modular backtesting and optimization framework for CME MNQ futures trading strategies, built with Python and VectorBT. The project contains extensive MNQ (Micro E-mini NASDAQ-100 futures) market data in Parquet format and uses the BMad Method (Business Automation and Development) for structured development.

### Deployment Environment
- **Single User**: Personal trading research environment
- **Infrastructure**: Ubuntu Server with firewall behind VPN
- **Domain**: lab.m4s8.dev

## Key Commands

### Development Commands
```bash
# Install dependencies (using uv package manager)
uv sync

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_specific.py

# Run a single test function
uv run pytest tests/test_specific.py::test_function_name

# Run tests with coverage
uv run pytest --cov=src

# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type checking
uv run mypy src
```

### BMad Framework Commands
```bash
# Access BMad help and available commands
*help

# Execute specific tasks
*task {task_name}

# Create documents from templates
*create-doc {template_name}

# Run quality checklists
*execute-checklist {checklist_name}

# Access knowledge base
*kb
```

## Architecture

### Trading Strategy Focus
The framework focuses on scalping strategies using:
- Level 1 tick data (best bid/ask, trades)
- Level 2 order book data (market depth)
- Example: Order Book Scalper Strategy

### Planned Project Structure
```
strategy_lab/
  src/
    core/           # Core data management and configuration
    strategies/     # Scalping strategy implementations
    backtesting/    # Backtesting engine and metrics
    optimization/   # Parameter optimization algorithms
    api/            # REST API and WebSocket server
  tests/            # Unit and integration tests
  data/             # Parquet files (not in git)
```

### Data Structure
Market data schema (Level 1 and Level 2 data):
- **level**: Data level indicator (string)
- **mdt**: Market Data Type
  - 0=Ask, 1=Bid, 2=Last, 3=DailyHigh, 4=DailyLow
  - 5=DailyVolume, 6=LastClose, 7=Opening, 8=OpenInterest, 9=Settlement
- **timestamp**: Nanosecond precision timestamps
- **price**: Decimal128 with 13 digits, 2 decimal places
- **volume**: Int32 trade/quote volume
- **operation**: Order book operations (0=Add, 1=Update, 2=Remove)
- **depth**: Order book depth level
- **market_maker**: Market maker identification

Data files are organized by contract month in `data/MNQ/` (e.g., "03-20", "06-24"). File index with metadata is in `data/MNQ_parquet_files.json`.

### BMad Framework Structure
The `.bmad-core/` directory contains the development methodology framework:
- `agents/`: AI agent definitions for different development roles
- `tasks/`: Executable workflows
- `templates/`: Document generation templates
- `checklists/`: Quality assurance procedures
- `data/`: Framework knowledge base
- `workflows/`: Development process definitions

## Prerequisites

- Python 3.12+
- uv package manager
- Access to MNQ tick data at `./data/MNQ`

## Important Notes

- The project is in early development stage - strategy implementations are being built
- Market data spans May 2019 to March 2025 with millions of ticks per day
- All timestamps are in nanosecond precision for high-frequency analysis
- Data files should not be committed to git (see .gitignore)
- Knowledge base documents in `knowledge-base/` provide detailed information about:
  - Trading NQ and MNQ futures
  - VectorBT framework
  - Data structure details
  - Trading strategies