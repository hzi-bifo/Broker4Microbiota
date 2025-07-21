#!/usr/bin/env python
"""
Database Migration Script
Migrates old database schema to current Django model structure
"""
import sqlite3
import sys
import os
from datetime import datetime

def run_sql(conn, sql, ignore_errors=False):
    """Execute SQL and handle errors"""
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        return True
    except sqlite3.OperationalError as e:
        if not ignore_errors:
            print(f"  ⚠️  {str(e)}")
        return False

def migrate_database(db_path='db.sqlite3', old_db_path=None):
    """Main migration function"""
    print(f"\n🚀 Starting database migration for: {db_path}")
    
    # Backup database
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"📦 Creating backup: {backup_path}")
    import shutil
    shutil.copy2(db_path, backup_path)
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        print("\n📋 Creating missing tables...")
        
        # 1. Create missing tables
        tables_sql = {
            'app_sitesettings': '''
                CREATE TABLE IF NOT EXISTS "app_sitesettings" (
                    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    "site_name" varchar(200) NOT NULL DEFAULT 'Sequencing Order Management',
                    "organization_name" varchar(200) NOT NULL DEFAULT 'Helmholtz Centre for Infection Research',
                    "organization_short_name" varchar(50) NOT NULL DEFAULT 'HZI',
                    "tagline" varchar(500) NOT NULL DEFAULT '',
                    "contact_email" varchar(254) NOT NULL DEFAULT 'sequencing@helmholtz-hzi.de',
                    "website_url" varchar(200) NOT NULL DEFAULT 'https://www.helmholtz-hzi.de',
                    "footer_content" text NOT NULL DEFAULT '',
                    "footer_text" text NOT NULL DEFAULT '',
                    "logo_url" varchar(200) NOT NULL DEFAULT '',
                    "logo" varchar(100) NOT NULL DEFAULT '',
                    "favicon_url" varchar(200) NOT NULL DEFAULT '',
                    "favicon" varchar(100) NOT NULL DEFAULT '',
                    "primary_color" varchar(7) NOT NULL DEFAULT '#3273dc',
                    "secondary_color" varchar(7) NOT NULL DEFAULT '#2366d1',
                    "order_submitted_message" text NOT NULL DEFAULT '',
                    "empty_projects_text" text NOT NULL DEFAULT 'Welcome!',
                    "projects_with_samples_text" text NOT NULL DEFAULT 'You have active projects.',
                    "project_form_title" varchar(200) NOT NULL DEFAULT 'Create New Project',
                    "project_form_description" text NOT NULL DEFAULT '',
                    "order_form_title" varchar(200) NOT NULL DEFAULT 'Create Order',
                    "order_form_description" text NOT NULL DEFAULT '',
                    "submission_instructions" text NOT NULL DEFAULT '',
                    "metadata_checklist_title" varchar(200) NOT NULL DEFAULT 'Select Standards',
                    "metadata_checklist_description" text NOT NULL DEFAULT '',
                    "ena_username" varchar(100) NOT NULL DEFAULT '',
                    "ena_password" varchar(200) NOT NULL DEFAULT '',
                    "ena_test_mode" bool NOT NULL DEFAULT 1,
                    "ena_center_name" varchar(100) NOT NULL DEFAULT '',
                    "created_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    "updated_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'app_statusnote': '''
                CREATE TABLE IF NOT EXISTS "app_statusnote" (
                    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    "created_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    "note_type" varchar(20) NOT NULL DEFAULT 'internal',
                    "content" text NOT NULL,
                    "old_status" varchar(30),
                    "new_status" varchar(30),
                    "is_rejection" bool NOT NULL DEFAULT 0,
                    "order_id" bigint NOT NULL,
                    "user_id" integer
                )
            ''',
            'app_formtemplate': '''
                CREATE TABLE IF NOT EXISTS "app_formtemplate" (
                    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    "name" varchar(200) NOT NULL,
                    "form_type" varchar(20) NOT NULL,
                    "description" text NOT NULL DEFAULT '',
                    "version" varchar(20) NOT NULL DEFAULT '1.0',
                    "is_active" bool NOT NULL DEFAULT 1,
                    "is_default" bool NOT NULL DEFAULT 0,
                    "facility_specific" bool NOT NULL DEFAULT 0,
                    "facility_name" varchar(200) NOT NULL DEFAULT '',
                    "schema" text NOT NULL DEFAULT '{}',
                    "json_schema" text NOT NULL DEFAULT '{}',
                    "created_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    "updated_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    "created_by_id" integer
                )
            ''',
            'app_formsubmission': '''
                CREATE TABLE IF NOT EXISTS "app_formsubmission" (
                    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                    "submission_data" text NOT NULL DEFAULT '{}',
                    "created_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    "updated_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    "form_template_id" bigint NOT NULL,
                    "order_id" bigint,
                    "project_id" bigint,
                    "user_id" integer NOT NULL
                )
            '''
        }
        
        for table_name, sql in tables_sql.items():
            if run_sql(conn, sql):
                print(f"  ✅ Created {table_name}")
            else:
                print(f"  ℹ️  {table_name} already exists")
        
        # 2. Add missing columns
        print("\n🔧 Adding missing columns...")
        
        columns_to_add = [
            # app_order columns
            ("app_order", "status", "varchar(30) DEFAULT 'draft'"),
            ("app_order", "status_updated_at", "datetime"),
            ("app_order", "status_notes", "text DEFAULT ''"),
            ("app_order", "checklist_changed", "bool DEFAULT 0"),
            ("app_order", "library", "varchar(100)"),
            
            # app_sampleset columns
            ("app_sampleset", "selected_fields", "TEXT DEFAULT '{}'"),
            ("app_sampleset", "field_overrides", "TEXT DEFAULT '{}'"),
            
            # app_statusnote columns
            ("app_statusnote", "is_rejection", "BOOLEAN DEFAULT 0"),
            
            # app_formtemplate columns
            ("app_formtemplate", "json_schema", "TEXT DEFAULT '{}'"),
            
            # app_sitesettings compatibility columns
            ("app_sitesettings", "logo", "varchar(100) DEFAULT ''"),
            ("app_sitesettings", "favicon", "varchar(100) DEFAULT ''"),
            ("app_sitesettings", "footer_text", "TEXT DEFAULT ''"),
        ]
        
        for table, column, definition in columns_to_add:
            sql = f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
            if run_sql(conn, sql, ignore_errors=True):
                print(f"  ✅ Added {table}.{column}")
        
        # 3. Data migrations
        print("\n📊 Migrating data...")
        
        # Update default values
        run_sql(conn, "UPDATE app_order SET status = 'draft' WHERE status IS NULL", True)
        run_sql(conn, "UPDATE app_statusnote SET is_rejection = 1 WHERE note_type = 'rejection'", True)
        run_sql(conn, "UPDATE app_formtemplate SET json_schema = schema WHERE json_schema IS NULL AND schema IS NOT NULL", True)
        
        # Copy data between renamed columns
        run_sql(conn, "UPDATE app_sitesettings SET logo = logo_url WHERE logo = '' AND logo_url != ''", True)
        run_sql(conn, "UPDATE app_sitesettings SET favicon = favicon_url WHERE favicon = '' AND favicon_url != ''", True)
        run_sql(conn, "UPDATE app_sitesettings SET footer_text = footer_content WHERE footer_text = '' AND footer_content != ''", True)
        
        # 4. Copy data from old database if provided
        if old_db_path and os.path.exists(old_db_path):
            print(f"\n📥 Copying data from old database: {old_db_path}")
            old_conn = sqlite3.connect(old_db_path)
            old_conn.row_factory = sqlite3.Row
            
            try:
                # Copy SiteSettings if not exists
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM app_sitesettings")
                if cursor.fetchone()[0] == 0:
                    old_cursor = old_conn.cursor()
                    old_cursor.execute("SELECT * FROM app_sitesettings LIMIT 1")
                    old_settings = old_cursor.fetchone()
                    if old_settings:
                        # Map and insert with safe column names
                        conn.execute("""
                            INSERT INTO app_sitesettings (
                                site_name, organization_name, organization_short_name,
                                tagline, contact_email, website_url, primary_color,
                                secondary_color, ena_username, ena_password,
                                ena_test_mode, ena_center_name
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            old_settings['site_name'], old_settings['organization_name'],
                            old_settings['organization_short_name'], old_settings['tagline'],
                            old_settings['contact_email'], old_settings['website_url'],
                            old_settings['primary_color'], old_settings['secondary_color'],
                            old_settings.get('ena_username', ''), old_settings.get('ena_password', ''),
                            old_settings.get('ena_test_mode', 1), old_settings.get('ena_center_name', '')
                        ))
                        print("  ✅ Copied SiteSettings")
                
                # Copy StatusNotes
                old_cursor = old_conn.cursor()
                old_cursor.execute("SELECT * FROM app_statusnote")
                notes = old_cursor.fetchall()
                copied = 0
                for note in notes:
                    try:
                        conn.execute("""
                            INSERT INTO app_statusnote (
                                id, created_at, note_type, content,
                                old_status, new_status, order_id, user_id, is_rejection
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            note['id'], note['created_at'], note['note_type'],
                            note['content'], note.get('old_status'), note.get('new_status'),
                            note['order_id'], note.get('user_id'),
                            1 if note.get('note_type') == 'rejection' else 0
                        ))
                        copied += 1
                    except:
                        pass
                if copied > 0:
                    print(f"  ✅ Copied {copied} StatusNote records")
                    
            finally:
                old_conn.close()
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # 5. Verify migration
        print("\n🔍 Verifying migration...")
        cursor = conn.cursor()
        
        # Check tables exist
        for table in ['app_sitesettings', 'app_statusnote', 'app_formtemplate', 'app_formsubmission']:
            cursor.execute(f"SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone()[0] > 0:
                print(f"  ✅ Table {table} exists")
            else:
                print(f"  ❌ Table {table} missing!")
        
        # Check key columns
        cursor.execute("PRAGMA table_info(app_order)")
        order_columns = [row[1] for row in cursor.fetchall()]
        for col in ['status', 'status_updated_at', 'checklist_changed']:
            if col in order_columns:
                print(f"  ✅ app_order.{col} exists")
            else:
                print(f"  ❌ app_order.{col} missing!")
        
        print("\n✅ Database is ready to use!")
        print(f"💾 Backup saved as: {backup_path}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    # Parse arguments
    db_path = 'db.sqlite3'
    old_db_path = None
    
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    if len(sys.argv) > 2:
        old_db_path = sys.argv[2]
    
    migrate_database(db_path, old_db_path)