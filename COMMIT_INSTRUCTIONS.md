# Commit Instructions for Migration Tools

The migration tools have been created and are ready to commit. Please run these commands in your terminal:

```bash
# Navigate to the project directory
cd /Users/pmu15/Documents/github.com/hzi-bifo/Broker4Microbiota

# Add the migrations directory
git add migrations/

# Create the commit
git commit -m "Add database migration tools for schema updates

- Created migrate_database.py script for automated migrations
- Added simple migration guide  
- Handles missing tables: app_sitesettings, app_statusnote, app_formtemplate, app_formsubmission
- Preserves existing data while updating schema

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to remote
git push origin main
```

## Files to be committed:
- `migrations/README.md` - Brief description of the migrations directory
- `migrations/migrate_database.py` - The migration script
- `migrations/DATABASE_MIGRATION_GUIDE.md` - Simple guide explaining the migration process

## Optional: Clean up duplicate files
If you have these files in the root directory, you can remove them:
```bash
rm -f DATABASE_MIGRATION_GUIDE.md complete_db_migration.sql migrate_database.py
```

The migration tools are now organized in a dedicated `/migrations/` directory to keep them separate from the main code.