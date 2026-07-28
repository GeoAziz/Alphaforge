#!/bin/bash
# ==========================================================================
# AlphaForge Disaster Recovery - Database Backup Script
# Run daily at 2 AM UTC via cron
# ==========================================================================

set -euo pipefail

# Configuration
BACKUP_DIR="/backups/postgresql"
S3_BUCKET="${S3_BACKUP_BUCKET:-alphaforge-backups}"
RETENTION_DAYS=30
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="${BACKUP_DIR}/alphaforge_${DATE}.sql.gz"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARN:${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
    exit 1
}

# ==========================================================================
# Pre-flight checks
# ==========================================================================

log "🚀 Starting AlphaForge database backup"

if ! command -v pg_dump &> /dev/null; then
    error "pg_dump not found. Install PostgreSQL client tools."
fi

if ! command -v aws &> /dev/null; then
    warn "AWS CLI not found. Will skip S3 upload."
    SKIP_S3=true
else
    SKIP_S3=false
fi

# ==========================================================================
# Create backup
# ==========================================================================

mkdir -p "${BACKUP_DIR}"

log "📦 Creating database backup..."

pg_dump "${DATABASE_URL}" \
    --format=custom \
    --compress=9 \
    --verbose \
    --no-owner \
    --no-privileges \
    2>/dev/null | gzip > "${BACKUP_FILE}"

BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
log "✅ Backup created: ${BACKUP_FILE} (${BACKUP_SIZE})"

# ==========================================================================
# Verify backup integrity
# ==========================================================================

log "🔍 Verifying backup integrity..."

if [ -f "${BACKUP_FILE}" ] && [ -s "${BACKUP_FILE}" ]; then
    log "✅ Backup file exists and is not empty"
else
    error "Backup verification failed: file is missing or empty"
fi

# Quick gzip integrity check
if ! gzip -t "${BACKUP_FILE}" 2>/dev/null; then
    error "Backup file is corrupted (gzip test failed)"
fi
log "✅ Gzip integrity verified"

# ==========================================================================
# Upload to S3
# ==========================================================================

if [ "${SKIP_S3}" = false ]; then
    log "☁️  Uploading to S3: s3://${S3_BUCKET}/postgresql/${DATE}.sql.gz"
    
    aws s3 cp "${BACKUP_FILE}" \
        "s3://${S3_BUCKET}/postgresql/${DATE}.sql.gz" \
        --storage-class STANDARD_IA \
        --sse AES256 \
        --only-show-errors
    
    log "✅ Upload complete"
fi

# ==========================================================================
# Cleanup old backups
# ==========================================================================

log "🧹 Cleaning up local backups older than ${RETENTION_DAYS} days..."

find "${BACKUP_DIR}" -name "alphaforge_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
DELETED_COUNT=$(find "${BACKUP_DIR}" -name "alphaforge_*.sql.gz" -type f -mtime +${RETENTION_DAYS} | wc -l)
log "✅ Cleaned up ${DELETED_COUNT} old backups"

# ==========================================================================
# Summary
# ==========================================================================

TOTAL_BACKUPS=$(find "${BACKUP_DIR}" -name "alphaforge_*.sql.gz" -type f | wc -l)
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" 2>/dev/null | cut -f1)

log ""
log "📊 Backup Summary:"
log "   File: ${BACKUP_FILE}"
log "   Size: ${BACKUP_SIZE}"
log "   Total local backups: ${TOTAL_BACKUPS}"
log "   Total local size: ${TOTAL_SIZE}"
log "   S3 upload: $(if [ "${SKIP_S3}" = false ]; then echo 'Yes'; else echo 'Skipped'; fi)"
log ""
log "✅ Backup completed successfully"
