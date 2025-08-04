#!/usr/bin/env python3
"""Quick start script for Strategy Lab - demonstrates basic usage."""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def main():
    """Demonstrate Strategy Lab components."""
    print("🚀 Strategy Lab Quick Start")
    print("=" * 50)

    try:
        # Test imports
        print("Testing component imports...")

        from strategy_lab.backtesting.engine.backtest_engine import BacktestEngine

        print("✓ Backtesting Engine")

        from strategy_lab.strategies.examples.simple_ma_strategy import SimpleMAStrategy

        print("✓ Simple MA Strategy")

        from strategy_lab.optimization.algorithms.grid_search import GridSearchOptimizer

        print("✓ Grid Search Optimizer")

        from strategy_lab.optimization.algorithms.genetic_algorithm import (
            GeneticAlgorithmOptimizer,
        )

        print("✓ Genetic Algorithm Optimizer")

        from strategy_lab.core.config.loader import ConfigLoader

        print("✓ Configuration Loader")

        print("\n✅ All core components loaded successfully!")

        # Show available templates
        print("\n📋 Available Configuration Templates:")
        template_dir = src_path / "strategy_lab" / "core" / "config" / "templates"
        if template_dir.exists():
            for template in template_dir.glob("*.yaml"):
                print(f"  • {template.name}")

        print("\n🎯 Next Steps:")
        print("1. Install the package: uv pip install -e .")
        print("2. Try the CLI: strategy-lab --help")
        print("3. Create a config: strategy-lab create-config --output my_config.yaml")
        print("4. Run a backtest: strategy-lab backtest --config my_config.yaml")
        print("5. List strategies: strategy-lab list-strategies")

        # Basic component test
        print("\n🧪 Basic Component Test:")
        try:
            engine = BacktestEngine()
            print("✓ BacktestEngine initialized")

            strategy = SimpleMAStrategy()
            print("✓ SimpleMAStrategy initialized")

            config_loader = ConfigLoader()
            print("✓ ConfigLoader initialized")

        except Exception as e:
            print(f"⚠️  Component test failed: {e}")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print(
            "Make sure you're in the strategy_lab directory and dependencies are installed"
        )
        return 1

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    print("\n🎉 Strategy Lab is ready to use!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
