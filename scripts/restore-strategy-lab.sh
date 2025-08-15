#!/bin/bash

# Strategy Lab Restore Script
# Restores data from backups with point-in-time recovery capability

set -euo pipefail

# Configuration
BACKUP_ROOT="/var/backups/strategy_lab"
DATA_DIR="/app/data"
CONFIG_DIR="/app/config"
LOG_DIR="/app/logs"
DB_PATH="/app/data/strategy_lab.db"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
RESTORE_DIR="/tmp/strategy_lab_restore"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Display usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -t, --type TYPE         Recovery type: latest, specific, point-in-time
    -b, --backup-id ID      Specific backup ID to restore
    -d, --date DATE         Point-in-time date (YYYY-MM-DD HH:MM:SS)
    -c, --components COMP   Components to restore (comma-separated)
                           Options: database,redis,configs,strategies,logs,all
    -m, --mode MODE        Recovery mode: full or selective (default: selective)
    -p, --preview          Preview changes without applying
    -f, --force            Force restore without confirmation
    -h, --help             Display this help message

Examples:
    $0 --type latest --components all
    $0 --type specific --backup-id full_20240114_020000 --components database,configs
    $0 --type point-in-time --date "2024-01-14 12:00:00" --mode selective
EOF
}

# Parse command line arguments
parse_args() {
    RECOVERY_TYPE="latest"
    BACKUP_ID=""
    RECOVERY_DATE=""
    COMPONENTS="database,configs,strategies"
    RECOVERY_MODE="selective"
    PREVIEW_ONLY=false
    FORCE_RESTORE=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--type)
                RECOVERY_TYPE="$2"
                shift 2
                ;;
            -b|--backup-id)
                BACKUP_ID="$2"
                shift 2
                ;;
            -d|--date)
                RECOVERY_DATE="$2"
                shift 2
                ;;
            -c|--components)
                COMPONENTS="$2"
                shift 2
                ;;
            -m|--mode)
                RECOVERY_MODE="$2"
                shift 2
                ;;
            -p|--preview)
                PREVIEW_ONLY=true
                shift
                ;;
            -f|--force)
                FORCE_RESTORE=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Find latest backup
find_latest_backup() {
    local latest=$(ls -t "$BACKUP_ROOT/daily/"*.tar.gz 2>/dev/null | head -1)

    if [ -z "$latest" ]; then
        error "No backups found"
        exit 1
    fi

    echo "$latest"
}

# Find backup by ID
find_backup_by_id() {
    local id=$1
    local backup=""

    # Search in all backup directories
    for dir in daily weekly monthly; do
        backup=$(find "$BACKUP_ROOT/$dir" -name "*${id}*.tar.gz" 2>/dev/null | head -1)
        if [ -n "$backup" ]; then
            break
        fi
    done

    if [ -z "$backup" ]; then
        error "Backup with ID '$id' not found"
        exit 1
    fi

    echo "$backup"
}

# Find point-in-time backup
find_point_in_time_backup() {
    local target_date=$1
    local target_timestamp=$(date -d "$target_date" +%s)
    local closest_backup=""
    local smallest_diff=999999999

    # Search all backups
    for backup in $(find "$BACKUP_ROOT" -name "*.tar.gz" | sort); do
        # Extract timestamp from filename
        local backup_timestamp=$(echo "$backup" | grep -oP '\d{8}_\d{6}' | head -1)
        if [ -n "$backup_timestamp" ]; then
            local backup_date=$(date -d "${backup_timestamp:0:8} ${backup_timestamp:9:2}:${backup_timestamp:11:2}:${backup_timestamp:13:2}" +%s)
            local diff=$((target_timestamp - backup_date))

            # Find closest backup before target date
            if [ $diff -ge 0 ] && [ $diff -lt $smallest_diff ]; then
                smallest_diff=$diff
                closest_backup=$backup
            fi
        fi
    done

    if [ -z "$closest_backup" ]; then
        error "No suitable backup found for date: $target_date"
        exit 1
    fi

    echo "$closest_backup"
}

# Extract backup
extract_backup() {
    local backup_file=$1

    log "Extracting backup: $(basename $backup_file)"

    # Create restore directory
    rm -rf "$RESTORE_DIR"
    mkdir -p "$RESTORE_DIR"

    # Extract backup
    tar -xzf "$backup_file" -C "$RESTORE_DIR"

    # Verify extraction
    if [ ! -f "$RESTORE_DIR/manifest.json" ]; then
        error "Invalid backup format: manifest.json not found"
        exit 1
    fi

    log "Backup extracted successfully"
}

# Preview restore
preview_restore() {
    info "=== RESTORE PREVIEW ==="
    info "Backup: $(basename $1)"
    info "Type: $RECOVERY_TYPE"
    info "Mode: $RECOVERY_MODE"
    info "Components: $COMPONENTS"

    if [ -f "$RESTORE_DIR/manifest.json" ]; then
        info "Backup details:"
        jq . "$RESTORE_DIR/manifest.json" | while IFS= read -r line; do
            info "  $line"
        done
    fi

    info "=== CHANGES TO BE APPLIED ==="

    # Check each component
    IFS=',' read -ra COMP_ARRAY <<< "$COMPONENTS"
    for comp in "${COMP_ARRAY[@]}"; do
        case $comp in
            database)
                if [ -f "$RESTORE_DIR"/database_*.db ]; then
                    local backup_size=$(du -h "$RESTORE_DIR"/database_*.db | cut -f1)
                    local current_size=$(du -h "$DB_PATH" 2>/dev/null | cut -f1 || echo "N/A")
                    info "Database: Current size: $current_size → Backup size: $backup_size"
                fi
                ;;
            configs)
                if [ -d "$RESTORE_DIR"/configs_* ]; then
                    local file_count=$(find "$RESTORE_DIR"/configs_* -type f | wc -l)
                    info "Configurations: $file_count files will be restored"
                fi
                ;;
            strategies)
                if [ -f "$RESTORE_DIR"/strategies_*.json ]; then
                    local strategy_count=$(jq '. | length' "$RESTORE_DIR"/strategies_*.json 2>/dev/null || echo "0")
                    info "Strategies: $strategy_count strategies will be restored"
                fi
                ;;
        esac
    done
}

# Stop services
stop_services() {
    log "Stopping services..."

    # Stop application services
    systemctl stop strategy-lab-frontend strategy-lab-backend 2>/dev/null || true

    # Wait for services to stop
    sleep 2

    log "Services stopped"
}

# Start services
start_services() {
    log "Starting services..."

    # Start application services
    systemctl start strategy-lab-backend strategy-lab-frontend 2>/dev/null || true

    # Wait for services to start
    sleep 5

    # Verify services are running
    if systemctl is-active --quiet strategy-lab-backend; then
        log "Services started successfully"
    else
        warning "Some services may not have started properly"
    fi
}

# Restore database
restore_database() {
    local backup_db=$(find "$RESTORE_DIR" -name "database_*.db" | head -1)

    if [ -z "$backup_db" ]; then
        warning "No database backup found in archive"
        return
    fi

    log "Restoring database..."

    # Verify backup integrity
    if ! sqlite3 "$backup_db" "PRAGMA integrity_check;" | grep -q "ok"; then
        error "Database backup integrity check failed"
        exit 1
    fi

    # Create backup of current database
    if [ -f "$DB_PATH" ]; then
        cp "$DB_PATH" "${DB_PATH}.before_restore_$(date +%Y%m%d_%H%M%S)"
    fi

    # Restore database
    if [ "$RECOVERY_MODE" = "full" ]; then
        cp "$backup_db" "$DB_PATH"
    else
        # Selective restore - merge data
        sqlite3 "$DB_PATH" <<EOF
ATTACH DATABASE '$backup_db' AS backup;
BEGIN TRANSACTION;

-- Restore strategies
INSERT OR REPLACE INTO strategies
SELECT * FROM backup.strategies;

-- Restore backtest results
INSERT OR REPLACE INTO backtest_results
SELECT * FROM backup.backtest_results;

-- Restore other tables as needed
COMMIT;
DETACH DATABASE backup;
EOF
    fi

    # Set proper permissions
    chown app:app "$DB_PATH"
    chmod 640 "$DB_PATH"

    log "Database restore completed"
}

# Restore Redis
restore_redis() {
    local backup_rdb=$(find "$RESTORE_DIR" -name "redis_*.rdb" | head -1)

    if [ -z "$backup_rdb" ]; then
        warning "No Redis backup found in archive"
        return
    fi

    log "Restoring Redis data..."

    # Stop Redis
    systemctl stop redis

    # Backup current data
    if [ -f /var/lib/redis/dump.rdb ]; then
        cp /var/lib/redis/dump.rdb /var/lib/redis/dump.rdb.before_restore_$(date +%Y%m%d_%H%M%S)
    fi

    # Restore Redis dump
    cp "$backup_rdb" /var/lib/redis/dump.rdb
    chown redis:redis /var/lib/redis/dump.rdb

    # Start Redis
    systemctl start redis

    log "Redis restore completed"
}

# Restore configurations
restore_configs() {
    local backup_configs=$(find "$RESTORE_DIR" -name "configs_*" -type d | head -1)

    if [ -z "$backup_configs" ]; then
        warning "No configuration backup found in archive"
        return
    fi

    log "Restoring configurations..."

    # Backup current configs
    if [ -d "$CONFIG_DIR" ]; then
        tar -czf "$CONFIG_DIR/../configs_before_restore_$(date +%Y%m%d_%H%M%S).tar.gz" -C "$CONFIG_DIR" .
    fi

    # Restore configs
    if [ "$RECOVERY_MODE" = "full" ]; then
        rm -rf "$CONFIG_DIR"/*
        cp -r "$backup_configs"/* "$CONFIG_DIR/"
    else
        # Selective restore - only overwrite existing files
        cp -r "$backup_configs"/* "$CONFIG_DIR/"
    fi

    # Set proper permissions
    chown -R app:app "$CONFIG_DIR"

    log "Configuration restore completed"
}

# Main restore function
perform_restore() {
    local backup_file=$1

    # Extract backup
    extract_backup "$backup_file"

    # Preview if requested
    if [ "$PREVIEW_ONLY" = true ]; then
        preview_restore "$backup_file"
        rm -rf "$RESTORE_DIR"
        exit 0
    fi

    # Confirm restore
    if [ "$FORCE_RESTORE" = false ]; then
        preview_restore "$backup_file"
        echo
        read -p "Do you want to proceed with the restore? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Restore cancelled"
            rm -rf "$RESTORE_DIR"
            exit 0
        fi
    fi

    # Stop services
    stop_services

    # Restore components
    IFS=',' read -ra COMP_ARRAY <<< "$COMPONENTS"
    for comp in "${COMP_ARRAY[@]}"; do
        case $comp in
            database)
                restore_database
                ;;
            redis)
                restore_redis
                ;;
            configs)
                restore_configs
                ;;
            strategies)
                # Strategies are restored with database
                ;;
            logs)
                warning "Log restoration not implemented"
                ;;
            all)
                restore_database
                restore_redis
                restore_configs
                ;;
            *)
                warning "Unknown component: $comp"
                ;;
        esac
    done

    # Start services
    start_services

    # Cleanup
    rm -rf "$RESTORE_DIR"

    log "Restore completed successfully"
}

# Main execution
main() {
    parse_args "$@"

    log "Starting Strategy Lab restore process..."

    # Find backup file based on recovery type
    case "$RECOVERY_TYPE" in
        latest)
            BACKUP_FILE=$(find_latest_backup)
            ;;
        specific)
            if [ -z "$BACKUP_ID" ]; then
                error "Backup ID required for specific recovery"
                exit 1
            fi
            BACKUP_FILE=$(find_backup_by_id "$BACKUP_ID")
            ;;
        point-in-time)
            if [ -z "$RECOVERY_DATE" ]; then
                error "Date required for point-in-time recovery"
                exit 1
            fi
            BACKUP_FILE=$(find_point_in_time_backup "$RECOVERY_DATE")
            ;;
        *)
            error "Invalid recovery type: $RECOVERY_TYPE"
            exit 1
            ;;
    esac

    # Perform restore
    perform_restore "$BACKUP_FILE"
}

# Error handling
trap 'error "Restore failed on line $LINENO"; exit 1' ERR

# Run main function
main "$@"
