"""
Management command to update model help texts from XML files
"""
import os
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path

class Command(BaseCommand):
    help = 'Updates model field help texts from XML files'

    def handle(self, *args, **options):
        # Dictionary to store field descriptions from XML
        field_descriptions = {}
        
        # Path to XML files
        xml_path = Path(settings.BASE_DIR) / 'static' / 'xml'
        
        # Process all XML files
        for xml_file in xml_path.glob('*.xml'):
            self.stdout.write(f'Processing {xml_file.name}...')
            
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                
                # Find all FIELD elements
                for field in root.findall('.//FIELD'):
                    name_elem = field.find('NAME')
                    desc_elem = field.find('DESCRIPTION')
                    
                    if name_elem is not None and desc_elem is not None:
                        field_name = name_elem.text.replace(' ', '_')
                        description = desc_elem.text
                        
                        # Store the description (use the longest one if we find duplicates)
                        if field_name not in field_descriptions or len(description) > len(field_descriptions[field_name]):
                            field_descriptions[field_name] = description
                            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {xml_file.name}: {str(e)}'))
        
        # Output the field descriptions
        self.stdout.write(self.style.SUCCESS(f'\nFound {len(field_descriptions)} unique field descriptions\n'))
        
        # Print some examples
        examples = ['experimental_factor', 'number_of_replicons', 'ventilation_rate', 'humidity']
        for field_name in examples:
            if field_name in field_descriptions:
                self.stdout.write(f'{field_name}:')
                self.stdout.write(f'  {field_descriptions[field_name][:200]}...\n')
        
        # Generate a Python file with all descriptions
        output_file = Path(settings.BASE_DIR) / 'app' / 'field_descriptions.py'
        with open(output_file, 'w') as f:
            f.write('"""\nField descriptions extracted from XML files\n"""\n\n')
            f.write('FIELD_DESCRIPTIONS = {\n')
            for field_name, description in sorted(field_descriptions.items()):
                # Escape quotes in description
                desc_escaped = description.replace('"', '\\"')
                f.write(f'    "{field_name}": "{desc_escaped}",\n')
            f.write('}\n')
        
        self.stdout.write(self.style.SUCCESS(f'Wrote field descriptions to {output_file}'))