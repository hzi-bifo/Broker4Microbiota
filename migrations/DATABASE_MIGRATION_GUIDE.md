# Database Migration Guide

## Quick Migration

The database needs these missing tables and columns to work with the current code:

**Missing Tables:**
- `app_sitesettings` - Site configuration
- `app_statusnote` - Order status tracking  
- `app_formtemplate` - Dynamic forms
- `app_formsubmission` - Form submissions

**Missing Columns:**
- `app_order`: status, status_updated_at, status_notes, checklist_changed, library
- `app_sampleset`: selected_fields, field_overrides

## Migration Steps

### 1. Install Requirements
```bash
pip install cryptography
```

### 2. Run Migration Script
```bash
# Basic migration (creates tables and columns)
python migrate_database.py

# Or migrate with data from old database
python migrate_database.py db.sqlite3 db_local_working.sqlite3
```

The script will:
- Create a backup automatically
- Add all missing tables and columns
- Copy data from old database (if provided)
- Verify the migration worked

### 3. Set Environment Variable
Add to your `.env` file:
```bash
# Generate key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
FIELD_ENCRYPTION_KEY=your-generated-key-here
```

### 4. Mark Django Migrations as Applied
```bash
python manage.py migrate --fake
```

## Verify Success

If you see this output, you're ready to go:
```
✅ Migration completed successfully!
✅ Database is ready to use!
```

## Troubleshooting

- **"no such column" errors** → Run the migration script again
- **Can't find old data** → Make sure to provide the old database path as second argument
- **Django errors** → Make sure to run `migrate --fake` after the script

That's it! Your database is now compatible with the current Django models.