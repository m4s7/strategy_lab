# Strategy Lab - Futures Trading Backtesting Framework

A modular backtesting and optimization framework for CME MNQ futures trading strategies, built with Python and VectorBT.

## Features

- **High-Performance Backtesting**: Process millions of ticks per day with VectorBT
- **Modular Strategy Design**: Pluggable strategy architecture for easy development
- **Trading Strategies Bases**: 
  - Scalping
  - Based on Level 1 and Level 2 Ticket Data of MNQ Future
  - e.g. Order Book Scalper Strategy with Level 2 data support
- **Real-time Monitoring**: Monitoring decoupled from backtesting threads
- **Advanced Optimization**: Grid search, genetic algorithms, and walk-forward analysis
- **Production Ready**: Full API, comprehensive testing, and deployment configurations
- **Planed usage**:
  - Single User (Just me)
  - Save Environment (Ubuntu Server with firewall behind a VPN)
  - Domain: lab.m4s8.dev

## Project Structure (Draft)

```
strategy_lab/
  src/
    core/           # Core data management and configuration
    strategies/     # Trading strategy implementations
    backtesting/    # Backtesting engine and metrics
    optimization/   # Parameter optimization algorithms
    api/            # REST API and WebSocket server
  tests/            # Unit and integration tests
  data/             # Parquet Files
```

## Quick Start

### Prerequisites

- Python 3.12+
- uv package manager
- Access to MNQ tick data at `./data/MNQ`

### Installation

```bash
# Project is already initialized with uv
# Install dependencies
uv sync

# Run tests
uv run pytest
```

### Development

```bash
# Run tests with coverage
uv run pytest --cov=src

# Format code
uv run black src tests

# Lint code
uv run ruff check src tests

# Type checking
uv run mypy src
```

## Data Structure

See `./knowledge-base/data.md`
