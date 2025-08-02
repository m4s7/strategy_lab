# Strategy Lab

A high-performance futures trading backtesting framework for developing and optimizing scalping strategies on MNQ (Micro E-mini NASDAQ-100) futures.

## Overview

Strategy Lab is a modular Python framework designed for:
- High-frequency tick data processing (100K-500K ticks/second)
- Level 1 and Level 2 market data analysis
- Rapid strategy development and testing
- Comprehensive parameter optimization
- Robust out-of-sample validation

## Features

- **High Performance**: Process millions of ticks per day with optimized data structures
- **Modular Architecture**: Pluggable strategy system for rapid development
- **Comprehensive Data Support**: Level 1 (trades) and Level 2 (order book) data
- **Advanced Optimization**: Grid search, genetic algorithms, and walk-forward analysis
- **Risk Management**: Built-in position sizing, stop-loss, and drawdown controls
- **Detailed Analytics**: Performance metrics, trade analysis, and visualization

## Installation

### Prerequisites

- Python 3.12 or higher
- 64GB RAM recommended for processing large datasets
- Ubuntu/Linux environment

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/strategy_lab.git
cd strategy_lab
```

2. Create a virtual environment using uv:
```bash
uv venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
uv pip install -e ".[dev]"
```

## Quick Start

1. Place your MNQ tick data in the `data/MNQ/` directory organized by contract month
2. Create a strategy configuration in `configs/`
3. Run a backtest:
```bash
strategy-lab backtest --config configs/my_strategy.yaml
```

## Project Structure

```
strategy_lab/
├── src/strategy_lab/       # Main package source
│   ├── core/              # Core framework components
│   ├── data/              # Data processing and ingestion
│   ├── strategies/        # Trading strategy implementations
│   ├── backtesting/       # Backtesting engine
│   ├── optimization/      # Parameter optimization
│   ├── analysis/          # Performance analysis
│   └── utils/            # Utility functions
├── tests/                 # Test suite
├── configs/              # Configuration files
├── docs/                 # Documentation
└── data/                 # Market data (gitignored)
```

## Development

### Code Style

This project uses:
- `black` for code formatting
- `ruff` for linting
- `mypy` for type checking
- `pytest` for testing

Run quality checks:
```bash
black src tests
ruff check src tests
mypy src
pytest
```

### Testing

Run the test suite:
```bash
pytest tests/
```

With coverage:
```bash
pytest --cov=src/strategy_lab tests/
```

## Documentation

See the `docs/` directory for:
- Architecture documentation
- Strategy development guide
- API reference
- Performance optimization tips

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run quality checks
5. Submit a pull request

## Support

For questions and support:
- Check the documentation in `docs/`
- Review examples in `configs/`
- Open an issue on GitHub
