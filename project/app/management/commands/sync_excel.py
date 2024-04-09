from django.core.management.base import BaseCommand
from .excel_sync import export_to_excel, import_from_excel

class Command(BaseCommand):
    help = 'Sync data with Excel'

    def add_arguments(self, parser):
        parser.add_argument('--import', type=str, help='Path to the Excel file to import')

    def handle(self, *args, **options):
        if options['import']:
            import_from_excel(options['import'])
        else:
            export_to_excel()