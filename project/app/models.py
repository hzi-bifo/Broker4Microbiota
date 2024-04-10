from django.db import models
from django.contrib.auth.models import User
from .mixs_metadata_standards import MIXS_METADATA_STANDARDS, MIXS_METADATA_STANDARDS_FULL
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import JSONField

LIBRARY_CHOICES = [
    ('choice1', 'Choice 1'),
    ('choice2', 'Choice 2'),
    ('other', 'Other'),
]

ISOLATION_METHOD_CHOICES = [
    ('method1', 'Method 1'), 
    ('method2', 'Method 2'),
    ('other', 'Other'),
]

STATUS_CHOICES = [
    ('in_preparation', 'In Preparation'),
    ('sequencing', 'Sequencing'),
    ('finished', 'Finished'),
    ('uploaded_to_ENA', 'Uploaded to ENA'),
]

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    billing_address = models.TextField(null=True, blank=True)
    ag_and_hzi = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    quote_no = models.CharField(max_length=100, null=True, blank=True)
    contact_phone = PhoneNumberField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    data_delivery = models.CharField(max_length=100, null=True, blank=True)
    signature = models.CharField(max_length=100, null=True, blank=True)
    experiment_title = models.CharField(max_length=100, null=True, blank=True)
    dna = models.CharField(max_length=20, null=True, blank=True)
    rna = models.CharField(max_length=20, null=True, blank=True)
    library = models.CharField(max_length=20, choices=LIBRARY_CHOICES, null=True, blank=True)
    method = models.CharField(max_length=100, null=True, blank=True)
    buffer = models.CharField(max_length=100, null=True, blank=True)
    organism = models.CharField(max_length=100, null=True, blank=True)
    isolated_from = models.CharField(max_length=100, null=True, blank=True)
    isolation_method = models.CharField(max_length=100, choices=ISOLATION_METHOD_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"Order by {self.user.username}"


class Sample(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    sample_name = models.CharField(max_length=100, null=True, blank=True)
    alias = models.CharField(max_length=100, null=True, blank=True)
    title = models.CharField(max_length=100, null=True, blank=True)
    taxon_id = models.CharField(max_length=100, null=True, blank=True)
    scientific_name = models.CharField(max_length=100, null=True, blank=True)
    investigation_type = models.CharField(max_length=100, null=True, blank=True)
    study_type = models.CharField(max_length=100, null=True, blank=True)
    platform = models.CharField(max_length=100, null=True, blank=True)
    library_source = models.CharField(max_length=100, null=True, blank=True)
    concentration = models.CharField(max_length=100, null=True, blank=True)
    volume = models.CharField(max_length=100, null=True, blank=True)
    ratio_260_280 = models.CharField(max_length=100, null=True, blank=True)
    ratio_260_230 = models.CharField(max_length=100, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    mixs_metadata_standard = models.CharField(max_length=100, choices=MIXS_METADATA_STANDARDS, null=True, blank=True)
    mixs_metadata = JSONField(null=True, blank=True)
    filename_forward = models.CharField(max_length=255, null=True, blank=True, verbose_name="Filename (Forward, R1)")
    filename_reverse = models.CharField(max_length=255, null=True, blank=True, verbose_name="Filename (Reverse, R2)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    nf_core_mag_outdir = models.CharField(max_length=255, null=True, blank=True)

    def get_standard_id(self):
        # Find the tuple in MIXS_METADATA_STANDARDS that matches the selected standard and return the ID
        standard = next((item for item in MIXS_METADATA_STANDARDS_FULL if item[0] == self.mixs_metadata_standard), None)
        return standard[2] if standard else None

    def __str__(self):
        return self.sample_name or ''

class Submission(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    samples = models.ManyToManyField(Sample)
    sample_object_xml = models.TextField(null=True, blank=True)
    submission_object_xml = models.TextField(null=True, blank=True)
    receipt_xml = models.TextField(null=True, blank=True)
    sample_accession_number = models.CharField(max_length=100, null=True, blank=True)
    samea_accession_number = models.CharField(max_length=100, null=True, blank=True)
    accession_status = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Submission for Order {self.order.id}"

class Pipelines(models.Model):
    run_id = models.CharField(max_length=100, unique=True)
    samples = models.ManyToManyField(Sample)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    output_folder = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.run_id