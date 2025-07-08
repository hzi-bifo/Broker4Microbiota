"""
Management command to load form templates from JSON files
"""
import os
import json
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.contrib.auth import get_user_model
from app.models import FormTemplate
from app.dynamic_forms import validate_form_schema

User = get_user_model()


class Command(BaseCommand):
    help = 'Load form templates from JSON files into the database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Specific JSON file to load (e.g., project_form_default.json)'
        )
        parser.add_argument(
            '--directory',
            type=str,
            default='app/form_templates',
            help='Directory containing form template JSON files'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing form templates before loading'
        )
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Only validate the JSON files without loading them'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Username of the user to set as creator (defaults to first superuser)'
        )
    
    def handle(self, *args, **options):
        # Get the user for created_by field
        if options['user']:
            try:
                user = User.objects.get(username=options['user'])
            except User.DoesNotExist:
                raise CommandError(f"User '{options['user']}' does not exist")
        else:
            # Default to first superuser
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                raise CommandError("No superuser found. Please create a superuser or specify --user")
        
        # Clear existing templates if requested
        if options['clear'] and not options['validate_only']:
            self.stdout.write('Clearing existing form templates...')
            FormTemplate.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all form templates'))
        
        # Get the directory path
        directory = os.path.join(settings.BASE_DIR, options['directory'])
        if not os.path.exists(directory):
            raise CommandError(f"Directory does not exist: {directory}")
        
        # Get list of files to process
        if options['file']:
            files = [options['file']]
        else:
            files = [
                f for f in os.listdir(directory) 
                if f.endswith('.json') and f != 'form_schema.json'
            ]
        
        # Process each file
        loaded_count = 0
        error_count = 0
        
        for filename in files:
            filepath = os.path.join(directory, filename)
            
            if not os.path.exists(filepath):
                self.stdout.write(
                    self.style.ERROR(f"File not found: {filepath}")
                )
                error_count += 1
                continue
            
            try:
                # Load and parse JSON
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                # Validate schema
                is_valid, error_msg = validate_form_schema(data)
                if not is_valid:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Invalid schema in {filename}: {error_msg}"
                        )
                    )
                    error_count += 1
                    continue
                
                if options['validate_only']:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ {filename} is valid")
                    )
                    continue
                
                # Extract metadata
                form_id = data.get('form_id')
                form_type = data.get('form_type')
                version = data.get('version', '1.0')
                
                # Check if template already exists
                existing = FormTemplate.objects.filter(
                    name=data.get('form_title', form_id),
                    version=version,
                    facility_name=data.get('facility_name', '')
                ).first()
                
                if existing:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Template already exists: {filename} "
                            f"(name='{existing.name}', version={version})"
                        )
                    )
                    
                    # Update the JSON schema
                    existing.json_schema = data
                    existing.is_active = True
                    existing.save()
                    self.stdout.write(
                        self.style.SUCCESS(f"Updated existing template")
                    )
                else:
                    # Create new template
                    template = FormTemplate(
                        name=data.get('form_title', form_id),
                        form_type=form_type,
                        description=data.get('form_description', ''),
                        version=version,
                        is_active=True,
                        facility_specific=data.get('facility_specific', False),
                        facility_name=data.get('facility_name', ''),
                        json_schema=data,
                        created_by=user
                    )
                    template.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Loaded: {filename} -> {template}"
                        )
                    )
                
                loaded_count += 1
                
            except json.JSONDecodeError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Invalid JSON in {filename}: {str(e)}"
                    )
                )
                error_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"Error loading {filename}: {str(e)}"
                    )
                )
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '-' * 50)
        if options['validate_only']:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Validation complete: {loaded_count} valid, {error_count} errors"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Loading complete: {loaded_count} loaded, {error_count} errors"
                )
            )
            
            # Show current templates
            templates = FormTemplate.objects.filter(is_active=True)
            self.stdout.write('\nActive form templates:')
            for template in templates:
                self.stdout.write(
                    f"  - {template.name} v{template.version} "
                    f"({template.form_type})"
                    f"{' [Facility: ' + template.facility_name + ']' if template.facility_specific else ''}"
                )