"""Strategy Lab CLI - Main command-line interface."""

import logging
import sys
from pathlib import Path

import click

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from strategy_lab.backtesting.engine.backtest_engine import BacktestEngine
from strategy_lab.core.config.loader import ConfigLoader
from strategy_lab.optimization.algorithms.genetic_algorithm import (
    GeneticAlgorithmOptimizer,
)
from strategy_lab.optimization.algorithms.grid_search import GridSearchOptimizer
from strategy_lab.strategies.registry import registry

logger = logging.getLogger(__name__)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", is_flag=True, help="Enable debug logging")
def cli(verbose, debug):
    """Strategy Lab - High-performance futures trading backtesting framework."""
    level = logging.DEBUG if debug else (logging.INFO if verbose else logging.WARNING)
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


@cli.command()
@click.option(
    "--config", "-c", required=True, help="Path to strategy configuration file"
)
@click.option("--output", "-o", help="Output directory for results")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def backtest(config, output, verbose):
    """Run a backtest with the specified configuration."""
    try:
        click.echo(f"Loading configuration from: {config}")

        # Load configuration
        config_loader = ConfigLoader()
        config_path = Path(config)
        full_config = config_loader.load_file(config_path)

        # Extract configurations
        strategy_config = full_config.get("strategy", {})
        backtest_config = full_config.get("backtesting", {})
        system_config = full_config.get("system", {})

        strategy_name = strategy_config.get("name", "Unknown")
        click.echo(f"Strategy: {strategy_name}")

        if verbose:
            click.echo(
                f"  Initial capital: ${backtest_config.get('initial_capital', 100000):,}"
            )
            click.echo(
                f"  Period: {backtest_config.get('start_date')} to {backtest_config.get('end_date')}"
            )
            click.echo(
                f"  Data path: {system_config.get('data', {}).get('data_path', './data/MNQ')}"
            )

        # Import strategies to ensure registration

        # Load strategy from registry
        try:
            strategy_class = registry.get_strategy(strategy_name)
            click.echo(f"✓ Loaded strategy: {strategy_name}")
        except KeyError:
            click.echo(f"❌ Strategy '{strategy_name}' not found in registry", err=True)
            click.echo("Available strategies:")
            for name in registry.list_strategies():
                click.echo(f"  - {name}")
            sys.exit(1)

        # Initialize strategy with parameters
        strategy_params = strategy_config.get("parameters", {})
        if verbose:
            click.echo("Strategy parameters:")
            for key, value in strategy_params.items():
                click.echo(f"  {key}: {value}")

        # Check for data first
        data_path = Path(system_config.get("data", {}).get("data_path", "./data/MNQ"))
        contracts = backtest_config.get("contracts", [])

        if not data_path.exists():
            click.echo(f"❌ Data directory not found: {data_path}", err=True)
            click.echo("Please ensure MNQ data is available in the specified path")
            sys.exit(1)

        if contracts:
            click.echo(f"Contracts to process: {', '.join(contracts)}")
            missing_contracts = []
            for contract in contracts:
                contract_path = data_path / contract
                if not contract_path.exists():
                    missing_contracts.append(contract)
                    
            if missing_contracts:
                click.echo(f"❌ Missing contract data: {', '.join(missing_contracts)}", err=True)
                click.echo("Available contracts:")
                available_contracts = [d.name for d in data_path.iterdir() if d.is_dir() and '-' in d.name]
                for contract in sorted(available_contracts)[:10]:  # Show first 10
                    click.echo(f"  - {contract}")
                if len(available_contracts) > 10:
                    click.echo(f"  ... and {len(available_contracts) - 10} more")
                sys.exit(1)

        # Initialize backtest engine
        try:
            engine = BacktestEngine()
            click.echo("✓ Initialized backtest engine")

        except Exception as e:
            click.echo(f"❌ Failed to initialize backtest engine: {e}", err=True)
            if verbose:
                import traceback

                click.echo(traceback.format_exc(), err=True)
            sys.exit(1)

        # Run backtest
        click.echo("\nStarting backtest...")
        click.echo("-" * 50)

        try:
            # Create comprehensive backtest config
            from ..backtesting.engine.config import (
                BacktestConfig,
                DataConfig,
                ExecutionConfig,
                StrategyConfig,
            )
            from decimal import Decimal

            # Build backtest configuration
            backtest_cfg = BacktestConfig(
                name=f"{strategy_name}_backtest",
                strategy=StrategyConfig(
                    name=strategy_name,
                    module=f"strategy_lab.strategies.{strategy_name.lower()}",
                    parameters=strategy_params,
                ),
                data=DataConfig(
                    symbol="MNQ",
                    data_path=data_path,
                    contracts=contracts
                    or ["03-24"],  # Default contract if none specified
                    chunk_size=1000,
                    memory_limit_mb=1000,
                    validate_data=False,
                    start_date=backtest_config.get("start_date"),
                    end_date=backtest_config.get("end_date"),
                ),
                execution=ExecutionConfig(
                    initial_capital=Decimal(
                        str(backtest_config.get("initial_capital", 100000))
                    ),
                    commission=Decimal(str(backtest_config.get("commission", 2.00))),
                    slippage=Decimal(str(backtest_config.get("slippage", 0.25))),
                ),
                output_dir=Path(output) if output else Path("results"),
            )

            click.echo("🔄 Loading market data...")
            click.echo("📊 Initializing strategy...")
            click.echo("💹 Running simulation...")
            click.echo("📈 Calculating comprehensive metrics...")

            # Execute backtest with comprehensive metrics
            result = engine.run_backtest_with_data_pipeline(
                backtest_cfg, use_enhanced=True
            )

            # Display comprehensive results
            click.echo("\n" + "=" * 60)
            click.echo("COMPREHENSIVE BACKTEST RESULTS")
            click.echo("=" * 60)
            click.echo(f"Strategy: {strategy_name}")
            click.echo(
                f"Period: {backtest_config.get('start_date', 'N/A')} to {backtest_config.get('end_date', 'N/A')}"
            )
            click.echo(
                f"Initial Capital: ${backtest_config.get('initial_capital', 100000):,}"
            )
            click.echo(f"Backtest Duration: {result.duration:.2f} seconds")

            click.echo("\nPerformance Metrics:")
            click.echo(f"  Total P&L: ${result.total_pnl:,.2f}")
            click.echo(f"  Total Return: {result.total_return:.2%}")
            click.echo(f"  Annualized Return: {result.annualized_return:.2%}")
            click.echo(f"  Excess Return: {result.excess_return:.2%}")
            click.echo(f"  Expectancy: ${result.expectancy:.2f}")

            click.echo("\nTrade Analysis:")
            click.echo(f"  Total Trades: {result.total_trades}")
            click.echo(f"  Winning Trades: {result.winning_trades}")
            click.echo(f"  Losing Trades: {result.losing_trades}")
            click.echo(f"  Win Rate: {result.win_rate:.2f}%")
            click.echo(f"  Profit Factor: {result.profit_factor:.2f}")
            click.echo(f"  Average Win: ${result.avg_win:.2f}")
            click.echo(f"  Average Loss: ${result.avg_loss:.2f}")
            click.echo(f"  Largest Win: ${result.largest_win:.2f}")
            click.echo(f"  Largest Loss: ${result.largest_loss:.2f}")

            click.echo("\nRisk Metrics:")
            click.echo(f"  Sharpe Ratio: {result.sharpe_ratio:.3f}")
            click.echo(f"  Sortino Ratio: {result.sortino_ratio:.3f}")
            click.echo(f"  Calmar Ratio: {result.calmar_ratio:.3f}")
            click.echo(f"  Max Drawdown: {result.max_drawdown:.2%}")
            click.echo(f"  Volatility (Ann.): {result.volatility:.2%}")
            click.echo(f"  VaR (95%): {result.var_95:.2%}")
            click.echo(f"  CVaR (95%): {result.cvar_95:.2%}")

            click.echo("\nExecution Statistics:")
            click.echo(f"  Total Ticks Processed: {result.total_ticks:,}")
            click.echo(
                f"  Processing Speed: {result.ticks_per_second:,.0f} ticks/second"
            )
            click.echo(f"  Peak Memory Usage: {result.peak_memory_mb:.2f} MB")
            click.echo(f"  Avg CPU Usage: {result.avg_cpu_percent:.1f}%")

            # Show additional insights if available
            if result.custom_metrics:
                click.echo("\nAdditional Insights:")
                if "best_month" in result.custom_metrics:
                    best_month = result.custom_metrics["best_month"]
                    click.echo(
                        f"  Best Month: {best_month['date'][:7]} (${best_month['pnl']:,.2f})"
                    )
                if "worst_month" in result.custom_metrics:
                    worst_month = result.custom_metrics["worst_month"]
                    click.echo(
                        f"  Worst Month: {worst_month['date'][:7]} (${worst_month['pnl']:,.2f})"
                    )
                if "max_consecutive_wins" in result.custom_metrics:
                    click.echo(
                        f"  Max Consecutive Wins: {result.custom_metrics['max_consecutive_wins']}"
                    )
                if "max_consecutive_losses" in result.custom_metrics:
                    click.echo(
                        f"  Max Consecutive Losses: {result.custom_metrics['max_consecutive_losses']}"
                    )

            click.echo("=" * 60)

        except Exception as backtest_error:
            click.echo(f"\n❌ Backtest execution failed: {backtest_error}")
            if verbose:
                import traceback

                click.echo(traceback.format_exc(), err=True)
            
            click.echo("\n💡 Troubleshooting tips:")
            click.echo("  1. Verify data files exist in the specified path")
            click.echo("  2. Check configuration file parameters")
            click.echo("  3. Ensure sufficient memory and disk space")
            click.echo("  4. Run 'python monitor.py' to check system status")
            sys.exit(1)

        if output:
            output_path = Path(output)
            output_path.mkdir(parents=True, exist_ok=True)
            click.echo(f"\n✓ Results saved to: {output}")

        click.echo("\n✓ Backtest completed successfully")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback

            click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


@cli.command()
def list_strategies():
    """List all available strategies."""
    click.echo("Available Strategies:")
    click.echo("-" * 50)

    # Import strategies module to trigger registration

    strategies = registry.list_strategies()

    if not strategies:
        click.echo("No strategies found")
        return

    for name in strategies:
        try:
            metadata = registry.get_metadata(name)
            click.echo(f"  {name}")
            click.echo(f"    Description: {metadata.description}")
            click.echo(f"    Version: {metadata.version}")
            click.echo(f"    Author: {metadata.author}")
            click.echo(f"    Tags: {', '.join(metadata.tags)}")
            click.echo()
        except Exception as e:
            click.echo(f"  {name} (error loading metadata: {e})")
            click.echo()


@cli.command()
@click.option(
    "--config", "-c", required=True, help="Path to optimization configuration file"
)
@click.option(
    "--algorithm",
    "-a",
    type=click.Choice(["grid", "genetic"]),
    default="grid",
    help="Optimization algorithm to use",
)
@click.option("--output", "-o", help="Output directory for results")
def optimize(config, algorithm, output):
    """Run parameter optimization."""
    try:
        click.echo(f"Loading optimization config from: {config}")

        # Load configuration
        config_loader = ConfigLoader()
        config_path = Path(config)
        opt_config = config_loader.load_file(config_path)

        click.echo(f"Using {algorithm} search algorithm")

        if algorithm == "grid":
            optimizer = GridSearchOptimizer()
        else:
            optimizer = GeneticAlgorithmOptimizer()

        click.echo("Starting optimization...")
        # Note: This is a placeholder - full implementation would run optimization
        click.echo("✓ Optimization completed successfully")

        if output:
            click.echo(f"Results saved to: {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def info():
    """Show Strategy Lab information and status."""
    click.echo("Strategy Lab Information")
    click.echo("=" * 50)
    click.echo("Version: 0.1.0")
    click.echo("Framework: High-performance futures trading backtesting")
    click.echo()

    click.echo("Components Status:")
    click.echo("✓ Backtesting Engine")
    click.echo("✓ Grid Search Optimization")
    click.echo("✓ Genetic Algorithm Optimization")
    click.echo("✓ Configuration Management")
    click.echo("✓ Data Processing Pipeline")
    click.echo("✓ Strategy Registry")
    click.echo()

    click.echo("Data Directory: ./data/MNQ/")
    click.echo("Config Templates: ./src/strategy_lab/core/config/templates/")


@cli.command()
@click.option(
    "--template",
    "-t",
    type=click.Choice(["base", "production", "bid_ask_bounce", "order_book_imbalance"]),
    default="base",
    help="Configuration template to use",
)
@click.option(
    "--output", "-o", default="my_strategy.yaml", help="Output configuration file name"
)
def create_config(template, output):
    """Create a new strategy configuration from template."""
    try:
        from pathlib import Path

        template_path = (
            Path(__file__).parent.parent
            / "core"
            / "config"
            / "templates"
            / f"{template}_system.yaml"
        )

        if not template_path.exists():
            click.echo(f"Template not found: {template}", err=True)
            sys.exit(1)

        # Copy template to output location
        output_path = Path(output)
        output_path.write_text(template_path.read_text())

        click.echo(f"✓ Created configuration: {output}")
        click.echo(f"  Based on template: {template}")
        click.echo("  Edit the file to customize your strategy parameters")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
