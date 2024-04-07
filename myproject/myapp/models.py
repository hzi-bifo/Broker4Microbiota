from django.db import models
from django.contrib.auth.models import User
from .mixs_metadata_standards import MIXS_METADATA_STANDARDS

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, null=True, blank=True)
    billing_address = models.TextField(null=True, blank=True)
    ag_and_hzi = models.CharField(max_length=100, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    quote_no = models.CharField(max_length=100, null=True, blank=True)
    contact_phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    data_delivery = models.CharField(max_length=100, null=True, blank=True)
    signature = models.CharField(max_length=100, null=True, blank=True)
    experiment_title = models.CharField(max_length=100, null=True, blank=True)
    dna = models.CharField(max_length=20, null=True, blank=True)
    rna = models.CharField(max_length=20, null=True, blank=True)
    library = models.CharField(max_length=20, null=True, blank=True)
    method = models.CharField(max_length=100, null=True, blank=True)
    buffer = models.CharField(max_length=100, null=True, blank=True)
    organism = models.CharField(max_length=100, null=True, blank=True)
    isolated_from = models.CharField(max_length=100, null=True, blank=True)
    isolation_method = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Order by {self.user.username}"

class Sample(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    sample_name = models.CharField(max_length=100, null=True, blank=True)
    concentration = models.CharField(max_length=100, null=True, blank=True)
    volume = models.CharField(max_length=100, null=True, blank=True)
    ratio_260_280 = models.CharField(max_length=100, null=True, blank=True)
    ratio_260_230 = models.CharField(max_length=100, null=True, blank=True)
    comments = models.TextField(null=True, blank=True)
    internal_id = models.DateTimeField(auto_now_add=True)
    mixs_metadata_standard = models.CharField(max_length=100, choices=MIXS_METADATA_STANDARDS, null=True, blank=True)

    def __str__(self):
        return self.sample_name or ''
