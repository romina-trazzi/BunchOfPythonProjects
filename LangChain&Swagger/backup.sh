#!/bin/bash

# Backup script for LangChain RAG Engine
# Usage: ./backup.sh [backup_type]
# Backup types: full, data, logs, config (default: full)

set -e

BACKUP_TYPE=${1:-full}
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
PROJECT_NAME="langchain-rag"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

print_status "Starting $BACKUP_TYPE backup at $DATE..."

case $BACKUP_TYPE in
    "full")
        print_status "Creating full backup..."
        
        # Backup vector database
        if [ -d "data" ]; then
            print_status "Backing up vector database..."
            tar -czf "$BACKUP_DIR/chroma_backup_$DATE.tar.gz" data/
        fi
        
        # Backup logs
        if [ -d "logs" ]; then
            print_status "Backing up logs..."
            tar -czf "$BACKUP_DIR/logs_backup_$DATE.tar.gz" logs/
        fi
        
        # Backup configuration
        print_status "Backing up configuration..."
        tar -czf "$BACKUP_DIR/config_backup_$DATE.tar.gz" \
            .env* \
            docker-compose.yml \
            Dockerfile \
            nginx.conf \
            requirements.txt \
            2>/dev/null || true
        
        # Backup source code
        print_status "Backing up source code..."
        tar -czf "$BACKUP_DIR/src_backup_$DATE.tar.gz" src/ examples/ docs/ README.md
        
        print_status "Full backup completed ✅"
        ;;
        
    "data")
        print_status "Creating data backup..."
        if [ -d "data" ]; then
            tar -czf "$BACKUP_DIR/chroma_backup_$DATE.tar.gz" data/
            print_status "Data backup completed ✅"
        else
            print_warning "No data directory found"
        fi
        ;;
        
    "logs")
        print_status "Creating logs backup..."
        if [ -d "logs" ]; then
            tar -czf "$BACKUP_DIR/logs_backup_$DATE.tar.gz" logs/
            print_status "Logs backup completed ✅"
        else
            print_warning "No logs directory found"
        fi
        ;;
        
    "config")
        print_status "Creating configuration backup..."
        tar -czf "$BACKUP_DIR/config_backup_$DATE.tar.gz" \
            .env* \
            docker-compose.yml \
            Dockerfile \
            nginx.conf \
            requirements.txt \
            2>/dev/null || true
        print_status "Configuration backup completed ✅"
        ;;
        
    *)
        print_error "Invalid backup type: $BACKUP_TYPE"
        print_error "Valid types: full, data, logs, config"
        exit 1
        ;;
esac

# Show backup size and location
print_status "Backup files created:"
ls -lh "$BACKUP_DIR"/*_$DATE.tar.gz 2>/dev/null || true

# Cleanup old backups (keep last 7 days)
print_status "Cleaning up old backups (keeping last 7 days)..."
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete 2>/dev/null || true

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
print_status "Total backup directory size: $TOTAL_SIZE"

print_status "Backup process completed! 🎉"

# Optional: Upload to cloud storage
if [ ! -z "$BACKUP_S3_BUCKET" ]; then
    print_status "Uploading to S3 bucket: $BACKUP_S3_BUCKET"
    aws s3 cp "$BACKUP_DIR"/*_$DATE.tar.gz "s3://$BACKUP_S3_BUCKET/langchain-rag/" || print_warning "S3 upload failed"
fi

if [ ! -z "$BACKUP_GCS_BUCKET" ]; then
    print_status "Uploading to GCS bucket: $BACKUP_GCS_BUCKET"
    gsutil cp "$BACKUP_DIR"/*_$DATE.tar.gz "gs://$BACKUP_GCS_BUCKET/langchain-rag/" || print_warning "GCS upload failed"
fi