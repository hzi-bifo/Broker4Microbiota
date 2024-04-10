from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from app.models import Sample, Submission, Order

class Command(BaseCommand):
    help = 'Generate XML for selected samples and create a new Submission'

    def add_arguments(self, parser):
        parser.add_argument('sample_ids', nargs='+', type=int, help='IDs of the samples to include in the XML')
        parser.add_argument('order_id', type=int, help='ID of the associated order')

    def handle(self, *args, **options):
        sample_ids = options['sample_ids']
        order_id = options['order_id']

        samples = Sample.objects.filter(id__in=sample_ids)
        order = Order.objects.get(id=order_id)

        context = {
            'samples': samples,
        }

        xml_content = render_to_string('admin/sample_xml_template.xml', context)

        submission = Submission.objects.create(
            order=order,
            sample_object_xml=xml_content,
        )
        submission.samples.set(samples)

        self.stdout.write(self.style.SUCCESS(f'Successfully created Submission {submission.id} with {samples.count()} samples'))