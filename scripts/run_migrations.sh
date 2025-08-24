#!/bin/bash

# Run database migrations for Strategy Lab

set -e

echo "=== Running Database Migrations ==="
echo ""

# Database configuration
DB_NAME="strategy_lab"
DB_USER="strategy_user"
DB_PASS="strategy_pass"
DB_HOST="localhost"
DB_PORT="5432"

MIGRATIONS_DIR="../standalone_api/migrations"

# Change to script directory
cd "$(dirname "$0")"

# Check if migrations directory exists
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "Error: Migrations directory not found at $MIGRATIONS_DIR"
    exit 1
fi

# Run each migration file
for migration in $MIGRATIONS_DIR/*.sql; do
    if [ -f "$migration" ]; then
        echo "Running migration: $(basename $migration)"
        PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f "$migration"
        echo "  ✓ Completed"
        echo ""
    fi
done

echo "=== All Migrations Completed Successfully ==="
echo ""
echo "Database is ready with TimescaleDB optimizations!"
echo "- Hypertables created for time-series data"
echo "- Continuous aggregates configured for metrics"
echo "- Compression policies enabled"
echo "- Retention policies set"
echo ""