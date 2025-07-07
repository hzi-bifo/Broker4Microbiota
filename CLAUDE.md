# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.



# Standard Workflow

First, think through the problem, read the codebase for relevant files, and write a plan to [PROJECTPLAN.md](PROJECTPLAN.md).
The plan should have a list of todo items that you can check off as you complete them. Before you begin working, check in with me and I will verify the plan. Then, begin working on the todo items, marking them as complete as you go. Please, at every step of the way, just give me a high-level explanation of what changes you made. Make every task and code change as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity. Finally, add a review section to the [PROJECTPLAN.md](PROJECTPLAN.md) file with a summary of the changes you made and any other relevant information.

## High-level architecture



## Project Overview

This is a Django application for managing sequencing orders and metadata collection for a bioinformatics facility. The system integrates with the European Nucleotide Archive (ENA) for sample submission and supports 17 different MIxS (Minimum Information about any (x) Sequence) checklists.

## Key Technologies

- **Django 5.0+** - Web framework
- **Python 3.8+** - Programming language
- **SQLite** - Default database
- **django-q2** - Task queue for asynchronous pipeline execution
- **Nextflow** - For running nf-core/mag bioinformatics pipeline
- **Biopython** - Biological data processing
- **Handsontable** - Spreadsheet-like UI for data entry

## Essential Commands

### Development Server
```bash
cd project
python manage.py runserver
```

### Database Operations
```bash
python manage.py makemigrations    # Create new migrations after model changes
python manage.py migrate           # Apply migrations
```

### Static Files
```bash
python manage.py collectstatic     # Update static files after XML/JSON changes
```

### Data Import/Export
```bash
python manage.py sync_excel                                    # Export database to Excel
python manage.py sync_excel --import /path/to/file.xlsx      # Import from Excel
python manage.py sample_xml_generator                         # Generate sample XML files
```

### Background Tasks
```bash
python manage.py qcluster          # Start the django-q2 task queue worker
```

## Architecture Overview

### Core Models (app/models.py)
- **User** - Django auth system for user management
- **Order** - Sequencing orders linked to users
- **Sample** - Biological samples linked to orders
- **MIxS Metadata** - Environmental metadata following MIxS standards
- **PipelineRun** - Tracks Nextflow pipeline executions

### Key Views (app/views.py)
- User authentication (register/login/logout)
- Order management (CRUD operations)
- Sample management with bulk operations
- MIxS metadata forms dynamically generated from XML templates
- Admin-only features: pipeline execution, ENA submission

### Background Processing
- Uses django-q2 for asynchronous task execution
- Primary use case: Running nf-core/mag pipeline on sample sets
- Configured with very long timeouts for bioinformatics pipelines

### Data Flow
1. Users create orders and associate samples
2. Samples are linked to MIxS environmental standards
3. Admin can export samples to ENA with auto-generated XML
4. Admin can run bioinformatics pipelines on sample sets
5. Results are tracked in the database

## Environment Configuration

Copy `TEMPLATE.env` to `.env` and set:
```bash
ENA_USERNAME=Webin-XXXXXX      # ENA submission account
ENA_PASSWORD=XXXXXXXXXX         # ENA password
ROOT_DIR=$HOME/git/django_ngs_metadata_collection
USE_SLURM_FOR_SUBMG=False      # Set to True for HPC environments
CONDA_PATH=                     # Path to conda installation if using Slurm
```

## MIxS Standards Configuration

- XML templates stored in `staticfiles/xml/EnvironmentID.xml`
- Supported environments defined in `app/mixs_metadata_standards.py`
- After modifying XML files, run `python manage.py collectstatic`

## Testing

Currently no test suite implemented. Test file exists at `project/app/tests.py` but is empty.

## Important Files and Locations

- Main settings: `project/project/settings.py`
- URL routing: `project/project/urls.py` and `project/app/urls.py`
- Form definitions: `project/app/forms.py`
- Admin customizations: `project/app/admin.py`
- Static assets: `project/staticfiles/` (XML templates, CSS, JS)
- Handsontable integration: `project/app/templates/app/handsontable.html`

## Security Notes

- Default SECRET_KEY in settings.py should be changed for production
- DEBUG = True should be set to False in production
- ENA credentials must be kept secure in environment variables