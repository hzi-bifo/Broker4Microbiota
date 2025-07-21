# Migration Guide: Sequencing File Management Update

This guide explains how to migrate to the new version that includes improved sequencing file management functionality.

## Overview of Changes

The update adds functionality to:
- Configure where sequencing files are stored
- Check for existing FASTQ files on the filesystem
- Automatically link discovered files to samples
- Track when files are missing or have been deleted
- Simulate sequencing file delivery for testing

## Database Migration Steps

### 1. Update the Code

First, pull the latest changes from the repository:
```bash
git pull origin main
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

### 3. Run Database Migrations

The update adds a new field `sequencing_data_path` to the `SiteSettings` model:

```bash
cd project
python manage.py makemigrations
python manage.py migrate
```

**Note**: If you encounter integrity errors during migration, you may need to:
1. Back up your database first
2. Use the `--fake` flag: `python manage.py migrate app 0004_add_sequencing_data_path --fake`
3. Then manually add the column:
   ```bash
   echo "ALTER TABLE app_sitesettings ADD COLUMN sequencing_data_path VARCHAR(500) DEFAULT '';" | python manage.py dbshell
   ```

### 4. Configure the Sequencing Data Path

1. Navigate to the Admin Settings: http://yourdomain/admin-dashboard/settings/
2. Find the "Sequencing Data Configuration" section
3. Enter the path where your sequencing files are stored (e.g., `/data/sequencing` or `/mnt/sequencing_data`)
4. Leave empty to use the default path: `<project>/media/simulated_reads/`

## New Features Usage

### Check for Read Files
- Always visible button in the order detail view
- Searches the configured directory for FASTQ files matching sample IDs
- Links found files to samples
- Clears database entries for files that no longer exist

### Simulate Reads (Testing)
- Only visible when samples are missing read files
- Creates dummy FASTQ files for testing
- Files are named using sample IDs (e.g., `SAMPLE_1753087065861_1.fastq.gz`)
- Does NOT link files to samples - use "Check for Read Files" for that

## File Naming Convention

The system looks for files with these naming patterns:
- `{SAMPLE_ID}_1.fastq.gz` and `{SAMPLE_ID}_2.fastq.gz`
- `{SAMPLE_ID}_R1.fastq.gz` and `{SAMPLE_ID}_R2.fastq.gz`
- Additional suffixes are supported (e.g., `{SAMPLE_ID}_L001_1.fastq.gz`)

Where `{SAMPLE_ID}` is the sample identifier like `SAMPLE_1753087065861`.

## Important Changes

### Sample Identification
- The system now uses `sample_id` (e.g., SAMPLE_1753087065861) instead of `sample_alias` for file matching
- This ensures exact matching and prevents confusion between similar sample names

### Read Status Display
- The UI now only shows samples as having reads if the files actually exist
- Empty database entries (where files were deleted) are properly handled

### Workflow Separation
- "Simulate Reads" only creates files (mimics sequencing center delivery)
- "Check for Read Files" discovers and links files (mimics data processing)

## Troubleshooting

### Migration Errors
If you encounter database integrity errors:
1. Check that no foreign key constraints are violated
2. Consider backing up and restoring your database
3. Use the manual column addition method shown above

### File Discovery Issues
If files aren't being found:
1. Verify the sequencing_data_path is correctly configured
2. Check file permissions (the web server user must have read access)
3. Ensure files follow the naming convention
4. Check that files are valid gzipped FASTQ format

### UI Not Updating
After clicking "Check for Read Files":
1. Refresh the page to see updated read counts
2. Check the status messages for any errors
3. Verify files exist in the configured path

## Rollback Instructions

If you need to rollback this update:
1. Revert to the previous code version
2. Remove the migration:
   ```bash
   python manage.py migrate app 0003_order_checklist_changed_sampleset_field_overrides_and_more
   ```
3. Manually remove the column if needed:
   ```bash
   echo "ALTER TABLE app_sitesettings DROP COLUMN sequencing_data_path;" | python manage.py dbshell
   ```

## Support

For issues or questions about this migration, please open an issue in the repository.