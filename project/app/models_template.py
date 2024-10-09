from django.db import models
from django.contrib.auth.models import User
from .mixs_metadata_standards import MIXS_METADATA_STANDARDS, MIXS_METADATA_STANDARDS_FULL
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import JSONField
from django.core.validators import RegexValidator
import importlib
import json

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

class SelfDescribingModel(models.Model):

    class Meta:
        abstract = True

    def getSubAttributes(self, exclude=[], include=[]):
        output = ""
        if include:
            for k in self.fields.keys():
                if k in include:
                    output = output + f"<SAMPLE_ATTRIBUTE><TAG>{k}</TAG><VALUE>{getattr(self, k)}</VALUE></SAMPLE_ATTRIBUTE>\n"
        else:
            for k in self.fields.keys():
                if k not in exclude:
                    output = output + f"<SAMPLE_ATTRIBUTE><TAG>{k}</TAG><VALUE>{getattr(self, k)}</VALUE></SAMPLE_ATTRIBUTE>\n"
        return output


    def getFields(self, exclude=[], include=[]):
        output = {}
        if include:
            for k in self.fields.keys():
                if k in include:
                    output[k] = getattr(self, k) or ''
        else:
            for k in self.fields.keys():
                if k not in exclude:
                    output[k] = getattr(self, k) or ''

        return output            
    
    def getHeaders(self, exclude=[], include=[]):

        headers = ""

        if include:
            for k, v in self.fields.items():
                if k in include:
                    headers = headers + f"{{title: '{k}', data: '{k}'"
                    try:
                        choices = getattr(self, f"{k}_choice")
                        headers = headers + f", type: 'dropdown', source: {choices}"
                    except:
                        pass      
                    headers = headers + f"}},\n"
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    headers = headers + f"{{title: '{k}', data: '{k}'"
                    try:
                        choices = getattr(self, f"{k}_choice")
                        headers = headers + f", type: 'dropdown', source: {choices}"
                    except:
                        pass      
                    headers = headers + f"}},\n"

        return headers + ""

    def getHeadersArray(self, index, exclude=[], include=[]):

        # string containing (comma-delimited)
        output = ""
        if include:
                for k, v in self.fields.items():
                    if k in include:
                        output = output + f"{k}: row[{index}].trim(),\n"
                        index = index + 1
        else:
                for k, v in self.fields.items():
                    if k not in exclude:
                        output = output + f"{k}: row[{index}].trim(),\n"
                        index = index + 1

        return (index, output)    
    
    def setFieldsFromResponse(self, response):

        for k in self.fields.keys():
            try:
                value = response[k]
            except:
                value = ''
            if k == 'checklists':
                value= json.loads('["GSC_MIxS_wastewater_sludge", "GSC_MIxS_miscellaneous_natural_or_artificial_environment"]')
            setattr(self, k, value)

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

class Sample(SelfDescribingModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    sample_name = models.CharField(max_length=100, null=True, blank=True)

    checklists = models.JSONField()    
    
    #     mixs_metadata_standard = models.CharField(max_length=100, choices=MIXS_METADATA_STANDARDS, null=True, blank=True)
    #     alias = models.CharField(max_length=100, null=True, blank=True)
    #     title = models.CharField(max_length=100, null=True, blank=True)
    #     taxon_id = models.CharField(max_length=100, null=True, blank=True)
    #     scientific_name = models.CharField(max_length=100, null=True, blank=True)
    #     investigation_type = models.CharField(max_length=100, null=True, blank=True)
    #     study_type = models.CharField(max_length=100, null=True, blank=True)
    #     platform = models.CharField(max_length=100, null=True, blank=True)
    #     library_source = models.CharField(max_length=100, null=True, blank=True)
    #     concentration = models.CharField(max_length=100, null=True, blank=True)
    #     volume = models.CharField(max_length=100, null=True, blank=True)
    #     ratio_260_280 = models.CharField(max_length=100, null=True, blank=True)
    #     ratio_260_230 = models.CharField(max_length=100, null=True, blank=True)
    #     comments = models.TextField(null=True, blank=True)
    #     status = models.CharField(max_length=20, choices=STATUS_CHOICES, null=True, blank=True)
    #     date = models.DateTimeField(auto_now_add=True)
    #     mixs_metadata = JSONField(null=True, blank=True)
    #     filename_forward = models.CharField(max_length=255, null=True, blank=True, verbose_name="Filename (Forward, R1)")
    #     filename_reverse = models.CharField(max_length=255, null=True, blank=True, verbose_name="Filename (Reverse, R2)")
    #     nf_core_mag_outdir = models.CharField(max_length=255, null=True, blank=True)

    fields = {
        'sample_name': sample_name,
        'checklists': checklists,
    }


    checklist_structure = {
        'GSC_MIxS_wastewater_sludge': {'checklist_class_name': 'GSC_MIxS_wastewater_sludge', 'unitchecklist_class_name': 'GSC_MIxS_wastewater_sludge_unit'},
        'GSC_MIxS_miscellaneous_natural_or_artificial_environment': {'checklist_class_name': 'GSC_MIxS_miscellaneous_natural_or_artificial_environment', 'unitchecklist_class_name': 'GSC_MIxS_miscellaneous_natural_or_artificial_environment_unit'},
    }

    @property
    def getAttributes(self):
    	# go through each of the fields within eah of the checklists
        # get the checklists for this sample    
        
        output = ""

        for checklist in json.loads(json.dumps(self.checklists)):
            checklist_class_name = self.checklist_structure[checklist]['checklist_class_name']
            checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
            checklist_item_instance = checklist_item_class.objects.filter(sample = self, order=self.order).first()
            
            include = []
            exclude = []

            attributes = checklist_item_instance.getSubAttributes(exclude, include)
            
            output = output + f'{attributes}\n'

        return output    
                
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

""" AIR__NUMBER_OF_REPLICONS__REGEX= "[+-]?[0-9]+"

AIR__SEQUENCE_QUALITY_CHECK__CHOICES = [
    ('manual', 'manual'), 
    ('software', 'software'),
    ('none', 'none'),
]

AIR__SAMPLE_VOLUME_OR_WEIGHT_FOR_DNA_EXTRACTION__UNITS = [
    ('g', 'g'), 
    ('mL', 'mL'),
    ('mg', 'mg'),
    ('ng', 'ng'),
]


class Air_checklist(SelfDescribingModel):
    # order = models.ForeignKey(Order, on_delete=models.CASCADE)
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    project_name = models.CharField(max_length=100, null=True, blank=True)
    number_of_replicons = models.CharField(max_length=100, null=True, blank=True, validators=[RegexValidator(AIR__NUMBER_OF_REPLICONS__REGEX)])
    sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, null=True, blank=True)
    sequence_quality_check = models.CharField(max_length=100, choices=AIR__SEQUENCE_QUALITY_CHECK__CHOICES, null=True, blank=True)

    fields = {
        'project_name': project_name,
        'number_of_replicons': number_of_replicons,
        'sample_volume_or_weight_for_DNA_extraction': sample_volume_or_weight_for_DNA_extraction,
        'sequence_quality_check': sequence_quality_check,
    }

class Air_unitchecklist(SelfDescribingModel):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=AIR__SAMPLE_VOLUME_OR_WEIGHT_FOR_DNA_EXTRACTION__UNITS, null=True, blank=True)

    
class Blah_checklist(SelfDescribingModel):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    foo = models.CharField(max_length=100, null=True, blank=True)
 
    fields = {
        'foo': foo,
    }
  
class Blah_unitchecklist(SelfDescribingModel):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE) """
