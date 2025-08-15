#!/bin/bash
set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="/backup/strategy-lab"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check if backup date is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_date> [--from-cloud]"
    echo "Example: $0 20240115_120000"
    echo "Example: $0 20240115_120000 --from-cloud"
    echo ""
    echo "Available local backups:"
    ls -1 "$BACKUP_DIR"/manifest_*.json 2>/dev/null | sed 's/.*manifest_\(.*\)\.json/  \1/' || echo "  No local backups found"
    exit 1
fi

BACKUP_DATE=$1
FROM_CLOUD=${2:-""}

# Load environment variables
if [ -f "$PROJECT_ROOT/.env.prod" ]; then
    export $(cat "$PROJECT_ROOT/.env.prod" | grep -v '^#' | xargs)
fi

log "Starting restore process for backup: $BACKUP_DATE"

# Download from cloud if requested
if [ "$FROM_CLOUD" == "--from-cloud" ]; then
    if command -v s3cmd &> /dev/null; then
        log "Downloading backup from cloud storage..."

        # Create temp directory for download
        TEMP_DIR="/tmp/restore_${BACKUP_DATE}"
        mkdir -p "$TEMP_DIR"

        # Download backup files
        s3cmd get "s3://strategy-lab-${ENVIRONMENT}-backups/*_${BACKUP_DATE}*" "$TEMP_DIR/" || {
            error "Failed to download backup from cloud"
            exit 1
        }

        # Move to backup directory
        mv "$TEMP_DIR"/* "$BACKUP_DIR/"
        rmdir "$TEMP_DIR"
    else
        error "s3cmd not installed. Cannot download from cloud."
        exit 1
    fi
fi

# Verify backup files exist
MANIFEST_FILE="$BACKUP_DIR/manifest_${BACKUP_DATE}.json"
if [ ! -f "$MANIFEST_FILE" ]; then
    error "Backup manifest not found: $MANIFEST_FILE"
    exit 1
fi

# Read manifest
log "Reading backup manifest..."
if command -v jq &> /dev/null; then
    BACKUP_FILES=$(jq -r '.files[]' "$MANIFEST_FILE")
else
    # Fallback if jq is not installed
    BACKUP_FILES=$(grep -o '"[^"]*"' "$MANIFEST_FILE" | grep -E "(db_|redis_|app_data_|config_)" | tr -d '"')
fi

# Verify all backup files exist
for file in $BACKUP_FILES; do
    if [ ! -f "$BACKUP_DIR/$file" ]; then
        error "Backup file missing: $file"
        exit 1
    fi
done

# Confirmation prompt
echo ""
warning "This will restore the following:"
echo "  - Database: db_${BACKUP_DATE}.sql.gz"
echo "  - Redis: redis_${BACKUP_DATE}.rdb"
echo "  - Application data: app_data_${BACKUP_DATE}.tar.gz"
echo "  - Configuration: config_${BACKUP_DATE}.tar.gz"
echo ""
read -p "Are you sure you want to continue? This will OVERWRITE current data! (yes/no): " -n 3 -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log "Restore cancelled by user"
    exit 0
fi

# Stop services
log "Stopping services..."
cd "$PROJECT_ROOT"
docker-compose -f docker-compose.prod.yml stop backend frontend

# 1. Restore database
log "Restoring PostgreSQL database..."

# Create new database for restore
docker exec strategy-lab-postgres psql -U "$DB_USER" -c "CREATE DATABASE ${DB_NAME}_restore;" || true

# Restore to new database
gunzip -c "$BACKUP_DIR/db_${BACKUP_DATE}.sql.gz" | \
    docker exec -i strategy-lab-postgres psql -U "$DB_USER" "${DB_NAME}_restore"

# If restore successful, swap databases
if [ $? -eq 0 ]; then
    log "Database restore successful, swapping databases..."

    # Disconnect all connections
    docker exec strategy-lab-postgres psql -U "$DB_USER" -c \
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();"

    # Rename databases
    docker exec strategy-lab-postgres psql -U "$DB_USER" -c "ALTER DATABASE ${DB_NAME} RENAME TO ${DB_NAME}_old;"
    docker exec strategy-lab-postgres psql -U "$DB_USER" -c "ALTER DATABASE ${DB_NAME}_restore RENAME TO ${DB_NAME};"

    # Drop old database
    docker exec strategy-lab-postgres psql -U "$DB_USER" -c "DROP DATABASE ${DB_NAME}_old;"

    log "Database restored successfully"
else
    error "Database restore failed"
    docker exec strategy-lab-postgres psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS ${DB_NAME}_restore;"
    exit 1
fi

# 2. Restore Redis data
log "Restoring Redis data..."
if [ -f "$BACKUP_DIR/redis_${BACKUP_DATE}.rdb" ]; then
    # Stop Redis to replace dump file
    docker-compose -f docker-compose.prod.yml stop redis

    # Copy dump file
    docker cp "$BACKUP_DIR/redis_${BACKUP_DATE}.rdb" strategy-lab-redis:/data/dump.rdb

    # Set correct permissions
    docker-compose -f docker-compose.prod.yml run --rm redis chown redis:redis /data/dump.rdb

    # Start Redis
    docker-compose -f docker-compose.prod.yml start redis

    log "Redis data restored successfully"
else
    warning "Redis backup not found, skipping..."
fi

# 3. Restore application data
log "Restoring application data..."
if [ -f "$BACKUP_DIR/app_data_${BACKUP_DATE}.tar.gz" ]; then
    # Backup current data
    if [ -d "$PROJECT_ROOT/data" ]; then
        mv "$PROJECT_ROOT/data" "$PROJECT_ROOT/data.old"
    fi

    # Extract backup
    tar -xzf "$BACKUP_DIR/app_data_${BACKUP_DATE}.tar.gz" -C "$PROJECT_ROOT"

    # Remove old data if restore successful
    if [ $? -eq 0 ]; then
        rm -rf "$PROJECT_ROOT/data.old"
        log "Application data restored successfully"
    else
        error "Failed to restore application data"
        mv "$PROJECT_ROOT/data.old" "$PROJECT_ROOT/data"
    fi
else
    warning "Application data backup not found, skipping..."
fi

# 4. Restore configuration (optional)
read -p "Do you want to restore configuration files? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log "Restoring configuration files..."

    # Create backup of current config
    tar -czf "$BACKUP_DIR/config_current_$(date +%Y%m%d_%H%M%S).tar.gz" \
        -C "$PROJECT_ROOT" \
        docker-compose.prod.yml \
        nginx/ \
        monitoring/ \
        scripts/ \
        2>/dev/null || true

    # Extract configuration backup
    tar -xzf "$BACKUP_DIR/config_${BACKUP_DATE}.tar.gz" -C "$PROJECT_ROOT"

    log "Configuration restored successfully"
fi

# 5. Run database migrations
log "Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head

# 6. Start services
log "Starting services..."
docker-compose -f docker-compose.prod.yml start backend frontend

# Wait for services to be healthy
log "Waiting for services to be healthy..."
sleep 30

# 7. Verify services
log "Verifying services..."
ERRORS=0

# Check frontend
if ! curl -f -s "http://localhost:3000/api/health" > /dev/null; then
    error "Frontend health check failed"
    ((ERRORS++))
fi

# Check backend
if ! curl -f -s "http://localhost:8000/api/health" > /dev/null; then
    error "Backend health check failed"
    ((ERRORS++))
fi

# Check database
if ! docker exec strategy-lab-postgres pg_isready -U "$DB_USER" -d "$DB_NAME" > /dev/null; then
    error "Database health check failed"
    ((ERRORS++))
fi

if [ $ERRORS -eq 0 ]; then
    log "Restore completed successfully!"
    log "All services are healthy"

    # Log restore completion
    echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") - Restore completed successfully from backup: $BACKUP_DATE" >> "$BACKUP_DIR/restore.log"
else
    error "Restore completed with $ERRORS errors"
    warning "Please check the services and logs for more information"
    exit 1
fi
