-- Complete Database Migration Script
-- This script migrates an old database schema to match current Django models
-- Run with: sqlite3 your_database.sqlite3 < complete_db_migration.sql

-- ============================================================================
-- PART 1: Create Missing Tables
-- ============================================================================

-- Create app_sitesettings table if it doesn't exist
CREATE TABLE IF NOT EXISTS "app_sitesettings" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "site_name" varchar(200) NOT NULL DEFAULT 'Sequencing Order Management',
    "organization_name" varchar(200) NOT NULL DEFAULT 'Helmholtz Centre for Infection Research',
    "organization_short_name" varchar(50) NOT NULL DEFAULT 'HZI',
    "tagline" varchar(500) NOT NULL DEFAULT 'Streamlining sequencing requests and ensuring compliance with MIxS standards',
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
    "empty_projects_text" text NOT NULL DEFAULT 'Welcome to the Sequencing Order Management System! Start by creating your first project to organize and track your sequencing requests.',
    "projects_with_samples_text" text NOT NULL DEFAULT 'You have active sequencing projects. Create a new project for a different study or continue working on your existing projects.',
    "project_form_title" varchar(200) NOT NULL DEFAULT 'Create New Project',
    "project_form_description" text NOT NULL DEFAULT '',
    "order_form_title" varchar(200) NOT NULL DEFAULT 'Create Sequencing Order',
    "order_form_description" text NOT NULL DEFAULT '',
    "submission_instructions" text NOT NULL DEFAULT '',
    "metadata_checklist_title" varchar(200) NOT NULL DEFAULT 'Select Metadata Standards',
    "metadata_checklist_description" text NOT NULL DEFAULT '',
    "ena_username" varchar(100) NOT NULL DEFAULT '',
    "ena_password" varchar(200) NOT NULL DEFAULT '',
    "ena_test_mode" bool NOT NULL DEFAULT 1,
    "ena_center_name" varchar(100) NOT NULL DEFAULT '',
    "created_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create app_statusnote table if it doesn't exist
CREATE TABLE IF NOT EXISTS "app_statusnote" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "created_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "note_type" varchar(20) NOT NULL DEFAULT 'internal',
    "content" text NOT NULL,
    "old_status" varchar(30),
    "new_status" varchar(30),
    "is_rejection" bool NOT NULL DEFAULT 0,
    "order_id" bigint NOT NULL REFERENCES "app_order" ("id") DEFERRABLE INITIALLY DEFERRED,
    "user_id" integer REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- Create app_formtemplate table if it doesn't exist
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
    "created_by_id" integer REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- Create app_formsubmission table if it doesn't exist
CREATE TABLE IF NOT EXISTS "app_formsubmission" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "submission_data" text NOT NULL DEFAULT '{}',
    "created_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "form_template_id" bigint NOT NULL REFERENCES "app_formtemplate" ("id") DEFERRABLE INITIALLY DEFERRED,
    "order_id" bigint REFERENCES "app_order" ("id") DEFERRABLE INITIALLY DEFERRED,
    "project_id" bigint REFERENCES "app_project" ("id") DEFERRABLE INITIALLY DEFERRED,
    "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED
);

-- ============================================================================
-- PART 2: Create Indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS "app_statusnote_order_id_idx" ON "app_statusnote" ("order_id");
CREATE INDEX IF NOT EXISTS "app_statusnote_user_id_idx" ON "app_statusnote" ("user_id");
CREATE INDEX IF NOT EXISTS "app_formtemplate_created_by_id_idx" ON "app_formtemplate" ("created_by_id");
CREATE INDEX IF NOT EXISTS "app_formsubmission_form_template_id_idx" ON "app_formsubmission" ("form_template_id");
CREATE INDEX IF NOT EXISTS "app_formsubmission_order_id_idx" ON "app_formsubmission" ("order_id");
CREATE INDEX IF NOT EXISTS "app_formsubmission_project_id_idx" ON "app_formsubmission" ("project_id");
CREATE INDEX IF NOT EXISTS "app_formsubmission_user_id_idx" ON "app_formsubmission" ("user_id");

-- ============================================================================
-- PART 3: Add Missing Columns to Existing Tables
-- Note: These will fail silently if columns already exist
-- ============================================================================

-- Add missing columns to app_order
ALTER TABLE app_order ADD COLUMN status varchar(30) DEFAULT 'draft';
ALTER TABLE app_order ADD COLUMN status_updated_at datetime;
ALTER TABLE app_order ADD COLUMN status_notes text DEFAULT '';
ALTER TABLE app_order ADD COLUMN checklist_changed bool DEFAULT 0;
ALTER TABLE app_order ADD COLUMN library varchar(100);

-- Add missing columns to app_sampleset
ALTER TABLE app_sampleset ADD COLUMN selected_fields TEXT DEFAULT '{}';
ALTER TABLE app_sampleset ADD COLUMN field_overrides TEXT DEFAULT '{}';

-- Add missing columns to app_sitesettings (for compatibility)
ALTER TABLE app_sitesettings ADD COLUMN logo varchar(100) DEFAULT '';
ALTER TABLE app_sitesettings ADD COLUMN favicon varchar(100) DEFAULT '';
ALTER TABLE app_sitesettings ADD COLUMN footer_text TEXT DEFAULT '';
ALTER TABLE app_sitesettings ADD COLUMN empty_projects_text TEXT DEFAULT 'Welcome to the Sequencing Order Management System! Start by creating your first project to organize and track your sequencing requests.';
ALTER TABLE app_sitesettings ADD COLUMN projects_with_samples_text TEXT DEFAULT 'You have active sequencing projects. Create a new project for a different study or continue working on your existing projects.';

-- Add missing columns to app_statusnote
ALTER TABLE app_statusnote ADD COLUMN is_rejection BOOLEAN NOT NULL DEFAULT 0;

-- Add missing columns to app_formtemplate
ALTER TABLE app_formtemplate ADD COLUMN json_schema TEXT;

-- ============================================================================
-- PART 4: Data Migrations and Fixes
-- ============================================================================

-- Update status defaults where NULL
UPDATE app_order SET status = 'draft' WHERE status IS NULL;
UPDATE app_order SET status_notes = '' WHERE status_notes IS NULL;
UPDATE app_order SET checklist_changed = 0 WHERE checklist_changed IS NULL;

-- Copy data between renamed columns if they exist
UPDATE app_sitesettings SET logo = logo_url WHERE logo = '' AND logo_url != '';
UPDATE app_sitesettings SET favicon = favicon_url WHERE favicon = '' AND favicon_url != '';
UPDATE app_sitesettings SET footer_text = footer_content WHERE footer_text = '' AND footer_content != '';

-- Copy schema to json_schema in formtemplate
UPDATE app_formtemplate SET json_schema = schema WHERE json_schema IS NULL AND schema IS NOT NULL;

-- Update is_rejection based on note_type
UPDATE app_statusnote SET is_rejection = 1 WHERE note_type = 'rejection';

-- ============================================================================
-- PART 5: Verification Queries
-- ============================================================================

SELECT '=== Migration Complete ===' as status;
SELECT 'Tables created/verified:' as info;
SELECT name FROM sqlite_master WHERE type='table' AND name IN ('app_sitesettings', 'app_statusnote', 'app_formtemplate', 'app_formsubmission') ORDER BY name;

SELECT '' as blank;
SELECT 'Key columns added:' as info;
SELECT 'app_order: status, status_updated_at, status_notes, checklist_changed, library' as columns;
SELECT 'app_sampleset: selected_fields, field_overrides' as columns;
SELECT 'app_statusnote: is_rejection' as columns;
SELECT 'app_formtemplate: json_schema' as columns;

-- ============================================================================
-- END OF MIGRATION SCRIPT
-- ============================================================================