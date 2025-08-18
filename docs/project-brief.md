# Project Brief: Strategy Lab - Futures Backtesting Framework

## Executive Summary

The Strategy Lab is a personal modular backtesting and optimization framework specifically designed for developing and testing high-frequency scalping strategies on CME MNQ futures. Built on rust and hftbacktest, it provides a systematic approach to strategy development with production-grade performance for processing millions of ticks.

**Primary problem being solved:** Need for a custom, high-performance backtesting environment tailored to personal trading style and scalping strategy development workflow.

**Target market:** Single user (personal use only)

**Key value proposition:** A tailored framework that integrates preferred tools (rust, hftbacktest) with custom workflows for rapid strategy iteration, comprehensive backtesting, and systematic optimization of scalping strategies.

## Problem Statement

Currently, there's no accessible backtesting solution that can efficiently process large volumes of Level 1 and Level 2 tick data for MNQ futures. Existing platforms either:

- Cannot handle the massive tick-by-tick datasets with full order book depth
- Lack the performance to test strategies on years of historical Level 2 data
- Don't provide the granular market microstructure visibility needed for scalping

Without proper Level 1 and Level 2 backtesting capabilities, it's impossible to develop and validate scalping strategies that rely on order book dynamics, making it risky to deploy strategies in live trading.

The impact is the inability to systematically develop profitable strategies with confidence in their real-world performance.

## Proposed Solution

Build a high-performance backtesting framework using rust and hftbacktest that can process both Level 1 (trades) and Level 2 (order book) tick data for MNQ futures. The framework will feature:

- **Modular architecture** for pluggable strategies, allowing rapid development of new scalping approaches
- **Efficient data handling** capable of processing millions of ticks per day from Parquet files
- **Order book reconstruction** for accurate Level 2 analysis and strategy signals
- **Comprehensive metrics** for evaluating strategy performance and market microstructure impact

This solution provides a personal research environment for systematic strategy development, with clean outputs that can inform manual live trading decisions.

## Target Users

### Primary User Segment: Solo Quantitative Trader

**Profile:**
- Individual trader focused on MNQ futures scalping
- Experienced programmer (20 years) with beginner-level rust skills
- Has access to historical Level 1 and Level 2 tick data
- Follows systematic approach: idea → refinement → parameter optimization

**Current behaviors and workflows:**
- Starts with rough trading ideas based on market observations
- Iteratively refines strategies through conceptual analysis
- Lacks tools to validate and optimize parameters with real data

**Specific needs:**
- rust-friendly framework with clear documentation and examples
- Fast processing of massive tick datasets
- Built-in parameter optimization capabilities
- Clean, understandable code structure despite rust beginner status

**Goals:**
- Develop profitable scalping strategies through systematic backtesting
- Efficiently move from idea to optimized strategy
- Leverage programming experience while learning rust best practices

## Goals & Success Metrics

### Primary Objective
- Find 1-2 profitable scalping strategies that are worth trading with real capital

### Success Definition
- The framework enables systematic testing of strategy ideas
- Backtesting results provide enough confidence to trade the strategies live
- Performance is fast enough that testing iterations don't become a bottleneck

### Practical Measures
- Strategies show consistent profitability across different market conditions in backtests
- The framework is reliable and easy to use for ongoing strategy development
- You trust the backtest results enough to risk real capital

## MVP Scope

### Core Features (Must Have)
- **Data ingestion** from Parquet files for Level 1 and Level 2 MNQ data
- **Basic scalping strategy template** with clear structure for modifications
- **Order book reconstruction** and event processing via hftbacktest
- **Core performance metrics**: PnL, trades, win rate, drawdown
- **Advanced optimization algorithms**: 
  - Grid search for exhaustive parameter testing
  - Genetic algorithms for efficient parameter space exploration
  - Walk-forward analysis for out-of-sample validation
- **Example strategies**: At least 2 working examples (e.g., order book imbalance, bid-ask bounce)

### Out of Scope for MVP
- Real-time monitoring dashboard
- Multi-instrument support
- Advanced visualization beyond basic plots
- Live trading integration
- Strategy combination/portfolio features

### MVP Success Criteria
- Can load and process a full day of MNQ tick data
- Can implement and test a new scalping strategy in < 30 minutes
- Can optimize strategy parameters using multiple algorithms
- Walk-forward analysis validates strategy robustness

## Post-MVP Vision

### Phase 2 Features
- Enhanced visualization tools for strategy analysis
- Multi-timeframe analysis capabilities
- Strategy performance comparison tools
- Automated report generation

### Long-term Vision (1-2 years)
- Comprehensive personal trading research platform
- Library of tested and validated scalping strategies
- Sophisticated market regime detection
- Integration with market data providers for continuous updates

### Expansion Opportunities
- Support for other futures contracts (ES, NQ)
- Additional strategy types beyond scalping
- Machine learning integration for pattern discovery

## Technical Considerations

### Platform Requirements
- **Target Platform:** Ubuntu Server
- **Environment:** Local development with potential for server deployment
- **Performance Requirements:** Process tick data as fast as hftbacktest allows (likely 100K-500K ticks/second depending on strategy complexity)
- **Data Storage:** Local Parquet files in `./data/MNQ` directory

### Technology Preferences
- **Language:** Rust
- **Core Library:** hftbacktest for backtesting engine

### Architecture Considerations
- **Repository Structure:** Monorepo with clear module separation
- **Service Architecture:** Monolithic application with modular components
- **Data Pipeline:** Parquet → DataFrame → hftbacktest engine
- **Optimization Service:** Separate threads/processes for parallel optimization

### Additional Technical Needs
- **Configuration:** YAML/JSON for strategy parameters

## Constraints & Assumptions

### Constraints
- **Budget:** Personal project (no specific budget constraints)
- **Timeline:** No hard deadline, development at your own pace (8h/week)
- **Resources:** Solo developer
- **Technical:** rust beginner level, but experienced programmer
- **Processing Time:** Multi-hour backtests are acceptable
- **Data Volume:** Files with ~15M rows of mixed Level 1 & Level 2 data
- **Backtest Period:** Months to years of historical data

### Key Assumptions
- Historical MNQ tick data (Level 1 & 2) is already available in Parquet format
- Files contain ~15M rows each (mixed tick types)
- hftbacktest can handle months/years of data with reasonable memory usage
- Overnight or long-running backtests are acceptable
- Ubuntu server has sufficient memory for large datasets (16 CPUs, 64GB RAM, 2TB SSD)

## Risks & Open Questions

### Key Risks
- **Memory Management:** Processing years of tick data may require careful memory handling (though 64GB helps significantly)
- **Strategy Overfitting:** With extensive optimization, strategies might overfit to historical data
- **Data Complexity:** Multiple contract months need to be handled correctly (rollover logic)

### Open Questions
✓ All resolved!
- Data format is well-documented with clear schema
- Server has ample resources for processing
- File organization by contract month is clear

### Areas Needing Further Research
- Optimal contract rollover handling for continuous backtesting
- Efficient order book reconstruction from operation codes (Add/Update/Remove)
- Parallel processing strategies using 16 CPUs for optimization

## Appendices

### A. Research Summary

**Data Structure Insights:**
- Mixed Level 1 & Level 2 data in single Parquet files
- ~7-10M rows per trading day (mostly L2 data)
- Multiple contract months need handling (e.g., 06-19, 09-19)
- Rich tick type information via MDT field

**Technical Feasibility:**
- 64GB RAM can handle months of data in memory
- 16 CPUs enable parallel parameter optimization
- hftbacktest should handle the tick format efficiently

### B. References
- hftbacktest documentation: https://github.com/nkaz001/hftbacktest
- Project data location: `./data/MNQ`
- Data schema reference: `./MNQ_parquet_files.json`

## Next Steps

### Immediate Actions
1. Save this Project Brief as `docs/project-brief.md` in your project
2. Create PRD with detailed requirements and epic structure
3. Begin architecture design focusing on data pipeline and optimization

### PM Handoff
This Project Brief provides the full context for Strategy Lab. Please start in 'PRD Generation Mode', review the brief thoroughly to work with the user to create the PRD section by section as the template indicates, asking for any necessary clarification or suggesting improvements.