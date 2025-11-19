#!/usr/bin/env python3
"""
ChromaDB Schema Migration Script

This script fixes ChromaDB schema compatibility issues by:
1. Detecting version mismatches between installed ChromaDB and database schema
2. Migrating the database schema to match the current ChromaDB version
3. Adding missing columns like 'topic' that are required by newer versions
4. Backing up the original database before migration

Usage:
    python scripts/chromadb_migration.py [--backup] [--force]
"""

import os
import sys
import sqlite3
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add the parent directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import chromadb
    from app.core.config import settings
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this from the backend directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ChromaDBMigrator:
    """Handles ChromaDB schema migration and compatibility fixes"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.sqlite_path = self.db_path / "chroma.sqlite3"
        self.backup_path = None
        
    def check_chromadb_version(self) -> Tuple[str, str]:
        """Check ChromaDB version and requirements compatibility"""
        installed_version = chromadb.__version__
        
        # Read requirements.txt to get expected version
        requirements_path = Path(__file__).parent.parent / "requirements.txt"
        expected_version = "unknown"
        
        try:
            with open(requirements_path, 'r') as f:
                for line in f:
                    if line.strip().startswith('chromadb=='):
                        expected_version = line.strip().split('==')[1]
                        break
        except Exception as e:
            logger.warning(f"Could not read requirements.txt: {e}")
            
        return installed_version, expected_version
    
    def backup_database(self) -> bool:
        """Create a backup of the ChromaDB database"""
        if not self.sqlite_path.exists():
            logger.info("No existing database to backup")
            return True
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_path = self.sqlite_path.parent / f"chroma_backup_{timestamp}.sqlite3"
        
        try:
            shutil.copy2(self.sqlite_path, self.backup_path)
            logger.info(f"✅ Database backed up to: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to backup database: {e}")
            return False
    
    def get_current_schema(self) -> Dict[str, List[Dict]]:
        """Get current database schema information"""
        if not self.sqlite_path.exists():
            return {}
            
        schema = {}
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = []
                    for row in cursor.fetchall():
                        columns.append({
                            'cid': row[0],
                            'name': row[1],
                            'type': row[2],
                            'notnull': row[3],
                            'dflt_value': row[4],
                            'pk': row[5]
                        })
                    schema[table] = columns
                    
        except Exception as e:
            logger.error(f"❌ Failed to get schema: {e}")
            
        return schema
    
    def check_missing_columns(self) -> Dict[str, List[str]]:
        """Check for missing columns that ChromaDB expects"""
        schema = self.get_current_schema()
        missing_columns = {}
        
        # Expected columns for ChromaDB 1.x
        expected_schema = {
            'collections': [
                'id', 'name', 'topic', 'dimension', 'database_id', 'config_json_str'
            ],
            'segments': [
                'id', 'type', 'scope', 'topic', 'collection', 'metadata'
            ]
        }
        
        for table, expected_cols in expected_schema.items():
            if table in schema:
                existing_cols = [col['name'] for col in schema[table]]
                missing = [col for col in expected_cols if col not in existing_cols]
                if missing:
                    missing_columns[table] = missing
            else:
                # Table doesn't exist - ChromaDB will create it
                logger.info(f"Table '{table}' doesn't exist - will be created by ChromaDB")
                
        return missing_columns
    
    def add_missing_columns(self, missing_columns: Dict[str, List[str]]) -> bool:
        """Add missing columns to the database"""
        if not missing_columns:
            logger.info("✅ No missing columns found")
            return True
            
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                cursor = conn.cursor()
                
                for table, columns in missing_columns.items():
                    logger.info(f"Adding missing columns to table '{table}': {columns}")
                    
                    for column in columns:
                        # Define column types based on ChromaDB expectations
                        column_definitions = {
                            'topic': 'TEXT',
                            'scope': 'TEXT', 
                            'collection': 'TEXT',
                            'metadata': 'TEXT'
                        }
                        
                        column_type = column_definitions.get(column, 'TEXT')
                        
                        try:
                            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                            logger.info(f"✅ Added column '{column}' to table '{table}'")
                        except sqlite3.OperationalError as e:
                            if "duplicate column name" in str(e).lower():
                                logger.info(f"Column '{column}' already exists in table '{table}'")
                            else:
                                raise e
                                
                conn.commit()
                logger.info("✅ All missing columns added successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to add missing columns: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """Verify that the migration was successful"""
        try:
            # Try to initialize ChromaDB with the migrated database
            from app.services.vector_store_service import VectorStoreService
            
            test_service = VectorStoreService()
            test_service.db_path = str(self.db_path)
            test_service.initialize()
            
            if test_service.is_ready():
                logger.info("✅ Migration verification successful - ChromaDB initializes correctly")
                return True
            else:
                logger.error("❌ Migration verification failed - ChromaDB not ready")
                return False
                
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False
    
    def migrate(self, create_backup: bool = True, force: bool = False) -> bool:
        """Perform the complete migration process"""
        logger.info("🚀 Starting ChromaDB schema migration...")
        
        # Check versions
        installed_version, expected_version = self.check_chromadb_version()
        logger.info(f"ChromaDB installed version: {installed_version}")
        logger.info(f"ChromaDB expected version: {expected_version}")
        
        if installed_version != expected_version:
            logger.warning(f"⚠️ Version mismatch detected!")
            if not force:
                response = input("Continue with migration? (y/N): ")
                if response.lower() != 'y':
                    logger.info("Migration cancelled by user")
                    return False
        
        # Create backup if requested
        if create_backup and not self.backup_database():
            logger.error("❌ Failed to create backup - aborting migration")
            return False
        
        # Check for missing columns
        missing_columns = self.check_missing_columns()
        if missing_columns:
            logger.info(f"Missing columns detected: {missing_columns}")
            
            # Add missing columns
            if not self.add_missing_columns(missing_columns):
                logger.error("❌ Failed to add missing columns")
                return False
        else:
            logger.info("✅ No schema issues detected")
        
        # Verify migration
        if not self.verify_migration():
            logger.error("❌ Migration verification failed")
            return False
        
        logger.info("🎉 ChromaDB schema migration completed successfully!")
        return True
    
    def rollback(self) -> bool:
        """Rollback to the backup database"""
        if not self.backup_path or not self.backup_path.exists():
            logger.error("❌ No backup found to rollback to")
            return False
            
        try:
            shutil.copy2(self.backup_path, self.sqlite_path)
            logger.info(f"✅ Rolled back to backup: {self.backup_path}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to rollback: {e}")
            return False

def main():
    """Main migration script entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ChromaDB Schema Migration Tool')
    parser.add_argument('--backup', action='store_true', 
                       help='Create backup before migration (default: True)')
    parser.add_argument('--no-backup', action='store_true',
                       help='Skip backup creation')
    parser.add_argument('--force', action='store_true',
                       help='Force migration even with version mismatches')
    parser.add_argument('--rollback', action='store_true',
                       help='Rollback to the most recent backup')
    parser.add_argument('--db-path', type=str,
                       help='Custom ChromaDB database path')
    
    args = parser.parse_args()
    
    # Determine database path
    if args.db_path:
        db_path = args.db_path
    else:
        # Use default path from settings or environment
        db_path = os.getenv("CHROMA_DB_PATH", 
                           os.path.join(os.getcwd(), "data", "chroma_db"))
    
    migrator = ChromaDBMigrator(db_path)
    
    if args.rollback:
        success = migrator.rollback()
    else:
        create_backup = not args.no_backup
        success = migrator.migrate(create_backup=create_backup, force=args.force)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()