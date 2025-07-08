# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Standard Workflow

First, think through the problem, read the codebase for relevant files, and write a plan to [PROJECTPLAN.md](PROJECTPLAN.md).
The plan should have a list of todo items that you can check off as you complete them. Before you begin working, check in with me and I will verify the plan. Then, begin working on the todo items, marking them as complete as you go. Please, at every step of the way, just give me a high-level explanation of what changes you made. Make every task and code change as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity. Finally, add a review section to the [PROJECTPLAN.md](PROJECTPLAN.md) file with a summary of the changes you made and any other relevant information.

Do not commmit changes on your own, only suggest to commit it but not star the process by your own.

## Project Overview

Broker4Microbiota is a Django-based metadata collection and management system for microbiome sequencing facilities. It streamlines the process of collecting sequencing orders, managing sample metadata according to MIxS standards, and submitting data to the European Nucleotide Archive (ENA). The system supports both manual data entry and programmatic submissions through integration with bioinformatics pipelines.

## Technical Architecture

### Core Technologies

- **Django 5.0+** - Web framework providing MVC architecture
- **Python 3.8+** - Primary programming language
- **SQLite** - Default database (production should use PostgreSQL/MySQL)
- **django-q2** - Task queue for asynchronous pipeline execution
- **Handsontable 14.1.0** - Spreadsheet UI for bulk data entry
- **jQuery 3.7.1** - JavaScript library for DOM manipulation
- **Nextflow** - Workflow engine for nf-core/mag pipeline
- **Biopython** - For FASTA/FASTQ file processing
- **xmltodict** - XML parsing for ENA submissions

### Database Schema

#### Core Models Hierarchy
```
User (Django Auth)
 └── Project (study-level metadata)
      └── Order (sequencing run metadata)
           ├── Sampleset (checklist configuration)
           ├── Sample (biological sample)
           │    ├── Read (sequencing files)
           │    ├── Assembly (optional)
           │    └── Bin (optional)
           ├── Assembly
           ├── Bin
           └── Alignment
```

#### Key Model Relationships

- **Project** → User: Many-to-One (users can have multiple projects)
- **Order** → Project: Many-to-One (projects can have multiple orders)
- **Sample** → Order: Many-to-One (orders can have multiple samples)
- **Read** → Sample: Many-to-One (samples can have multiple read files)
- **Checklist Models** → Sample & Sampleset: One-to-One (dynamic based on selection)

#### MIxS Checklist Models

The system includes 17 pairs of checklist models following GSC MIxS standards:
- Each environment type has a main model and a unit model
- Examples: `GSC_MIxS_water`, `GSC_MIxS_soil`, `GSC_MIxS_human_gut`
- Dynamically loaded based on user selection in `Sampleset.checklists`

### URL Structure and Views

#### Authentication Flow
```
/                    → login_view (entry point)
/register/           → register_view
/logout/             → logout_view
```

#### Main Application Flow
```
/projects/                              → ProjectListView
/project/create/                        → project_view (create)
/project/<id>/edit/                     → project_view (edit)
/project/<id>/orders/                   → OrderListView
/project/<id>/orders/create/            → order_view (create)
/project/<id>/orders/<id>/metadata/     → metadata_view
/project/<id>/orders/<id>/samples/<type>/ → samples_view
```

#### View Functions

- **Authentication Views**: Handle user registration, login, logout
- **Project Views**: CRUD operations for projects
- **Order Views**: CRUD operations for sequencing orders
- **Metadata View**: Interactive tree UI for selecting MIxS checklists
- **Samples View**: Handsontable interface for bulk sample data entry

### Order Status Workflow

The system implements a comprehensive order status tracking system with the following workflow:

#### Status Progression
```
Draft → Ready for Sequencing → Sequencing in Progress → Sequencing Completed → Data Processing → Data Delivered → Completed
```

#### Status Definitions

1. **Draft**: Initial state when order is created. User can edit all details.
2. **Ready for Sequencing**: User marks order as complete and ready for the sequencing center.
3. **Sequencing in Progress**: Sequencing center starts processing the samples.
4. **Sequencing Completed**: Raw sequencing is finished, data generation complete.
5. **Data Processing**: Bioinformatics analysis and quality control in progress.
6. **Data Delivered**: Final processed data delivered to user.
7. **Completed**: Order workflow finished, project archived.

#### Implementation for Sequencing Center Integration

For sequencing center staff to update order status, implement the following:

**API Endpoint** (to be implemented):
```python
# In views.py
@require_http_methods(["POST"])
@csrf_exempt  # For API access
def advance_order_status(request, order_id):
    """
    API endpoint for sequencing center to update order status
    Requires authentication token for security
    """
    # Validate authentication token
    # Update order status with notes
    # Send notification to user
    # Log status change for audit trail
```

**External Integration Points**:
- **LIMS Integration**: Connect to Laboratory Information Management System
- **Notification System**: Email/SMS alerts on status changes
- **API Authentication**: Token-based auth for sequencing center systems
- **Audit Logging**: Track all status changes with timestamp and user

**Security Considerations**:
- Use API tokens for sequencing center access
- Log all status changes for audit trail
- Validate status transitions (can't skip steps)
- Rate limiting to prevent abuse

## Essential Commands

### Development Server
```bash
source venv/bin/activate           # Activate virtual environment first!
cd project
python manage.py runserver         # Start on http://127.0.0.1:8000/
```

### Database Operations
```bash
python manage.py makemigrations    # Create new migrations after model changes
python manage.py migrate           # Apply migrations
python manage.py createsuperuser   # Create admin user
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

### Testing & Linting
```bash
python manage.py test              # Run tests (currently empty)
# No linting configuration found - consider adding flake8/black
```

## Code Organization

### Directory Structure
```
project/
├── app/                           # Main Django application
│   ├── models.py                  # Database models (1500+ lines)
│   ├── views.py                   # View logic (1000+ lines)
│   ├── forms.py                   # Django forms
│   ├── admin.py                   # Admin customizations
│   ├── urls.py                    # App URL routing
│   ├── utils.py                   # Helper functions
│   ├── async_calls.py             # Async task definitions
│   ├── management/commands/       # Custom Django commands
│   └── templates/                 # HTML templates
├── project/                       # Django project settings
│   ├── settings.py                # Main settings file
│   └── urls.py                    # Root URL configuration
├── static/                        # Static assets
│   ├── xml/                       # MIxS XML templates (17 files)
│   ├── json/                      # JSON configurations
│   ├── hot/                       # Handsontable assets
│   └── js/                        # JavaScript files
└── media/                         # User uploads
```

### Key Files and Their Purposes

#### Models (`app/models.py`)
- **SelfDescribingModel**: Abstract base class for models that generate XML/YAML
- **Project**: Study-level metadata (title, description, ENA accession)
- **Order**: Sequencing run metadata (platform, strategy, contact info)
- **Sample**: Core sample data with dynamic attributes from checklists
- **Read**: Sequencing file paths and checksums
- **Submission models**: Track ENA submission status
- **Pipeline models**: Track bioinformatics pipeline runs
- **SiteSettings**: Singleton model for site-wide branding configuration

#### Views (`app/views.py`)
- **Authentication**: Login, logout, registration
- **CRUD operations**: Projects, orders, samples
- **metadata_view**: Complex tree UI for checklist selection
- **samples_view**: Handsontable integration for bulk editing

#### Forms (`app/forms.py`)
- **ProjectForm**: Project creation/editing
- **OrderForm**: Order creation with field customization
- **BinForm**, **AssemblyForm**: Specialized sample types

#### Admin (`app/admin.py`)
- Custom admin actions for ENA submission
- Pipeline execution triggers
- Bulk operations on samples
- XML generation and validation
- SiteSettingsAdmin: Singleton admin for branding configuration

#### Context Processors (`app/context_processors.py`)
- **site_settings**: Injects branding configuration into all templates
- Uses caching to minimize database queries
- Provides fallback values for robustness

### Frontend Architecture

#### Templates
- **base.html**: Main layout with Bootstrap styling
- **metadata.html**: jqTree integration for checklist selection
- **samples.html**: Handsontable spreadsheet interface
- **order_list.html**: Dashboard showing orders with action buttons

#### JavaScript Components
- **Handsontable**: Provides Excel-like editing for sample data
- **jqTree**: Renders hierarchical checklist selection
- **Custom JS**: Form validation and dynamic UI updates

### Data Processing Flow

1. **User Registration/Login**
   - Standard Django auth system
   - User isolation enforced at view level

2. **Project Creation**
   - Basic metadata collection
   - ENA study accession tracking

3. **Order Management**
   - Sequencing parameters (Illumina/Nanopore)
   - Library preparation details
   - Contact information

4. **Metadata Configuration**
   - Interactive tree selection of MIxS checklists
   - Saved as JSON in Sampleset model
   - Determines which fields appear in sample forms

5. **Sample Data Entry**
   - Handsontable provides spreadsheet interface
   - Dynamic columns based on selected checklists
   - Validation based on MIxS requirements

6. **ENA Submission (Admin only)**
   - XML generation from model data
   - Batch submission support
   - Accession number tracking

7. **Pipeline Execution (Admin only)**
   - Triggers Nextflow pipelines
   - Tracks run status in database
   - Results linked back to samples

## Configuration and Environment

### Environment Variables
Copy `TEMPLATE.env` to `.env` and configure:
```bash
ENA_USERNAME=Webin-XXXXXX      # ENA submission account
ENA_USER=                       # Alternative ENA username field
ENA_PASSWORD=XXXXXXXXXX         # ENA password
ROOT_DIR=$HOME/git/django_ngs_metadata_collection
USE_SLURM_FOR_SUBMG=False      # Set to True for HPC environments
CONDA_PATH=                     # Path to conda installation if using Slurm
```

### Django Settings (`project/settings.py`)
- **SECRET_KEY**: Change for production!
- **DEBUG**: Set to False in production
- **ALLOWED_HOSTS**: Configure for your domain
- **DATABASES**: Default SQLite, use PostgreSQL/MySQL for production
- **STATIC_ROOT**: Where collectstatic puts files
- **MEDIA_ROOT**: User upload directory

### MIxS Standards Configuration
- XML templates: `project/static/xml/*.xml`
- JSON configs: `project/static/json/*.json`
- Checklist mapping: `app/models.py:Sampleset.checklist_structure`
- After changes: `python manage.py collectstatic`

## Common Development Tasks

### Managing Site Branding
1. Access Django admin at `/admin/`
2. Navigate to "Site Settings"
3. Update organization info, logos, colors, etc.
4. Changes are cached for 5 minutes - to force update:
   ```python
   from django.core.cache import cache
   cache.delete('site_settings')
   ```

### Adding a New MIxS Checklist
1. Add XML template to `static/xml/NewEnvironment.xml`
2. Add JSON config to `static/json/NewEnvironment.json`
3. Update `Sampleset.checklist_structure` in models.py
4. Create model classes: `GSC_MIxS_new_environment` and `GSC_MIxS_new_environment_unit`
5. Run migrations: `python manage.py makemigrations && python manage.py migrate`
6. Run `python manage.py collectstatic`

### Modifying Order Form Fields
1. Edit `OrderForm` class in `app/forms.py`
2. Update corresponding fields in `Order` model (`app/models.py`)
3. Run migrations
4. Update template if needed (`templates/order_form.html`)

### Adding Custom Sample Attributes
1. Add to relevant checklist model in `models.py`
2. Update the corresponding XML template
3. Run migrations and collectstatic
4. Fields automatically appear in Handsontable

### Working with Handsontable
- Configuration: `templates/samples.html`
- Column definitions generated from model fields
- Validators defined in model's `getValidators()` method
- Headers from model's `getHeaders()` method

## Admin Interface Customizations

### Custom Admin Actions
- **Generate SUBMG config**: Creates SubMG YAML files
- **Generate sample XMLs**: Prepares ENA submission files
- **Run MAG cluster**: Triggers nf-core/mag pipeline
- **Create gzipped files**: Compresses sequencing files

### Admin-Only Features
- ENA submission workflow
- Pipeline execution
- Bulk sample operations
- Direct database editing

## API Endpoints and Integration Points

### ENA Integration
- Submission endpoint: Admin actions trigger XML generation
- Uses Webin REST API for submissions
- Tracks accession numbers in database

### Excel Import/Export
- Custom management command: `sync_excel`
- Bidirectional sync with Excel files
- Preserves relationships and metadata

### Pipeline Integration
- Nextflow pipeline execution via django-q2
- MAG and SubMG pipeline support
- Results tracked in Pipelines model

## Debugging Tips

### Common Issues
1. **Handsontable not loading**: Check static files collected
2. **Checklist fields missing**: Verify XML/JSON files match model
3. **ENA submission fails**: Check credentials and 24-hour wait period
4. **Pipeline won't start**: Ensure django-q2 cluster is running

### Useful Django Shell Commands
```python
# Get all samples for a user
from app.models import Sample, User
user = User.objects.get(username='testuser')
samples = Sample.objects.filter(order__project__user=user)

# Check checklist configuration
from app.models import Sampleset
ss = Sampleset.objects.first()
print(ss.checklists)  # Shows selected checklists

# Debug ENA submission
from app.models import SampleSubmission
submission = SampleSubmission.objects.latest('id')
print(submission.submission_response)
```

## Security Considerations

1. **User Isolation**: Views filter by `request.user`
2. **CSRF Protection**: Enabled by default
3. **SQL Injection**: Use Django ORM, avoid raw queries
4. **File Uploads**: Validate file types and sizes
5. **Secrets**: Never commit `.env` file
6. **Production**: Disable DEBUG, use HTTPS, secure SECRET_KEY