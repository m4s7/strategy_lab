#!/bin/bash

# Strategy Lab Backup Script
# Performs automated backups of database, configurations, and application data

set -euo pipefail

# Configuration
BACKUP_ROOT="/var/backups/strategy_lab"
DATA_DIR="/app/data"
CONFIG_DIR="/app/config"
LOG_DIR="/app/logs"
DB_PATH="/app/data/strategy_lab.db"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Backup settings
BACKUP_TYPE="${1:-incremental}" # full or incremental
RETENTION_DAILY=7
RETENTION_WEEKLY=4
RETENTION_MONTHLY=12

# Create timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TODAY=$(date +%Y%m%d)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Create backup directories
create_backup_dirs() {
    mkdir -p "$BACKUP_ROOT"/{daily,weekly,monthly,temp}
    log "Backup directories created/verified"
}

# Check available disk space
check_disk_space() {
    local required_space=$1
    local available_space=$(df "$BACKUP_ROOT" | awk 'NR==2 {print $4}')

    if [ "$available_space" -lt "$required_space" ]; then
        error "Insufficient disk space. Required: ${required_space}KB, Available: ${available_space}KB"
        exit 1
    fi
    log "Disk space check passed"
}

# Backup SQLite database
backup_database() {
    local backup_file="$1/database_${TIMESTAMP}.db"

    log "Starting database backup..."

    # Create database backup with integrity check
    sqlite3 "$DB_PATH" ".backup '$backup_file'"

    # Verify backup
    if sqlite3 "$backup_file" "PRAGMA integrity_check;" | grep -q "ok"; then
        log "Database backup completed and verified"
    else
        error "Database backup verification failed"
        rm -f "$backup_file"
        exit 1
    fi

    # Calculate checksum
    sha256sum "$backup_file" > "${backup_file}.sha256"
}

# Backup Redis data
backup_redis() {
    local backup_file="$1/redis_${TIMESTAMP}.rdb"

    log "Starting Redis backup..."

    # Trigger Redis BGSAVE
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" BGSAVE

    # Wait for backup to complete
    while [ $(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE) -eq $(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" LASTSAVE) ]; do
        sleep 1
    done

    # Copy Redis dump file
    cp /var/lib/redis/dump.rdb "$backup_file"
    log "Redis backup completed"
}

# Backup configuration files
backup_configs() {
    local backup_dir="$1/configs_${TIMESTAMP}"

    log "Starting configuration backup..."

    mkdir -p "$backup_dir"

    # Copy configuration files
    cp -r "$CONFIG_DIR"/* "$backup_dir/" 2>/dev/null || true

    # Remove sensitive data
    find "$backup_dir" -name "*.key" -o -name "*.pem" -o -name "*secret*" | xargs rm -f

    log "Configuration backup completed"
}

# Backup strategy definitions
backup_strategies() {
    local backup_file="$1/strategies_${TIMESTAMP}.json"

    log "Starting strategy backup..."

    # Export strategies from database
    sqlite3 -json "$DB_PATH" "SELECT * FROM strategies;" > "$backup_file"

    log "Strategy backup completed"
}

# Backup logs (compressed)
backup_logs() {
    local backup_file="$1/logs_${TIMESTAMP}.tar.gz"

    log "Starting log backup..."

    # Compress logs older than 1 day
    find "$LOG_DIR" -name "*.log" -mtime +1 | tar -czf "$backup_file" -T -

    log "Log backup completed"
}

# Create incremental backup
create_incremental_backup() {
    local backup_dir="$BACKUP_ROOT/temp/incremental_${TIMESTAMP}"
    local last_backup_marker="$BACKUP_ROOT/.last_backup"

    mkdir -p "$backup_dir"

    log "Creating incremental backup..."

    # Find files modified since last backup
    if [ -f "$last_backup_marker" ]; then
        local last_backup_time=$(cat "$last_backup_marker")
        find "$DATA_DIR" "$CONFIG_DIR" -newer "$last_backup_marker" -type f | \
            tar -czf "$backup_dir/incremental_${TIMESTAMP}.tar.gz" -T -
    else
        warning "No previous backup found, creating full backup instead"
        create_full_backup
        return
    fi

    # Update last backup marker
    echo "$TIMESTAMP" > "$last_backup_marker"

    # Move to daily directory
    mv "$backup_dir" "$BACKUP_ROOT/daily/"

    log "Incremental backup completed"
}

# Create full backup
create_full_backup() {
    local backup_dir="$BACKUP_ROOT/temp/full_${TIMESTAMP}"

    mkdir -p "$backup_dir"

    log "Creating full backup..."

    # Backup all components
    backup_database "$backup_dir"
    backup_redis "$backup_dir"
    backup_configs "$backup_dir"
    backup_strategies "$backup_dir"
    backup_logs "$backup_dir"

    # Create manifest
    cat > "$backup_dir/manifest.json" <<EOF
{
    "timestamp": "$TIMESTAMP",
    "type": "full",
    "components": {
        "database": true,
        "redis": true,
        "configs": true,
        "strategies": true,
        "logs": true
    },
    "size": $(du -sb "$backup_dir" | cut -f1)
}
EOF

    # Compress entire backup
    tar -czf "$BACKUP_ROOT/daily/full_${TIMESTAMP}.tar.gz" -C "$backup_dir" .

    # Clean up temp directory
    rm -rf "$backup_dir"

    # Update last backup marker
    echo "$TIMESTAMP" > "$BACKUP_ROOT/.last_backup"

    log "Full backup completed"
}

# Rotate backups
rotate_backups() {
    log "Starting backup rotation..."

    # Rotate daily backups
    find "$BACKUP_ROOT/daily" -name "*.tar.gz" -mtime +$RETENTION_DAILY -delete

    # Promote weekly backups (Sunday)
    if [ $(date +%u) -eq 7 ]; then
        cp "$BACKUP_ROOT/daily/full_${TODAY}"*.tar.gz "$BACKUP_ROOT/weekly/" 2>/dev/null || true
    fi

    # Rotate weekly backups
    find "$BACKUP_ROOT/weekly" -name "*.tar.gz" -mtime +$((RETENTION_WEEKLY * 7)) -delete

    # Promote monthly backups (1st of month)
    if [ $(date +%d) -eq 01 ]; then
        cp "$BACKUP_ROOT/weekly/"*".tar.gz" "$BACKUP_ROOT/monthly/" 2>/dev/null || true
    fi

    # Rotate monthly backups
    find "$BACKUP_ROOT/monthly" -name "*.tar.gz" -mtime +$((RETENTION_MONTHLY * 30)) -delete

    log "Backup rotation completed"
}

# Send notification
send_notification() {
    local status=$1
    local message=$2

    # Send to monitoring system (example: webhook)
    if [ -n "${BACKUP_WEBHOOK_URL:-}" ]; then
        curl -s -X POST "$BACKUP_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"status\": \"$status\", \"message\": \"$message\", \"timestamp\": \"$TIMESTAMP\"}"
    fi

    # Log to syslog
    logger -t "strategy_lab_backup" "$status: $message"
}

# Main execution
main() {
    log "Starting Strategy Lab backup process..."

    # Create directories
    create_backup_dirs

    # Check disk space (require at least 5GB)
    check_disk_space 5242880

    # Perform backup based on type
    case "$BACKUP_TYPE" in
        full)
            create_full_backup
            ;;
        incremental)
            create_incremental_backup
            ;;
        *)
            error "Invalid backup type: $BACKUP_TYPE"
            exit 1
            ;;
    esac

    # Rotate old backups
    rotate_backups

    # Send success notification
    send_notification "success" "Backup completed successfully"

    log "Backup process completed successfully"
}

# Error handling
trap 'error "Backup failed on line $LINENO"; send_notification "error" "Backup failed: check logs"; exit 1' ERR

# Run main function
main "$@"
