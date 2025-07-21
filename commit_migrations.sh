#!/bin/bash
# Script to commit migration tools

cd /Users/pmu15/Documents/github.com/hzi-bifo/Broker4Microbiota

# Add the migrations directory
git add migrations/

# Show status
echo "Git status:"
git status

# Create commit
git commit -m "Add database migration tools for schema updates

- Created migrate_database.py script for automated migrations
- Added simple migration guide
- Handles missing tables: app_sitesettings, app_statusnote, app_formtemplate, app_formsubmission
- Preserves existing data while updating schema

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to remote
git push origin main

echo "Migration tools committed and pushed successfully!"