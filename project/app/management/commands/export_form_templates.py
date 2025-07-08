"""
Management command to export form templates from database to JSON files
"""
import os
import json
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from app.models import FormTemplate


class Command(BaseCommand):
    help = 'Export form templates from database to JSON files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--template-id',
            type=int,
            help='Export specific template by ID'
        )
        parser.add_argument(
            '--form-type',
            type=str,
            choices=['project', 'order', 'sample', 'custom'],
            help='Export all templates of a specific type'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='app/form_templates/exported',
            help='Directory to export files to'
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            default=True,
            help='Only export active templates (default: True)'
        )
        parser.add_argument(
            '--include-inactive',
            action='store_true',
            help='Include inactive templates'
        )
    
    def handle(self, *args, **options):
        # Get output directory
        output_dir = os.path.join(settings.BASE_DIR, options['output_dir'])
        
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Build query
        query = FormTemplate.objects.all()
        
        if options['template_id']:
            query = query.filter(id=options['template_id'])
        
        if options['form_type']:
            query = query.filter(form_type=options['form_type'])
        
        if not options['include_inactive']:
            query = query.filter(is_active=True)
        
        # Export templates
        exported_count = 0
        
        for template in query:
            # Generate filename
            filename = self._generate_filename(template)
            filepath = os.path.join(output_dir, filename)
            
            # Prepare data for export
            export_data = template.json_schema.copy() if template.json_schema else {}
            
            # Add metadata if not present
            export_data.update({
                'form_id': f"{template.form_type}_{template.id}",
                'form_type': template.form_type,
                'form_title': template.name,
                'form_description': template.description,
                'version': template.version,
                'facility_specific': template.facility_specific,
                'facility_name': template.facility_name,
            })
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(export_data, indent=2, fp=f)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Exported: {template} -> {filename}"
                )
            )
            exported_count += 1
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\nExported {exported_count} templates to {output_dir}"
            )
        )
    
    def _generate_filename(self, template):
        """
        Generate a filename for the template
        """
        # Start with form type
        parts = [template.form_type, 'form']
        
        # Add facility name if specific
        if template.facility_specific and template.facility_name:
            facility_slug = template.facility_name.lower().replace(' ', '_')
            parts.append(facility_slug)
        
        # Add version if not 1.0
        if template.version != '1.0':
            version_slug = template.version.replace('.', '_')
            parts.append(f'v{version_slug}')
        
        # Add ID to ensure uniqueness
        parts.append(str(template.id))
        
        return '_'.join(parts) + '.json'