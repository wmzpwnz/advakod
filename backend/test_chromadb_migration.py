#!/usr/bin/env python3
"""
Test script for ChromaDB migration

This script tests the ChromaDB migration functionality by:
1. Running the migration script
2. Testing ChromaDB initialization
3. Verifying that the schema issues are resolved
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the current directory to the path
sys.path.append('.')

def test_migration():
    """Test the ChromaDB migration process"""
    print("🧪 Testing ChromaDB migration...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db_path = os.path.join(temp_dir, "test_chroma_db")
        
        print(f"📁 Using test database path: {test_db_path}")
        
        # Test 1: Migration on fresh database
        print("\n1️⃣ Testing migration on fresh database...")
        try:
            from scripts.chromadb_migration import ChromaDBMigrator
            
            migrator = ChromaDBMigrator(test_db_path)
            success = migrator.migrate(create_backup=False, force=True)
            
            if success:
                print("✅ Fresh database migration successful")
            else:
                print("❌ Fresh database migration failed")
                return False
                
        except Exception as e:
            print(f"❌ Error during fresh migration: {e}")
            return False
        
        # Test 2: Test vector store service initialization
        print("\n2️⃣ Testing vector store service initialization...")
        try:
            from app.services.vector_store_service import VectorStoreService
            
            # Create a test service with the migrated database
            test_service = VectorStoreService()
            test_service.db_path = test_db_path
            test_service.initialize()
            
            if test_service.is_ready():
                print("✅ Vector store service initialization successful")
            else:
                print("❌ Vector store service initialization failed")
                return False
                
        except Exception as e:
            print(f"❌ Error during service initialization: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Test 3: Test basic operations
        print("\n3️⃣ Testing basic ChromaDB operations...")
        try:
            # Test adding a document
            success = test_service.add_document(
                content="Test document content",
                metadata={"source": "test", "title": "Test Document"}
            )
            
            if success:
                print("✅ Document addition successful")
            else:
                print("❌ Document addition failed")
                return False
            
            # Test searching with lower similarity threshold for testing
            import asyncio
            results = asyncio.run(test_service.search_similar("test", limit=1, min_similarity=0.0))
            
            if results and len(results) > 0:
                print("✅ Document search successful")
                print(f"   Found {len(results)} results with similarity: {results[0].get('similarity', 'N/A')}")
            else:
                print("❌ Document search failed")
                return False
                
        except Exception as e:
            print(f"❌ Error during basic operations: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n🎉 All ChromaDB migration tests passed!")
    return True

def test_existing_database():
    """Test migration on the existing database"""
    print("\n🔍 Testing migration on existing database...")
    
    # Use the actual database path
    db_path = os.getenv("CHROMA_DB_PATH", os.path.join(os.getcwd(), "data", "chroma_db"))
    
    if not os.path.exists(os.path.join(db_path, "chroma.sqlite3")):
        print("ℹ️ No existing database found - skipping existing database test")
        return True
    
    try:
        from scripts.chromadb_migration import ChromaDBMigrator
        
        migrator = ChromaDBMigrator(db_path)
        
        # Check current schema
        missing_columns = migrator.check_missing_columns()
        if missing_columns:
            print(f"⚠️ Missing columns detected: {missing_columns}")
            
            # Run migration
            success = migrator.migrate(create_backup=True, force=True)
            if success:
                print("✅ Existing database migration successful")
                return True
            else:
                print("❌ Existing database migration failed")
                return False
        else:
            print("✅ Existing database schema is already compatible")
            return True
            
    except Exception as e:
        print(f"❌ Error during existing database migration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting ChromaDB migration tests...")
    
    # Test migration functionality
    if not test_migration():
        print("❌ Migration tests failed")
        sys.exit(1)
    
    # Test on existing database
    if not test_existing_database():
        print("❌ Existing database tests failed")
        sys.exit(1)
    
    print("\n🎉 All tests passed! ChromaDB migration is working correctly.")