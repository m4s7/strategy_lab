# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Strategy Lab is a financial trading data repository with strategy development framework using the BMad Method (Business Automation and Development). The project contains extensive MNQ (Micro E-mini NASDAQ-100 futures) market data in Parquet format.

## Key Commands

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

### Data Processing
The project uses Parquet files for market data storage. When working with data:
- Data files are located in `data/MNQ/` organized by contract month (e.g., "03-20", "06-24")
- Schema is defined in `data/schema.json`
- File index is maintained in `data/MNQ_parquet_files.json`

## Architecture

### Data Structure
Market data follows this schema:
- **level**: Data level indicator (string)
- **mdt**: Market Data Type - 0=Ask, 1=Bid, 2=Last, 3=ImpliedBid, 4=ImpliedAsk, 5=BookReset
- **timestamp**: Nanosecond precision timestamps
- **price**: Decimal128 with 13 digits, 2 decimal places
- **volume**: Int32 trade/quote volume
- **operation**: Order book operations (0=Add, 1=Update, 2=Remove)
- **depth**: Order book depth level

### BMad Framework Structure
The `.bmad-core/` directory contains:
- `agents/`: AI agent definitions (bmad-master.md defines main commands)
- `tasks/`: Executable workflows
- `templates/`: Document generation templates
- `checklists/`: Quality assurance procedures
- `data/`: Framework knowledge base
- `workflows/`: Development process definitions

### Development Workflow
BMad follows a structured approach:
1. **Planning Phase**: Use analyst and PM agents for requirements
2. **Architecture Phase**: Use architect agent for system design
3. **Implementation Phase**: Use developer agents for coding
4. **Quality Phase**: Execute checklists for validation

## Important Notes

- This is primarily a data repository - no trading strategies are implemented yet
- The BMad framework provides methodology but actual strategy code needs to be developed
- Market data spans May 2019 to March 2025 (current)
- All timestamps are in nanosecond precision for high-frequency analysis
- Data files should not be committed to git (see .gitignore)