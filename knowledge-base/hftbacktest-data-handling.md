# hftbacktest Implementation Guide: Architecture, Data Formats, and Production Patterns

hftbacktest has emerged as a powerful high-frequency trading backtesting framework with proven production deployments processing billions of market events. This comprehensive guide reveals the technical implementation details, architectural patterns, and real-world performance benchmarks essential for building modular HFT backtesting systems.

## Data format requirements for Level 2 order book data

hftbacktest mandates a strict **numpy structured array format** with an 8-field schema stored as compressed NPZ files. Each market event requires exactly these fields in order: event flags (uint64), exchange timestamp (int64 nanoseconds), local timestamp (int64 nanoseconds), price (float64), quantity (float64), order ID (uint64, zero for L2), and two reserved fields (int64 and float64).

The framework processes Level 2 data through **event-driven updates** where each bid or ask level change generates a separate event. Bid events use the `BUY_EVENT` flag while ask events use `SELL_EVENT`, both combined with `DEPTH_EVENT` and processing flags. A critical requirement is that all timestamps must be in nanoseconds with local timestamp always greater than or equal to exchange timestamp to ensure positive latency.

**Data preprocessing is mandatory** before use. The framework provides correction functions like `correct_local_timestamp()` and `correct_event_order()` to fix timestamp issues and ensure chronological ordering. Events with identical timestamps must follow specific rules: trades precede depth updates, and all events are sorted first by exchange timestamp, then by local timestamp.

The recommended file format is **compressed NPZ** (`.npz`), offering 70-80% size reduction compared to raw data. While the framework also supports uncompressed NPY format, it notably does not support Parquet, HDF5, or CSV formats natively. Converting from these formats requires custom preprocessing pipelines that transform data into the required event_dtype structure.

## Real-time monitoring implementation strategies

Real-time monitoring of hftbacktest backtests requires careful architectural decisions to maintain the framework's high-performance characteristics while providing visibility into execution progress. The core challenge lies in extracting state information without impacting the nanosecond-precision simulation engine.

The most effective pattern uses **queue-based communication** between the backtest process and monitoring components. Within the strategy loop, state snapshots are captured at regular intervals (typically every 1000-10000 ticks) and published to a non-blocking queue. This approach adds less than 1 microsecond overhead per update while ensuring the backtest continues uninterrupted even if monitoring systems lag.

For **thread-safe communication**, Python implementations leverage `queue.Queue` with `put_nowait()` operations, while Rust implementations use Tokio's mpsc channels. The monitoring thread consumes these updates and broadcasts them via WebSocket to connected dashboards, enabling real-time visualization of equity curves, positions, and order flow.

**Update frequencies** should balance information density with performance impact. High-frequency strategies typically update every 1-10 seconds of simulated time, translating to 1-10 Hz dashboard refresh rates - well within human perception limits. Each state snapshot contains essential metrics like timestamp, progress percentage, current position, equity, and order book state, serialized as JSON messages of 200-500 bytes.

For **multiple concurrent backtests**, a process pool executor manages separate backtest instances, each publishing to a shared progress queue. A central monitoring service aggregates updates and provides both WebSocket streams for real-time updates and REST endpoints for status queries. This architecture scales to dozens of simultaneous backtests while maintaining sub-millisecond monitoring overhead.

## Modular architecture patterns for HFT systems

Building a modular HFT backtesting system with hftbacktest requires a **layered architecture** that separates data processing, strategy execution, and optimization concerns. The most successful implementations follow a progressive optimization pipeline: Python prototypes → Numba JIT compilation → Rust production code.

The **data pipeline architecture** implements a four-stage process: ingestion → normalization → conversion → storage. A modular converter system handles multiple input formats (Parquet, CSV, FIX) through format-specific adapters that transform data into hftbacktest's NPZ format. Processed files follow a consistent naming convention (`{symbol}_{YYYYMMDD}.npz`) with separate directories for raw and processed data, enabling efficient data management at scale.

For **strategy development**, a plugin architecture with consistent interfaces across languages proves most effective. Abstract base classes define the strategy contract with `initialize()`, `on_tick()`, and `cleanup()` methods. Python implementations use Numba's `@njit` decorator for 10-100x performance gains, while production strategies leverage Rust for maximum speed. A factory pattern manages strategy instantiation, allowing runtime selection between implementations based on performance requirements.

The **parameter optimization harness** supports multiple optimization algorithms through a unified interface. Grid search handles exhaustive parameter exploration, while SAMBO (Sequential Approximate Multi-objective Bayesian Optimization) and genetic algorithms enable efficient exploration of large parameter spaces. A particularly powerful technique is Combinatorial Cross-Validation (CCV), which generates multiple train-test splits to identify robust parameters that generalize across market regimes.

**Configuration management** follows a hierarchical pattern where default settings cascade through environment-specific, strategy-specific, and user-specific configurations. YAML files define parameter spaces, optimization methods, and deployment targets, enabling teams to maintain consistent configurations across development and production environments.

## Real-world implementations and performance insights

Production deployments of hftbacktest demonstrate impressive scalability and performance. The **Hard Sums Technologies case study** achieved 40x acceleration in backtesting deep learning HFT models, processing 920+ million ticks across 1000+ trading days. Their optimized implementation completed 15 months of backtesting in just 12 days, achieving a processing rate of 82.3 simulated days per wall-clock day on a single Nvidia 1080Ti GPU.

**Common implementation patterns** from successful deployments reveal several best practices. Market-making strategies typically structure their main loop around 10-millisecond intervals using `hbt.elapse(10_000_000)`, clearing inactive orders and recalculating prices based on alpha forecasts and risk metrics. Asset configurations carefully model exchange-specific characteristics including latency (typically 10ms round-trip), queue position models, and fee structures with maker rebates.

**Performance optimization** requires attention to several critical areas. Always use Numba JIT compilation for Python strategies - this alone provides order-of-magnitude speedups. For large datasets, preloading into memory proves more efficient than lazy loading for repeated backtests. Choose queue position models that match exchange behavior: power law models for aggressive taking, risk-averse models for conservative execution.

**Common pitfalls** include reusing HftBacktest instances (always create new instances), floating-point precision errors with 32-bit floats (use proper rounding based on tick size), and memory management issues with multi-day datasets (implement lazy loading for datasets exceeding available RAM). The framework's Python and Rust versions use different data formats, requiring careful migration when transitioning to production.

**Directory organization** in production systems typically separates strategies by type (market_making, grid_trading, statistical_arbitrage), maintains distinct paths for raw and processed data, centralizes configuration in YAML files, and organizes results by backtest runs. This structure supports both rapid development iteration and production deployment requirements.

The ecosystem includes several mature implementations worth studying. The primary nkaz001/hftbacktest repository (2.7k+ stars) provides comprehensive examples and supports live trading on Binance Futures and Bybit. Alternative implementations like evgerher/hft-backtesting integrate with ClickHouse for large-scale data storage, while DJ824/hft-backtester demonstrates advanced orderbook implementations with O(1) order access and concurrent multi-instrument backtesting.

## Conclusion

hftbacktest provides a robust foundation for building high-performance backtesting systems, with proven scalability to billions of market events and nanosecond precision. Success requires careful attention to data format requirements, thoughtful architecture design supporting progressive optimization, and implementation patterns that balance development velocity with production performance. The framework's maturity is evident in its adoption across academic research, cryptocurrency trading, and institutional applications, with well-documented patterns for addressing common challenges in HFT system development.