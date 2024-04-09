from django.contrib import admin
from .models import Order, Sample

def add_example_filenames(modeladmin, request, queryset):
    for sample in queryset:
        sample.filename_forward = f"samples/Sample{sample.id}_R1.fastq"
        sample.filename_reverse = f"samples/Sample{sample.id}_R2.fastq"
        sample.save()

add_example_filenames.short_description = "Add example filenames"

class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'date', 'quote_no', 'billing_address', 'ag_and_hzi', 'contact_phone', 'email', 'data_delivery', 'signature', 'experiment_title', 'dna', 'rna', 'library', 'method', 'buffer', 'organism', 'isolated_from', 'isolation_method')

class SampleAdmin(admin.ModelAdmin):
    list_display = ('order', 'id', 'concentration', 'volume', 'ratio_260_280', 'ratio_260_230', 'comments', 'date', 'mixs_metadata_standard', 'mixs_metadata',  'filename_forward', 'filename_reverse', 'status')
    actions = [add_example_filenames]

admin.site.register(Order, OrderAdmin)
admin.site.register(Sample, SampleAdmin)