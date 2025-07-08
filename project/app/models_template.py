from django.db import models
from django.contrib.auth.models import User
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import JSONField
from django.core.validators import RegexValidator
import importlib
import json
from pathlib import Path

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

SAMPLE_TYPE_NORMAL = 1
SAMPLE_TYPE_ASSEMBLY = 2
SAMPLE_TYPE_BIN = 3
SAMPLE_TYPE_MAG = 4

class SelfDescribingModel(models.Model):

    class Meta:
        abstract = True

    def getSubAttributes(self, include=[], exclude=[]):

        class_name = type(self).__name__
        unit_class_name = f"{class_name}_unit"
        unitchecklist_class =  getattr(importlib.import_module("app.models"), unit_class_name)
        unitchecklist_item_instance = unitchecklist_class.objects.filter(sampleset=self.sampleset).first()

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

    def getSubAttributesYAML(self, indent="", include=[], exclude=[]):


        class_name = type(self).__name__
        unit_class_name = f"{class_name}_unit"
        unitchecklist_class =  getattr(importlib.import_module("app.models"), unit_class_name)
        unitchecklist_item_instance = unitchecklist_class.objects.filter(sampleset=self.sampleset).first()

        yaml = []
        if include:
            for k, v in self.fields.items():
                if k in include:
                    yaml.append(f"{indent}{v}: \"{getattr(self, k).replace('\n', '|')}\"")
                    try:
                        unitoption = getattr(unitchecklist_item_instance, k + "_units")[0][0]
                        current_unitoption = getattr(unitchecklist_item_instance, f"{k}")
                        if current_unitoption != '':
                            unitoption = current_unitoption   
                        # output = output + f"<UNITS>{unitoption}</UNITS>\n"
                    except:
                        pass
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    yaml.append(f"{indent}{v}: \"{getattr(self, k).replace('\n', '|')}\"")
                    try:
                        unitoption = getattr(unitchecklist_item_instance, k + "_units")[0][0]
                        current_unitoption = getattr(unitchecklist_item_instance, f"{k}")
                        if current_unitoption != '':
                            unitoption = current_unitoption   
                        # output = output + f"<UNITS>{unitoption}</UNITS>\n"
                    except:
                        pass
        return yaml


    # Get actual value for each field
    def getFields(self, include=[], exclude=[]):
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
    def getHeaders(self, include=[], exclude=[], extra_choices=[]):

        headers = ""

        if include:
            for k, v in self.fields.items():
                if k in include:
                    headers = headers + f"{{title: '{k}', data: '{k}'"
                    try:
                        choices = getattr(self, f"{k}_choice")
                        single_choice = [t[0] for t in choices]
                        if k == "sequence_quality_check":
                            strict = "true"
                        else:
                            strict = "true"
                        headers = headers + f", type: 'autocomplete', source: {single_choice}, strict: {strict}, allowInvalid: true"
                    except:
                        pass
                    if (k == 'assembly' or k == 'bin') and len(extra_choices) > 0:
						# ['Afghanistan', 'Albania']
                        single_choice = extra_choices
                        headers = headers + f", type: 'autocomplete', source: {single_choice}, strict: true, allowInvalid: true"
                    try:
                        validator = getattr(self, f"validator: {k}_validator")
                        headers = headers + f", validator: {k}_validator, allowInvalid: true"
                    except:
                        pass
                    headers = headers + f"}},\n"
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    headers = headers + f"{{title: '{k}', data: '{k}'"
                    try:
                        choices = getattr(self, f"{k}_choice")
                        single_choice = [t[0] for t in choices]
                        if k == "sequence_quality_check":
                            strict = "true"
                        else:
                            strict = "true"
                        headers = headers + f", type: 'autocomplete', source: {single_choice}, strict: {strict}, allowInvalid: true"
                    except:
                        pass
                    if (k == 'assembly' or k == 'bin') and  len(extra_choices) > 0:
						# ['Afghanistan', 'Albania']
                        single_choice = extra_choices
                        headers = headers + f", type: 'autocomplete', source: {single_choice}, strict: true, allowInvalid: true"
                    try:
                        validator = getattr(self, f"{k}_validator")
                        headers = headers + f", validator: {k}_validator, allowInvalid: true"
                    except:
                        pass
                    headers = headers + f"}},\n"

        return headers + ""

    def getHeaderNames(self, include=[], exclude=[]):

        headerNames = []

        if include:
            for k, v in self.fields.items():
                if k in include:
                    headerNames.append(k)
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    headerNames.append(k)

        return headerNames


    # Get the headers for returning the data output from HoT
    def getHeadersArray(self, index, include=[], exclude=[]):

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

    # Populate instance fields from a subMG response
    def setFieldsFromSubMG(self, assembly_sample_alias, assembly_sample_title, assembly_sample_name, assembly_sample_attributes):

        for k, v in self.fields.items():
            value = ''
            # do k lookup
            if k == 'sample_id':
                pass
            elif k == 'sample_title':
                value = assembly_sample_title
            elif k == 'sample_alias':
                value = assembly_sample_alias
            elif k == 'scientific_name':
                value = assembly_sample_name['SCIENTIFIC_NAME']
            elif k == 'tax_id':
                value = assembly_sample_name['TAXON_ID']
            else:
                try:
                    for overattribute in assembly_sample_attributes:
                        for attribute in overattribute:
                            if attribute != "SAMPLE_ATTRIBUTE":
                                for items in attribute:
                                    if items['TAG'] == k.replace('_', ' '):
                                        value = items['VALUE']
                                        break
                except:
                    pass

            setattr(self, k, value)

    # Get the headers for the HoT (including choices)
    def getValidators(self, include=[], exclude=[] ):

        validators = ""

        if include:
            for k, v in self.fields.items():
                if k in include:
                    try:
                        validator_body = getattr(self, f"{k}_validator")
                        validator = (f"{k}_validator", f"{validator_body}")
                        validators = validators + f"const {k}_validator = /{validator_body}/;\n"
                    except:
                        pass
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    try:
                        validator_body = getattr(self, f"{k}_validator")
                        validator = (f"{k}_validator", f"{validator_body}")
                        validators = validators + f"const {k}_validator = /{validator_body}/;\n"
                    except:
                        pass

        return validators

    def getHeadersCount(self, include=[], exclude=[]):

        count = 0

        if include:
            for k, v in self.fields.items():
                if k in include:
                    count = count + 1
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    count = count + 1

        return count        

    def getHeadersMaxSize(self, headers_max_size, include=[], exclude=[]):
            
        if include:
            for k, v in self.fields.items():
                if k in include:
                    if len(v) > headers_max_size:
                        headers_max_size = len(v)
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    if len(v) > headers_max_size:
                        headers_max_size = len(v)
        if self.name:
            if len(self.name) > headers_max_size:
                headers_max_size = len(self.name    )

        return headers_max_size

    def getHeadersSize(self, pixelsPerChar, include=[], exclude=[]):

        headersSize = []    

        if include:
            for k, v in self.fields.items():
                if k in include:
                    headersSize.append(len(k) * pixelsPerChar) 
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    headersSize.append(len(k) * pixelsPerChar)

        return headersSize



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
    submitted = models.BooleanField(default=False)

    def getSubMGYAML(self):

        yaml = []
        yaml.append(f"STUDY: \"{self.study_accession_id}\"")
        yaml.append(f"PROJECT_NAME: \"{self.title}\"")

        return yaml

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
    method = models.CharField(max_length=100, null=True, blank=True)
    buffer = models.CharField(max_length=100, null=True, blank=True)
    organism = models.CharField(max_length=100, null=True, blank=True)
    isolated_from = models.CharField(max_length=100, null=True, blank=True)
    isolation_method = models.CharField(max_length=100, choices=ISOLATION_METHOD_CHOICES, null=True, blank=True)
    platform = models.CharField(max_length=100, null=True, blank=True, default="OXFORD_NANOPORE")
    insert_size = models.CharField(max_length=100, null=True, blank=True, default="2")
    library_name = models.CharField(max_length=100, null=True, blank=True, default="PCRtest")
    library_source = models.CharField(max_length=100, null=True, blank=True, default="GENOMIC")
    library_selection = models.CharField(max_length=100, null=True, blank=True, default="PCR")
    library_strategy = models.CharField(max_length=100, null=True, blank=True, default="WGS")
    sequencing_instrument = models.CharField(max_length=100, null=True, blank=True, default="Illumina HiSeq 1500")

    submitted = models.BooleanField(default=False)

    def show_metadata(self):
        # if no samples at all
        sample_set = self.sampleset_set.filter(sample_type=SAMPLE_TYPE_NORMAL).first()
        if not sample_set:
            return True
    
        sample = self.sample_set.first()
        if not sample:
            return True
        # sample = Sample.objects.filter(order=self).first()

    def show_samples(self):
        # metadata exists
        sample_set = self.sampleset_set.filter(sample_type=SAMPLE_TYPE_NORMAL).first()
        if not sample_set:
            return False

        # Maybe this is not needed
        checklists = sample_set.checklists
        for checklist in checklists:
            checklist_class_name = Sampleset.checklist_structure[checklist]['checklist_class_name']
            checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
            try:
                checklist_item_instance = checklist_item_class.objects.filter(sampleset=sample_set, sample_type=SAMPLE_TYPE_NORMAL).first()
                return True
            except:
                pass

        return False

    def show_assembly(self):
        if not self.show_samples():
            return False
        
        assembly = self.assembly_set.first()
        if not assembly:
            return False

        return True

    def show_bin(self):
        if not self.show_samples():
            return False
        
        bin = self.bin_set.first()
        if not bin:
            return False

        return True

    def getSubMGSequencingPlatforms(self, platformList):
        
        if self.platform not in platformList:
            platformList.append(self.platform)

        return ', '.join(f'"{p}"' for p in platformList)
        return platformList

    def getSubMGYAML(self, platformList):

        yaml = []
        
        yaml.append(f"SEQUENCING_PLATFORMS: [{platformList}]")

        return yaml

class Sampleset(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    # list of checklists
    checklists = models.JSONField()
    include = models.JSONField()
    exclude = models.JSONField()
    custom = models.JSONField()
    sample_type = models.IntegerField(default=SAMPLE_TYPE_NORMAL)

    checklist_structure = {
        %CHECKLIST_STRUCTURE%
    }

class Sample(SelfDescribingModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    # from ENA spreadsheet download

    status = models.CharField(max_length=2, null=True, blank=True)
    sample_id = models.CharField(max_length=100, null=True, blank=True)
    tax_id = models.CharField(max_length=100, null=True, blank=True)
    scientific_name = models.CharField(max_length=100, null=True, blank=True)
    sample_alias = models.CharField(max_length=100, null=True, blank=True)
    sample_title = models.CharField(max_length=100, null=True, blank=True)
    sample_description = models.CharField(max_length=100, null=True, blank=True)
    sample_accession_number = models.CharField(max_length=100, null=True, blank=True)
    sample_biosample_number = models.CharField(max_length=100, null=True, blank=True)
    sample_type = models.IntegerField(default=SAMPLE_TYPE_NORMAL)
    submitted = models.BooleanField(default=False)
    assembly = models.ForeignKey('app.Assembly', on_delete=models.SET_NULL, blank=True, null=True)
    bin = models.ForeignKey('app.Bin', on_delete=models.SET_NULL, blank=True, null=True)
    mag_data = models.CharField(max_length=100, null=True, blank=True)



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
        'assembly': 'assembly_identifier',
        'bin': 'bin_identifier',
    }

    name = 'Sample'

    @property
    def getAttributes(self):
    	# go through each of the fields within eah of the checklists
        # get the checklists for this sample    
        
        output = ""
        sampleset = Sampleset.objects.filter(order=self.order).first()
        checklists = sampleset.checklists
 
        for checklist in json.loads(json.dumps(checklists)):
            checklist_name = checklist
            checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
            checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
            checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
            checklist_item_instance = checklist_item_class.objects.filter(sample = self, sampleset=sampleset).first()
            
            include = []
            exclude = []

            attributes = checklist_item_instance.getSubAttributes(exclude, include)

            attributes = attributes + f"<SAMPLE_ATTRIBUTE><TAG>ena-checklist</TAG><VALUE>{checklist_code}</VALUE></SAMPLE_ATTRIBUTE>\n"

            output = output + f'{attributes}\n'

        return output    

    # Get actual value for each field
    def getFields(self, include=[], exclude=[]):
        output = {}

        output['status'] = getattr(self, 'status') or ''
        # output['status'] = '. '

        if include:
            for k, v in self.fields.items():
                if k in include:
                    if k == 'assembly' or k == 'bin':
                        if getattr(self, k):
                            output[v] = str(getattr(self, k).id)
                        else:
                            output[v] = ''
                    else:
                        output[v] = getattr(self, k) or ''
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    if k == 'assembly' or k == 'bin':
                        if getattr(self, k):
                            output[v] = str(getattr(self, k).id)
                        else:
                            output[v] = ''                    
                    else:
                        output[v] = getattr(self, k) or ''

        return output            

    def getSubMGYAMLHeader():

        yaml = []
        
        yaml.append(f"NEW_SAMPLES:")
                    
        return yaml

    def getSubMGTaxId(self, tax_id):

        if self.tax_id not in tax_id and self.tax_id != '':
            tax_id.append(self.tax_id)

        return tax_id

    def getSubMGTaxIdYAML(self, tax_id):

        yaml = []

        yaml.append(f"METAGENOME_TAXID: \"{tax_id[0]}\"")

        return yaml

    def getSubMGScientificName(self, scientific_name):

        if self.scientific_name not in scientific_name and self.scientific_name != '':
            scientific_name.append(self.scientific_name)

        return scientific_name

    def getSubMGScientificNameYAML(self, scientific_name):

        yaml = []

        yaml.append(f"METAGENOME_SCIENTIFIC_NAME: \"{scientific_name[0]}\"")

        return yaml
    
    def getSubMGYAML(self, sample_type):

        indent = f"  "

        yaml = []
        yaml_sample = []
        yaml_additional = []

        # go through checklist
        # search for specific sample fields and append to sample
        # take everything else and append to additional
        # check for multiplicity, replace returns with |
                    
        sampleset = Sampleset.objects.filter(order=self.order, sample_type=sample_type).first()
        checklists = sampleset.checklists
 
        for checklist in json.loads(json.dumps(checklists)):
            checklist_name = checklist
            checklist_code = Sampleset.checklist_structure[checklist_name]['checklist_code']  
            checklist_class_name = Sampleset.checklist_structure[checklist_name]['checklist_class_name']
            checklist_item_class =  getattr(importlib.import_module("app.models"), checklist_class_name)
            checklist_item_instance = checklist_item_class.objects.filter(sample = self, sampleset=sampleset).first()
            
            include = ["collection_date", "geographic_location_country_and_or_sea"]
            exclude = []

            indent = f"  "

            yaml_sample.extend(checklist_item_instance.getSubAttributesYAML(indent, include, exclude))

            include = []
            exclude = ["collection_date", "geographic_location_country_and_or_sea", "metagenomic_source"]

            indent = f"    "

            yaml_additional.extend(checklist_item_instance.getSubAttributesYAML(indent, include, exclude))

            # attributes = attributes + f"<SAMPLE_ATTRIBUTE><TAG>ena-checklist</TAG><VALUE>{checklist_code}</VALUE></SAMPLE_ATTRIBUTE>\n"
            
        indent = f"  "    

        if sample_type == SAMPLE_TYPE_NORMAL:
            yaml.append(f"- TITLE: \"{self.sample_title}\"")
        if sample_type == SAMPLE_TYPE_NORMAL or sample_type == SAMPLE_TYPE_ASSEMBLY:
            yaml.extend(yaml_sample)
        yaml.append(f"{indent}ADDITIONAL_SAMPLESHEET_FIELDS:")
        yaml.extend(yaml_additional)

        return yaml

    # Populate instance fields from a response
    def setFieldsFromResponse(self, response):

        for k, v in self.fields.items():
            try:
                value = response[v]
            except:
                value = ''

            if k == 'assembly':
                if value != '':
                    assembly_class = getattr(importlib.import_module("app.models"), 'Assembly')
                    assembly_instance = assembly_class.objects.filter(id=value).first()
                    if assembly_instance:
                        self.assembly = assembly_instance
                    else:
                        self.assembly = None
            elif k == 'bin':
                if value != '':
                    bin_class = getattr(importlib.import_module("app.models"), 'Bin')
                    bin_instance = bin_class.objects.filter(id=value).first()
                    if bin_instance:
                        self.bin = bin_instance
                    else:
                        self.bin = None
            else:
                setattr(self, k, value)


    def getHeaderNames(self, include=[], exclude=[]):

        headerNames = []

        if include:
            for k, v in self.fields.items():
                if k in include:
                    headerNames.append(v)
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    headerNames.append(v)

        return headerNames


    # Get the headers for returning the data output from HoT
    def getHeadersArray(self, index, include=[], exclude=[]):

        output = ""
        if include:
                for k, v in self.fields.items():
                    if k in include:
                        output = output + f"{v}: row[{index}].trim(),\n"
                        index = index + 1
        else:
                for k, v in self.fields.items():
                    if k not in exclude:
                        output = output + f"{v}: row[{index}].trim(),\n"
                        index = index + 1

        return (index, output)    

    def getHeaders(self, include=[], exclude=[], extra_choices=[]):

        headers = ""

        if include:
            for k, v in self.fields.items():
                if k in include:
                    headers = headers + f"{{title: '{k}', data: '{k}'"
                    try:
                        choices = getattr(self, f"{k}_choice")
                        single_choice = [t[0] for t in choices]
                        if k == "sequence_quality_check":
                            strict = "true"
                        else:
                            strict = "true"
                        headers = headers + f", type: 'autocomplete', source: {single_choice}, strict: {strict}, allowInvalid: true"
                    except:
                        pass
                    if (k == 'assembly' or k == 'bin') and len(extra_choices) > 0:
						# ['Afghanistan', 'Albania']
                        single_choice = extra_choices
                        headers = headers + f", type: 'autocomplete', source: {single_choice}, strict: true, allowInvalid: true"
                    try:
                        validator = getattr(self, f"validator: {k}_validator")
                        headers = headers + f", validator: {k}_validator, allowInvalid: true"
                    except:
                        pass
                    headers = headers + f"}},\n"
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    headers = headers + f"{{title: '{k}', data: '{v}'"
                    try:
                        choices = getattr(self, f"{k}_choice")
                        single_choice = [t[0] for t in choices]
                        if k == "sequence_quality_check":
                            strict = "true"
                        else:
                            strict = "true"
                        headers = headers + f", type: 'autocomplete', source: {single_choice}, strict: {strict}, allowInvalid: true"
                    except:
                        pass
                    if (k == 'assembly' or k == 'bin') and  len(extra_choices) > 0:
						# ['Afghanistan', 'Albania']
                        single_choice = extra_choices
                        headers = headers + f", type: 'autocomplete', source: {single_choice}, strict: true, allowInvalid: true"
                    try:
                        validator = getattr(self, f"{k}_validator")
                        headers = headers + f", validator: {k}_validator, allowInvalid: true"
                    except:
                        pass
                    headers = headers + f"}},\n"

        return headers + ""

class ProjectSubmission(models.Model):
    projects = models.ManyToManyField(Project)
    project_object_xml = models.TextField(null=True, blank=True)
    submission_object_xml = models.TextField(null=True, blank=True)
    receipt_xml = models.TextField(null=True, blank=True)
    accession_status = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"Submission for Project" #  {self.project.id}

class Read(models.Model):
    sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
    file_1 = models.CharField(max_length=255, null=True, blank=True)
    file_2 = models.CharField(max_length=255, null=True, blank=True)
    uncompressed_file_1 = models.CharField(max_length=255, null=True, blank=True)
    uncompressed_file_2 = models.CharField(max_length=255, null=True, blank=True)    
    read_file_checksum_1 = models.CharField(max_length=255, null=True, blank=True)
    read_file_checksum_2 = models.CharField(max_length=255, null=True, blank=True)    
    experiment_accession_number = models.CharField(max_length=100, null=True, blank=True)
    run_accession_number = models.CharField(max_length=100, null=True, blank=True)
    submitted = models.BooleanField(default=False)

    def getSubMGYAMLHeader():

        yaml = []
        
        yaml.append(f"PAIRED_END_READS:")
                    
        return yaml


    def getSubMGYAML(self):

        indent = f"  "

        yaml = []
        yaml.append(f"- NAME: \"{self.sample.sample_title}\"")
        yaml.append(f"{indent}PLATFORM: \"{self.sample.order.platform}\"")
        yaml.append(f"{indent}LIBRARY_NAME: \"{self.sample.order.library_name}\"")
        yaml.append(f"{indent}SEQUENCING_INSTRUMENT: \"{self.sample.order.sequencing_instrument}\"")
        yaml.append(f"{indent}LIBRARY_SOURCE: \"{self.sample.order.library_source}\"")
        yaml.append(f"{indent}LIBRARY_SELECTION: \"{self.sample.order.library_selection}\"")
        yaml.append(f"{indent}LIBRARY_STRATEGY: \"{self.sample.order.library_strategy}\"")
        yaml.append(f"{indent}INSERT_SIZE: \"{self.sample.order.insert_size}\"")
        yaml.append(f"{indent}FASTQ1_FILE: \"{self.file_1}\"")
        yaml.append(f"{indent}FASTQ2_FILE: \"{self.file_2}\"")   
        yaml.append(f"{indent}RELATED_SAMPLE_TITLE: \"{self.sample.sample_title}\"")
        yaml.append(f"{indent}ADDITIONAL_MANIFEST_FIELDS:")

        return yaml






class SampleSubmission(models.Model):
    samples = models.ManyToManyField(Sample)
    sample_object_xml = models.TextField(null=True, blank=True)
    sampleSubmission_object_xml = models.TextField(null=True, blank=True)
    receipt_xml = models.TextField(null=True, blank=True)
    accession_status = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"SampleSubmission for Order " # {self.order.id}

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

class MagRun(models.Model):
    reads = models.ManyToManyField(Read)

    status = models.CharField(max_length=100, null=True, blank=True)
    samplesheet_content = models.CharField(max_length=100, null=True, blank=True)
    cluster_config = models.CharField(max_length=100, null=True, blank=True)

class MagRunInstance(models.Model):
    magRun = models.ForeignKey(MagRun, on_delete=models.CASCADE)

    uuid = models.CharField(max_length=100, null=True, blank=True)

    status = models.CharField(max_length=100, null=True, blank=True)
    run_folder = models.CharField(max_length=100, null=True, blank=True)

    # Output files

class Assembly(models.Model):
    read = models.ManyToManyField(Read)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    assembly_software = models.CharField(max_length=255, null=True, blank=True)
    file = models.CharField(max_length=255, null=True, blank=True)
    submitted = models.BooleanField(default=False)
    assembly_accession_number = models.CharField(max_length=100, null=True, blank=True)

    def getSubMGYAMLHeader():

        yaml = []
        
        yaml.append(f"ASSEMBLY:")
                    
        return yaml


    def getSubMGYAML(self):

        indent = f"  "

        yaml = []
        yaml.append(f"{indent}ASSEMBLY_NAME: \"{self.order.project.title}_coasm\"")
        yaml.append(f"{indent}ASSEMBLY_SOFTWARE: \"{self.assembly_software}\"")
        yaml.append(f"{indent}ISOLATION_SOURCE: \"UNKNOWN\"")
        yaml.append(f"{indent}FASTA_FILE: \"{self.file}\"")

        # Separate call to assembly sample
        
        return yaml

    def getSubMGYAMLFooter():

        indent = f"  "

        yaml = []
        
        yaml.append(f"{indent}ADDITIONAL_MANIFEST_FIELDS:")
                    
        return yaml
    
class Bin(models.Model):
    read = models.ManyToManyField(Read)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    bin_number = models.CharField(max_length=255, null=True, blank=True)
    completeness_software = models.CharField(max_length=255, null=True, blank=True)
    binning_software = models.CharField(max_length=255, null=True, blank=True)
    quality_file = models.CharField(max_length=255, null=True, blank=True)
    file = models.CharField(max_length=255, null=True, blank=True)
    submitted = models.BooleanField(default=False)
    bin_accession_number = models.CharField(max_length=100, null=True, blank=True)

    def getSubMGYAMLHeader():

        yaml = []
        
        yaml.append(f"BINS:")
                    
        return yaml


    def getSubMGYAML(self):

        indent = f"  "

        yaml = []
        yaml.append(f"{indent}BINS_DIRECTORY: \"{self.file.rsplit('/', 1)[0]}\"")
        yaml.append(f"{indent}COMPLETENESS_SOFTWARE: \"{self.completeness_software}\"")
        yaml.append(f"{indent}QUALITY_FILE: \"{self.quality_file}\"")
        yaml.append(f"{indent}BINNING_SOFTWARE: \"{self.binning_software}\"")
        yaml.append(f"{indent}ISOLATION_SOURCE: \"UNKNOWN\"")
        # yaml.append(f"{indent}FASTA_FILE: \"{self.file}\"")

        # Separate call to bin sample
        
        return yaml

    def getSubMGYAMLTaxIDYAML(self, tax_ids):

        indent = f"  "

        # tax_id_path = Path(self.file.split('/', 1)[0] + "/tax_ids.txt")
        tax_id_path = Path("/tmp/tax_ids.txt")

        with open(tax_id_path, 'w') as tax_id_file:
            print(f"Bin_id\tScientific_name\tTax_id", file=tax_id_file)
            for tax_id in tax_ids:
                print(f"{tax_id}\t{tax_ids[tax_id][0]}\t{tax_ids[tax_id][1]}", file=tax_id_file)

        yaml = []

        yaml.append(f"{indent}MANUAL_TAXONOMY_FILE: \"{tax_id_path}\"")
        # yaml.append(f"{indent}NCBI_TAXONOMY_FILES:")

        return yaml

    def getSubMGYAMLFooter():

        indent = f"  "

        yaml = []
        
        yaml.append(f"{indent}ADDITIONAL_MANIFEST_FIELDS:")
                    
        return yaml
    
class Mag(models.Model):

    def getSubMGYAMLHeader():

        yaml = []
        
        yaml.append(f"MAGS:")
                    
        return yaml    

    def getSubMGYAMLMagDataYAML(mag_data):

        indent = f"  "

        mag_data_path = "/tmp/mag_data.txt"

        with open(mag_data_path, 'w') as mag_data_file:
            print(mag_data, file=mag_data_file)

        yaml = []

        yaml.append(f"{indent}MAG_METADATA_FILE: \"{mag_data_path}\"")

        return yaml

    def getSubMGYAMLFooter():

        indent = f"  "

        yaml = []
        
        yaml.append(f"{indent}ADDITIONAL_MANIFEST_FIELDS:")
                    
        return yaml    

class Alignment(models.Model):

    read = models.ForeignKey(Read, on_delete=models.CASCADE)
    assembly = models.ForeignKey(Assembly, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    file = models.CharField(max_length=255, null=True, blank=True)
    submitted = models.BooleanField(default=False)

    def getSubMGYAMLHeader():

        yaml = []
        
        yaml.append(f"BAM_FILES:")
                    
        return yaml


    def getSubMGYAML(self):

        indent = f"  "

        yaml = []
        yaml.append(f"{indent}- \"{self.file}\"")

        # Separate call to assembly sample
        
        return yaml


class SubMGRun(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    projects = models.ManyToManyField(Project)
    samples = models.ManyToManyField(Sample)
    reads = models.ManyToManyField(Read)
    # assembly_samples = models.ManyToManyField(Sample)
    # bin_samples = models.ManyToManyField(Sample)
    # mag_samples = models.ManyToManyField(Sample)
    assemblys = models.ManyToManyField(Assembly)
    bins = models.ManyToManyField(Bin)
    # mags = models.ManyToManyField(Bin)

    type = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=100, null=True, blank=True)

    yaml = models.CharField(max_length=100, null=True, blank=True)

    # Accession stuff
    # Mark things as submitted files

class SubMGRunInstance(models.Model):
    subMGRun = models.ForeignKey(SubMGRun, on_delete=models.CASCADE)

    uuid = models.CharField(max_length=100, null=True, blank=True)

    status = models.CharField(max_length=100, null=True, blank=True)
    run_folder = models.CharField(max_length=100, null=True, blank=True)

    # Output files

