#!/bin/bash

# Database Setup Script for Strategy Lab with TimescaleDB
# This script creates the database, user, and runs migrations

set -e

echo "=== Strategy Lab Database Setup ==="
echo ""

# Database configuration
DB_NAME="strategy_lab"
DB_USER="strategy_user"
DB_PASS="strategy_pass"

# Check if PostgreSQL is running
if ! systemctl is-active --quiet postgresql; then
    echo "PostgreSQL is not running. Starting it..."
    sudo systemctl start postgresql
fi

echo "Creating database and user..."

# Create database and user using postgres superuser
sudo -u postgres psql <<EOF
-- Create user if not exists
DO
\$\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_user
      WHERE usename = '$DB_USER') THEN
      CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';
   END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\\gexec

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

echo "Enabling TimescaleDB extension..."

# Enable TimescaleDB extension
sudo -u postgres psql -d $DB_NAME <<EOF
CREATE EXTENSION IF NOT EXISTS timescaledb;
EOF

echo "Database setup complete!"
echo ""
echo "Connection string: postgresql://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME"
echo ""
echo "Next: Run migrations with: bash scripts/run_migrations.sh"