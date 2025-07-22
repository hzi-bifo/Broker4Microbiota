#!/usr/bin/env python
"""
Fix missing columns in checklist tables
"""
import os
import django
import sqlite3

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.conf import settings
from django.db import connection
from app.models import Sampleset

def fix_all_missing_columns():
    """Add missing columns to all checklist tables"""
    
    db_path = settings.DATABASES['default']['NAME']
    print(f"Working with database: {db_path}")
    
    # Connect directly to SQLite
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List of common fields that might be missing
    common_fields = [
        ('project_name', 'varchar(120)'),
        ('experimental_factor', 'varchar(120)'),
        ('ploidy', 'varchar(120)'),
        ('number_of_replicons', 'varchar(120)'),
        ('relationship_to_oxygen', 'varchar(120)'),
    ]
    
    try:
        # Get all checklist table names
        for checklist_name, checklist_info in Sampleset.checklist_structure.items():
            table_name = f"app_{checklist_info['checklist_class_name'].lower()}"
            
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                print(f"Table {table_name} doesn't exist, skipping...")
                continue
                
            print(f"\nChecking table: {table_name}")
            
            # Get existing columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Add missing columns
            for field_name, field_type in common_fields:
                if field_name not in column_names:
                    print(f"  Adding missing '{field_name}' column...")
                    try:
                        cursor.execute(f"""
                            ALTER TABLE {table_name} 
                            ADD COLUMN {field_name} {field_type} DEFAULT ''
                        """)
                        conn.commit()
                        print(f"  ✓ Added {field_name}")
                    except Exception as e:
                        print(f"  ✗ Error adding {field_name}: {e}")
                        conn.rollback()
                        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("\nDone!")

if __name__ == "__main__":
    fix_all_missing_columns()