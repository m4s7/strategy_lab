# Strategy Lab PRD - Technical Assumptions

## Repository Structure: Monorepo

The Strategy Lab will use a monorepo structure with clear module separation, enabling unified development while maintaining logical component boundaries.

## Service Architecture

**Monolithic application with modular components** - Given the single-user nature and performance requirements, a monolithic architecture with well-defined internal modules provides the best balance of simplicity and performance. The modular design will enable future extraction of components if needed.

## Testing Requirements

**Full Testing Pyramid** - Comprehensive testing including unit tests, integration tests, and end-to-end backtesting validation. Given the financial nature of the application, thorough testing is critical to ensure strategy reliability and system correctness.

## Additional Technical Assumptions and Requests

- **Language:** Python 3.12+ for all components
- **Core Library:** hftbacktest as the primary backtesting engine
- **Package Manager:** uv for dependency management and project setup
- **Data Libraries:** pandas and pyarrow for efficient Parquet file handling
- **Optimization Libraries:** scipy for mathematical optimization, DEAP for genetic algorithms
- **Visualization:** matplotlib for basic plotting and analysis
- **Configuration:** YAML/JSON configuration files for strategy parameters and system settings
- **Development Tools:** black (formatting), ruff (linting), mypy (type checking), pytest (testing)
- **Target Platform:** Ubuntu Server with local development support
- **Data Pipeline:** Parquet → DataFrame → hftbacktest engine processing flow
- **Parallel Processing:** Utilize 16 CPU cores for optimization algorithms and concurrent backtesting