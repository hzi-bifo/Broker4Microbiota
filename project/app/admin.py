from django.contrib import admin
from .models import Order, Sample

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'date', 'quote_no', 'billing_address', 'ag_and_hzi', 'contact_phone', 'email', 'data_delivery', 'signature', 'experiment_title', 'dna', 'rna', 'library', 'method', 'buffer', 'organism', 'isolated_from', 'isolation_method')

class SampleAdmin(admin.ModelAdmin):
    list_display = ('order', 'sample_name', 'concentration', 'volume', 'ratio_260_280', 'ratio_260_230', 'comments', 'internal_id', 'mixs_metadata_standard', 'mixs_metadata')

admin.site.register(Order, OrderAdmin)
admin.site.register(Sample, SampleAdmin)