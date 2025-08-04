# Strategy Lab Quick Start

> **TL;DR**: Get Strategy Lab running in 5 minutes

## 🚀 Installation & Setup

```bash
# 1. Setup environment
git clone <repo-url> && cd strategy_lab
uv venv && source .venv/bin/activate
uv sync

# 2. Verify installation
uv run python quick_start.py
```

## 📋 Essential Commands

```bash
# System info
uv run strategy-lab info

# Create configuration
uv run strategy-lab create-config --output my_config.yaml

# List available strategies
uv run strategy-lab list-strategies

# Run backtest
uv run strategy-lab backtest --config my_config.yaml --verbose

# Optimize parameters
uv run strategy-lab optimize --config opt_config.yaml --algorithm grid
```

## ⚡ Quick Test Run

```bash
# 1. Create a basic config
uv run strategy-lab create-config --template base --output test.yaml

# 2. Edit test.yaml (set your parameters)

# 3. Run backtest
uv run strategy-lab backtest --config test.yaml --verbose
```

## 📁 File Structure

```
strategy_lab/
├── src/strategy_lab/           # Core framework
├── configs/                    # Your configurations
├── data/MNQ/                   # Market data (Parquet files)
├── docs/                       # Documentation
└── quick_start.py              # Demo script
```

## 🎯 Available Templates

- `base` - Basic configuration
- `production` - Production setup
- `bid_ask_bounce` - Scalping strategy
- `order_book_imbalance` - Microstructure strategy

## 📊 Built-in Strategies

- **SimpleMAStrategy**: Moving average crossover
- **BidAskBounceStrategy**: Bid-ask spread scalping
- **OrderBookImbalanceStrategy**: Order flow analysis

## 🔧 Development

```bash
# Run tests
uv run pytest

# Code quality
uv run black src tests
uv run ruff check src tests
uv run mypy src
```

## 🆘 Need Help?

- **Full docs**: `docs/getting-started.md`
- **System check**: `uv run python quick_start.py`
- **CLI help**: `uv run strategy-lab --help`
- **Examples**: Check `configs/` directory

---

**Ready to trade? Start with a simple MA strategy and build from there!** 🎉
