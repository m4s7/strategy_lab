#!/bin/bash

# TimescaleDB Installation Script for Ubuntu
# This script installs PostgreSQL with TimescaleDB extension

set -e

echo "=== TimescaleDB Installation Script ==="
echo "This script will install PostgreSQL with TimescaleDB extension"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "Please run with sudo: sudo bash install_timescaledb.sh"
    exit 1
fi

# Update system packages
echo "Updating system packages..."
apt-get update

# Install PostgreSQL if not already installed
echo "Installing PostgreSQL..."
apt-get install -y postgresql postgresql-contrib postgresql-client

# Get PostgreSQL version
PG_VERSION=$(psql --version | awk '{print $3}' | sed 's/\..*//')
echo "PostgreSQL version: $PG_VERSION"

# Add TimescaleDB repository
echo "Adding TimescaleDB repository..."
apt-get install -y gnupg lsb-release wget

# Add PostgreSQL apt repository
sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

# Add TimescaleDB repository
sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add -

# Update package list
apt-get update

# Install TimescaleDB
echo "Installing TimescaleDB for PostgreSQL $PG_VERSION..."
apt-get install -y timescaledb-2-postgresql-$PG_VERSION

# Run TimescaleDB tuning script
echo "Running TimescaleDB tuning script..."
timescaledb-tune --quiet --yes

# Restart PostgreSQL
echo "Restarting PostgreSQL..."
systemctl restart postgresql

# Enable PostgreSQL on boot
systemctl enable postgresql

echo ""
echo "=== Installation Complete ==="
echo "PostgreSQL with TimescaleDB has been installed successfully!"
echo ""
echo "Next steps:"
echo "1. Run: sudo bash scripts/setup_database.sh"
echo "2. This will create the strategy_lab database with TimescaleDB enabled"
echo ""