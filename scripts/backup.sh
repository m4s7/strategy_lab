#!/bin/bash
set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="/backup/strategy-lab"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PREFIX="backup_${DATE}"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Load environment variables
if [ -f "$PROJECT_ROOT/.env.prod" ]; then
    export $(cat "$PROJECT_ROOT/.env.prod" | grep -v '^#' | xargs)
fi

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

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Start backup process
log "Starting backup process..."

# 1. Backup database
log "Backing up PostgreSQL database..."
if docker exec strategy-lab-postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/db_${BACKUP_PREFIX}.sql.gz"; then
    log "Database backup completed successfully"
else
    error "Database backup failed"
    exit 1
fi

# 2. Backup Redis data
log "Backing up Redis data..."
if docker exec strategy-lab-redis redis-cli -a "$REDIS_PASSWORD" BGSAVE && \
   sleep 5 && \
   docker cp strategy-lab-redis:/data/dump.rdb "$BACKUP_DIR/redis_${BACKUP_PREFIX}.rdb"; then
    log "Redis backup completed successfully"
else
    warning "Redis backup failed - continuing with other backups"
fi

# 3. Backup application data
log "Backing up application data..."
if [ -d "$PROJECT_ROOT/data" ]; then
    tar -czf "$BACKUP_DIR/app_data_${BACKUP_PREFIX}.tar.gz" -C "$PROJECT_ROOT" data/
    log "Application data backup completed"
else
    warning "No application data directory found"
fi

# 4. Backup configuration files
log "Backing up configuration files..."
tar -czf "$BACKUP_DIR/config_${BACKUP_PREFIX}.tar.gz" \
    -C "$PROJECT_ROOT" \
    --exclude='.env*' \
    docker-compose.prod.yml \
    nginx/ \
    monitoring/ \
    scripts/ \
    2>/dev/null || true
log "Configuration backup completed"

# 5. Backup docker volumes
log "Backing up Docker volumes..."
for volume in $(docker volume ls -q | grep strategy-lab); do
    docker run --rm \
        -v "$volume:/source:ro" \
        -v "$BACKUP_DIR:/backup" \
        alpine \
        tar -czf "/backup/volume_${volume}_${BACKUP_PREFIX}.tar.gz" -C / source/
done
log "Docker volumes backup completed"

# 6. Create backup manifest
log "Creating backup manifest..."
cat > "$BACKUP_DIR/manifest_${BACKUP_PREFIX}.json" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "version": "1.0",
  "files": [
    "db_${BACKUP_PREFIX}.sql.gz",
    "redis_${BACKUP_PREFIX}.rdb",
    "app_data_${BACKUP_PREFIX}.tar.gz",
    "config_${BACKUP_PREFIX}.tar.gz"
  ],
  "environment": {
    "domain": "${DOMAIN}",
    "environment": "${ENVIRONMENT}"
  }
}
EOF

# 7. Upload to cloud storage (DigitalOcean Spaces)
if command -v s3cmd &> /dev/null; then
    log "Uploading backups to cloud storage..."

    # Configure s3cmd if not already configured
    if [ ! -f "$HOME/.s3cfg" ]; then
        warning "s3cmd not configured. Skipping cloud upload."
    else
        # Upload all backup files
        for file in "$BACKUP_DIR"/*_${BACKUP_PREFIX}*; do
            if s3cmd put "$file" "s3://strategy-lab-${ENVIRONMENT}-backups/$(basename "$file")"; then
                log "Uploaded $(basename "$file") to cloud storage"
            else
                error "Failed to upload $(basename "$file")"
            fi
        done

        # Sync to ensure consistency
        s3cmd sync "$BACKUP_DIR/" "s3://strategy-lab-${ENVIRONMENT}-backups/" \
            --exclude "*" --include "*_${BACKUP_PREFIX}*"
    fi
else
    warning "s3cmd not installed. Skipping cloud upload."
fi

# 8. Clean up old local backups
log "Cleaning up old backups..."
find "$BACKUP_DIR" -type f -name "*.gz" -o -name "*.tar.gz" -o -name "*.rdb" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -type f -name "manifest_*.json" -mtime +$RETENTION_DAYS -delete

# 9. Verify backup integrity
log "Verifying backup integrity..."
ERRORS=0

# Check database backup
if ! gzip -t "$BACKUP_DIR/db_${BACKUP_PREFIX}.sql.gz" 2>/dev/null; then
    error "Database backup file is corrupted"
    ((ERRORS++))
fi

# Check tar archives
for archive in "$BACKUP_DIR"/*_${BACKUP_PREFIX}.tar.gz; do
    if [ -f "$archive" ] && ! tar -tzf "$archive" >/dev/null 2>&1; then
        error "Archive $(basename "$archive") is corrupted"
        ((ERRORS++))
    fi
done

# 10. Send notification
if [ $ERRORS -eq 0 ]; then
    log "Backup completed successfully!"

    # Send success notification (implement your notification method)
    # curl -X POST "$SLACK_WEBHOOK" -d "{\"text\": \"Backup completed successfully for ${ENVIRONMENT}\"}"
else
    error "Backup completed with $ERRORS errors"
    exit 1
fi

# Calculate backup size
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log "Total backup size: $BACKUP_SIZE"

# Log backup completion
echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") - Backup completed successfully. Size: $BACKUP_SIZE" >> "$BACKUP_DIR/backup.log"
