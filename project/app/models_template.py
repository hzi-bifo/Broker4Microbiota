from django.db import models
from django.contrib.auth.models import User
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

        class_name = type(self).__name__
        unit_class_name = f"{class_name}_unit"
        unitchecklist_class =  getattr(importlib.import_module("app.models"), unit_class_name)
        unitchecklist_item_instance = unitchecklist_class.objects.filter(order=self.order).first()

        output = ""
        if include:
            for k, v in self.fields.items():
                if k in include:
                    output = output + f"<SAMPLE_ATTRIBUTE><TAG>{v}</TAG><VALUE>{getattr(self, k)}</VALUE>"
                    try:
                        unitoption = getattr(unitchecklist_item_instance, k + "_units")[0][0]
                        current_unitoption = getattr(unitchecklist_item_instance, f"{k}")
                        if current_unitoption != '':
                            unitoption = current_unitoption   
                        output = output + f"<UNITS>{unitoption}</UNITS>\n"
                    except:
                        pass
                    output = output + f"</SAMPLE_ATTRIBUTE>\n"            
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    output = output + f"<SAMPLE_ATTRIBUTE><TAG>{v}</TAG><VALUE>{getattr(self, k)}</VALUE>"
                    try:
                        unitoption = getattr(unitchecklist_item_instance, k + "_units")[0][0]
                        current_unitoption = getattr(unitchecklist_item_instance, f"{k}")
                        if current_unitoption != '':
                            unitoption = current_unitoption   
                        output = output + f"<UNITS>{unitoption}</UNITS>\n"
                    except:
                        pass
                    output = output + f"</SAMPLE_ATTRIBUTE>\n"            
        return output

    # Get actual value for each field
    def getFields(self, exclude=[], include=[]):
        output = {}
        if include:
            for k, v in self.fields.items():
                if k in include:
                    output[k] = getattr(self, k) or ''
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    output[k] = getattr(self, k) or ''

        return output            
    
    # Get the headers for the HoT (including choices)
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

    # Get the headers for returning the data output from HoT
    def getHeadersArray(self, index, exclude=[], include=[]):

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
    
    # Populate instance fields from a response
    def setFieldsFromResponse(self, response):

        for k, v in self.fields.items():
            try:
                value = response[k]
            except:
                value = ''
            setattr(self, k, value)



# class SelfDescribingUnitModel(SelfDescribingModel):

#     class Meta:
#         abstract = True

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)

    #     for field in self.fields.keys():
    #         value = getattr(self, field+"_units")[0][0]
    #         setattr(self, field, value)

class Project(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, null=True, blank=True)
    alias = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    study_accession_id = models.CharField(max_length=100, null=True, blank=True)
    alternative_accession_id = models.CharField(max_length=100, null=True, blank=True)

class Order(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
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

class Sampleset(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    # list of checklists
    checklists = models.JSONField()
    include = models.JSONField()
    exclude = models.JSONField()
    custom = models.JSONField()

    # fields = {
    #     'order': 'order',
    #     'checklists': 'checklists',
    #     'include': 'include',
    #     'exclude': 'exclude',
    #     'custom': 'custom',
    # }

    checklist_structure = {
        'GSC_MIxS_wastewater_sludge': {"checklist_code" : "ERC000023", 'checklist_class_name': 'GSC_MIxS_wastewater_sludge', 'unitchecklist_class_name': 'GSC_MIxS_wastewater_sludge_unit'},
        'GSC_MIxS_miscellaneous_natural_or_artificial_environment': {"checklist_code" : "ERC0000xx", 'checklist_class_name': 'GSC_MIxS_miscellaneous_natural_or_artificial_environment', 'unitchecklist_class_name': 'GSC_MIxS_miscellaneous_natural_or_artificial_environment_unit'},
    }

class Sample(SelfDescribingModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    # from ENA spreadsheet download

    sample_id = models.CharField(max_length=100, null=True, blank=True)
    tax_id = models.CharField(max_length=100, null=True, blank=True)
    scientific_name = models.CharField(max_length=100, null=True, blank=True)
    sample_alias = models.CharField(max_length=100, null=True, blank=True)
    sample_title = models.CharField(max_length=100, null=True, blank=True)
    sample_description = models.CharField(max_length=100, null=True, blank=True)
    sample_accession_number = models.CharField(max_length=100, null=True, blank=True)
    sample_biosample_number = models.CharField(max_length=100, null=True, blank=True)


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
    #     filename_forward = models.CharField(max_length=255, null=True, blank=True, verbose_name="Filename (Forward, R1)")
    #     filename_reverse = models.CharField(max_length=255, null=True, blank=True, verbose_name="Filename (Reverse, R2)")
    #     nf_core_mag_outdir = models.CharField(max_length=255, null=True, blank=True)

    fields = {
        'sample_id': 'sample_id',
        'tax_id': 'tax_id',
        'scientific_name': 'scientific_name',
        'sample_alias': 'sample_alias',
        'sample_title': 'sample_title',
        'sample_description': 'sample_description',
        'sample_accession_number': 'sample_accession_number',
        'sample_biosample_number': 'sample_biosample_number',
    }

    # @property
    # def getAttributes(self):
    # 	# go through each of the fields within eah of the checklists
    #     # get the checklists for this sample    
        
    #     output = ""
    #     checklists = Sampleset.objects.filter(order=self.order).first().checklists
 
    #     for checklist in json.loads(json.dumps(checklists)):
    #         checklist_name = checklist
    #         checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
    #         checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
    #         checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
    #         checklist_item_instance = checklist_item_class.objects.filter(sample = self, order=self.order).first()
            
    #         include = []
    #         exclude = []

    #         attributes = checklist_item_instance.getSubAttributes(exclude, include)

    #         attributes = attributes + f"<SAMPLE_ATTRIBUTE><TAG>ena-checklist</TAG><VALUE>{checklist_code}</VALUE></SAMPLE_ATTRIBUTE>\n"

    #         output = output + f'{attributes}\n'

    #     return output    


class ProjectSubmission(models.Model):
    projects = models.ManyToManyField(Project)
    project_object_xml = models.TextField(null=True, blank=True)
    submission_object_xml = models.TextField(null=True, blank=True)
    receipt_xml = models.TextField(null=True, blank=True)
    accession_status = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Submission for Project" #  {self.project.id}



class SequenceTemplate(models.Model):
    template_id = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    platform = models.CharField(max_length=100, null=True, blank=True)
    insert_size = models.CharField(max_length=100, null=True, blank=True)
    library_name = models.CharField(max_length=100, null=True, blank=True)
    library_source = models.CharField(max_length=100, null=True, blank=True)
    library_selection = models.CharField(max_length=100, null=True, blank=True)
    library_strategy = models.CharField(max_length=100, null=True, blank=True)

class Sequence(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    sequence_template = models.ForeignKey(SequenceTemplate, on_delete=models.CASCADE)
    file_1 = models.CharField(max_length=255, null=True, blank=True)
    file_2 = models.CharField(max_length=255, null=True, blank=True)
    experiment_accession_number = models.CharField(max_length=100, null=True, blank=True)
    run_accession_number = models.CharField(max_length=100, null=True, blank=True)

class Submission(models.Model):
    samples = models.ManyToManyField(Sample)
    sample_object_xml = models.TextField(null=True, blank=True)
    submission_object_xml = models.TextField(null=True, blank=True)
    receipt_xml = models.TextField(null=True, blank=True)
    accession_status = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Submission for Order " # {self.order.id}

class ReadSubmission(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    samples = models.ManyToManyField(Sample)
    # Should be sequences???
    read_object_txt_list = models.JSONField()
    receipt_xml = models.TextField(null=True, blank=True)
    accession_status = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Read Submission for Order " # {self.order.id}

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

