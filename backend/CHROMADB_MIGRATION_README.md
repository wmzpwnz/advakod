# ChromaDB Schema Migration

## Overview

This document describes the ChromaDB schema migration implemented to fix compatibility issues between the installed ChromaDB version and the database schema.

## Problem

The system was experiencing a "no such column: collections.topic" error due to a version mismatch:
- **Requirements.txt specified**: ChromaDB 0.4.18
- **Actually installed**: ChromaDB 1.2.2
- **Database schema**: Created with older version, missing required columns

## Solution

### 1. Migration Script

Created `scripts/chromadb_migration.py` that:
- Detects version mismatches
- Backs up the existing database
- Adds missing columns (`topic` in collections table, `topic` and `metadata` in segments table)
- Verifies the migration was successful

### 2. Automatic Migration

Updated `vector_store_service.py` to:
- Check schema compatibility on initialization
- Automatically run migration if needed
- Provide better error messages and logging

### 3. Fixed Database Path

Corrected the database path configuration from:
```python
os.path.join(os.getcwd(), "backend", "data", "chroma_db")
```
to:
```python
os.path.join(os.getcwd(), "data", "chroma_db")
```

## Usage

### Manual Migration
```bash
# Run migration with backup (recommended)
python scripts/chromadb_migration.py

# Force migration without prompts
python scripts/chromadb_migration.py --force

# Skip backup creation
python scripts/chromadb_migration.py --no-backup

# Rollback to backup
python scripts/chromadb_migration.py --rollback
```

### Automatic Migration

The vector store service now automatically detects and fixes schema issues on initialization.

## Files Modified

1. **`scripts/chromadb_migration.py`** - New migration script
2. **`app/services/vector_store_service.py`** - Added automatic migration and schema checks
3. **`test_chromadb_migration.py`** - Test script for migration functionality

## Schema Changes

### Collections Table
- **Added**: `topic` column (TEXT)

### Segments Table  
- **Added**: `topic` column (TEXT)
- **Added**: `metadata` column (TEXT)

## Verification

After migration, the following should work without errors:
```python
from app.services.vector_store_service import vector_store_service
vector_store_service.initialize()
assert vector_store_service.is_ready()
```

## Backup

The migration script automatically creates backups with timestamps:
```
data/chroma_db/chroma_backup_YYYYMMDD_HHMMSS.sqlite3
```

## Troubleshooting

### If migration fails:
1. Check the logs for specific error messages
2. Ensure proper file permissions on the database directory
3. Try running with `--force` flag
4. If needed, restore from backup using `--rollback`

### If ChromaDB still fails to initialize:
1. Check ChromaDB version: `python -c "import chromadb; print(chromadb.__version__)"`
2. Verify database schema: `sqlite3 data/chroma_db/chroma.sqlite3 "PRAGMA table_info(collections);"`
3. Check file permissions and disk space

## Requirements Compatibility

The migration handles the version mismatch between:
- ChromaDB 0.4.18 (requirements.txt)
- ChromaDB 1.2.2 (actually installed)

Consider updating requirements.txt to match the installed version or vice versa for consistency.