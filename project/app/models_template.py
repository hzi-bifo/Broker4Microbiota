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
    
    def setFieldsFromResponse(self, response, inclusions=None):

        for k, v in self.fields.items():
            # Skip fields not in inclusions if inclusions list is provided
            if inclusions and k not in inclusions:
                continue
                
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
    library = models.CharField(max_length=100, choices=LIBRARY_CHOICES, null=True, blank=True)
    platform = models.CharField(max_length=100, null=True, blank=True, default="OXFORD_NANOPORE")
    insert_size = models.CharField(max_length=100, null=True, blank=True, default="2")
    library_name = models.CharField(max_length=100, null=True, blank=True, default="PCRtest")
    library_source = models.CharField(max_length=100, null=True, blank=True, default="GENOMIC")
    library_selection = models.CharField(max_length=100, null=True, blank=True, default="PCR")
    library_strategy = models.CharField(max_length=100, null=True, blank=True, default="WGS")
    sequencing_instrument = models.CharField(max_length=100, null=True, blank=True, default="Illumina HiSeq 1500")

    submitted = models.BooleanField(default=False)
    checklist_changed = models.BooleanField(default=False)

    # Order status tracking
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ready_for_sequencing', 'Ready for Sequencing'),
        ('sequencing_in_progress', 'Sequencing in Progress'),
        ('sequencing_completed', 'Sequencing Completed'),
        ('data_processing', 'Data Processing'),
        ('data_delivered', 'Data Delivered'),
        ('completed', 'Completed'),
    ]
    
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Current status of the sequencing order"
    )
    
    status_updated_at = models.DateTimeField(auto_now=True)
    status_notes = models.TextField(
        blank=True,
        help_text="Additional notes about the current status"
    )

    def show_metadata(self):
        # Return False if metadata setup is still needed (i.e., when template shows "not order.show_metadata")
        # Return True if metadata setup is completed
        sample_set = self.sampleset_set.filter(sample_type=SAMPLE_TYPE_NORMAL).first()
        if not sample_set:
            return False  # No sampleset means metadata setup is still needed
        
        # Check if sampleset has checklists configured
        if not sample_set.checklists:
            return False  # No checklists configured means metadata setup is still needed
            
        return True  # Metadata setup is completed

    def is_order_created(self):
        # Always True for existing orders - this step is completed when order exists
        return True
    
    def is_waiting_for_facility(self):
        # Return True if order is in facility-managed states
        facility_states = ['ready_for_sequencing', 'sequencing_in_progress', 'sequencing_completed', 'data_processing', 'data_delivered']
        return self.status in facility_states

    def show_samples(self):
        # Check if actual sample data has been created (not just metadata configured)
        # This should return True only when samples have been added, not just when checklist is selected
        sample_set = self.sampleset_set.filter(sample_type=SAMPLE_TYPE_NORMAL).first()
        if not sample_set:
            return False
        
        # Check if metadata checklist is configured first
        if not sample_set.checklists:
            return False
            
        # Now check if actual Sample objects exist for this order
        actual_samples = self.sample_set.filter(sample_type=SAMPLE_TYPE_NORMAL)
        return actual_samples.exists()  # Returns True only if samples were actually created
    
    def get_selected_checklist(self):
        """Return the name of the selected metadata checklist in a human-readable format"""
        sample_set = self.sampleset_set.filter(sample_type=SAMPLE_TYPE_NORMAL).first()
        if not sample_set or not sample_set.checklists:
            return None
            
        try:
            import json
            checklists = json.loads(sample_set.checklists) if isinstance(sample_set.checklists, str) else sample_set.checklists
            if checklists and len(checklists) > 0:
                # Convert checklist key back to readable name
                checklist_key = checklists[0]
                # Convert underscore format back to readable name
                readable_name = checklist_key.replace('_', ' ')
                return readable_name
        except:
            pass
            
        return None
    
    def get_sample_count(self):
        """Return the number of samples added to this order"""
        return self.sample_set.filter(sample_type=SAMPLE_TYPE_NORMAL).count()


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

    
    def get_status_display_color(self):
        """Return appropriate CSS color class for current status"""
        status_colors = {
            'draft': 'is-light',
            'ready_for_sequencing': 'is-info',
            'sequencing_in_progress': 'is-warning',
            'sequencing_completed': 'is-primary',
            'data_processing': 'is-primary',
            'data_delivered': 'is-success',
            'completed': 'is-success',
        }
        return status_colors.get(self.status, 'is-light')
    
    def get_next_status(self):
        """Return the next logical status in the workflow"""
        status_progression = {
            'draft': 'ready_for_sequencing',
            'ready_for_sequencing': 'sequencing_in_progress',
            'sequencing_in_progress': 'sequencing_completed',
            'sequencing_completed': 'data_processing',
            'data_processing': 'data_delivered',
            'data_delivered': 'completed',
            'completed': None,
        }
        return status_progression.get(self.status)
    
    def can_advance_status(self):
        """Check if status can be advanced to next stage"""
        return self.get_next_status() is not None
    
    def get_status_history(self):
        """Return all status changes for this order"""
        return self.notes.filter(note_type='status_change').order_by('created_at')
    
    def get_notes(self, include_internal=False):
        """Return notes for this order, optionally including internal notes"""
        if include_internal:
            return self.notes.all()
        else:
            return self.notes.filter(
                note_type__in=['user_visible', 'status_change', 'rejection']
            )
    
    def add_status_note(self, user, new_status, content=""):
        """Helper method to add a status change note"""
        
        old_status = self.status
        self.status = new_status
        self.save()
        
        if not content:
            content = f"Status changed from {self.get_status_display()} to {dict(self.STATUS_CHOICES)[new_status]}"
        
        return StatusNote.objects.create(
            order=self,
            user=user,
            note_type='status_change',
            content=content,
            old_status=old_status,
            new_status=new_status
        )
    
    def reject_with_note(self, user, content, new_status='draft'):
        """Reject the order and add a user-visible note"""
        
        old_status = self.status
        self.status = new_status
        self.save()
        
        return StatusNote.objects.create(
            order=self,
            user=user,
            note_type='rejection',
            content=content,
            old_status=old_status,
            new_status=new_status,
            is_rejection=True
        )

class Sampleset(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE)

    # list of checklists
    checklists = models.JSONField()
    include = models.JSONField()
    exclude = models.JSONField()
    custom = models.JSONField()
    sample_type = models.IntegerField(default=SAMPLE_TYPE_NORMAL)
    
    # Field selection - stores which fields from the checklist are selected
    selected_fields = models.JSONField(default=dict, blank=True)
    # Field overrides - stores custom configurations like making optional fields required
    field_overrides = models.JSONField(default=dict, blank=True)
    
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
    def setFieldsFromResponse(self, response, inclusions=None):

        for k, v in self.fields.items():
            # Skip fields not in inclusions if inclusions list is provided
            if inclusions and k not in inclusions:
                continue
                
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

    def getSubMGYAMLTaxIDYAML(self):

        indent = f"  "

        # tax_id_path = Path(self.file.split('/', 1)[0] + "/tax_ids.txt")
        tax_id_path = Path("tax_ids.txt")

        yaml = []

        yaml.append(f"{indent}MANUAL_TAXONOMY_FILE: \"{tax_id_path}\"")
        # yaml.append(f"{indent}NCBI_TAXONOMY_FILES:")

        return yaml

    def getSubMGYAMLTaxIDContent(self, tax_ids):

        content = ""

        content += f"Bin_id\tScientific_name\tTax_id\n"
        for tax_id in tax_ids:
            content += f"{tax_id}\t{tax_ids[tax_id][0]}\t{tax_ids[tax_id][1]}"

        return content

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
    tax_ids = models.CharField(max_length=100, null=True, blank=True)

    # Accession stuff
    # Mark things as submitted files

class SubMGRunInstance(models.Model):
    subMGRun = models.ForeignKey(SubMGRun, on_delete=models.CASCADE)

    uuid = models.CharField(max_length=100, null=True, blank=True)

    status = models.CharField(max_length=100, null=True, blank=True)
    run_folder = models.CharField(max_length=100, null=True, blank=True)

    # Output files


class SiteSettings(models.Model):
    """
    Singleton model for storing site-wide branding and configuration settings.
    Only one instance of this model should exist.
    """
    # Basic Information
    site_name = models.CharField(
        max_length=200, 
        default="Sequencing Order Management",
        help_text="The name of your application"
    )
    organization_name = models.CharField(
        max_length=200, 
        default="Helmholtz Centre for Infection Research",
        help_text="Full name of your organization"
    )
    organization_short_name = models.CharField(
        max_length=50, 
        default="HZI",
        help_text="Short name or acronym"
    )
    tagline = models.CharField(
        max_length=500,
        default="Streamlining sequencing requests and ensuring compliance with MIxS standards",
        blank=True,
        help_text="A brief description or tagline for your site"
    )
    
    # Contact Information
    contact_email = models.EmailField(
        default="sequencing@helmholtz-hzi.de",
        help_text="Primary contact email address"
    )
    website_url = models.URLField(
        default="https://www.helmholtz-hzi.de",
        blank=True,
        help_text="Organization's main website URL"
    )
    
    # Branding
    logo = models.ImageField(
        upload_to='branding/',
        blank=True,
        null=True,
        help_text="Organization logo (recommended size: 200x50px)"
    )
    favicon = models.ImageField(
        upload_to='branding/',
        blank=True,
        null=True,
        help_text="Favicon for browser tab (recommended: 32x32px .ico or .png)"
    )
    
    # Appearance
    primary_color = models.CharField(
        max_length=7,
        default="#3273dc",
        help_text="Primary theme color in hex format (e.g., #3273dc)",
        validators=[RegexValidator(
            regex='^#[0-9a-fA-F]{6}$',
            message='Enter a valid hex color code (e.g., #3273dc)'
        )]
    )
    secondary_color = models.CharField(
        max_length=7,
        default="#2366d1",
        help_text="Secondary theme color in hex format",
        validators=[RegexValidator(
            regex='^#[0-9a-fA-F]{6}$',
            message='Enter a valid hex color code (e.g., #2366d1)'
        )]
    )
    
    # Footer
    footer_text = models.TextField(
        blank=True,
        help_text="Additional footer text (HTML allowed)",
        default=""
    )
    
    # Empty State Messages
    empty_projects_text = models.TextField(
        default="Welcome to the Sequencing Order Management System! Start by creating your first project to organize and track your sequencing requests.",
        help_text="Message shown when user has no projects",
        blank=True
    )
    projects_with_samples_text = models.TextField(
        default="You have active sequencing projects. Create a new project for a different study or continue working on your existing projects.",
        help_text="Message shown when user has projects with samples",
        blank=True
    )
    
    # Form Customization
    project_form_title = models.CharField(
        max_length=200,
        default="Create New Sequencing Project",
        help_text="Title shown on project creation form"
    )
    project_form_description = models.TextField(
        default="A project represents a study or experiment that groups related sequencing orders. Each project can contain multiple orders for different samples or time points.",
        help_text="Description shown on project creation form",
        blank=True
    )
    
    # Order Form Customization
    order_form_title = models.CharField(
        max_length=200,
        default="Create Sequencing Order",
        help_text="Title shown on order creation form"
    )
    order_form_description = models.TextField(
        default="Provide detailed information for your sequencing order including contact details, sample information, and sequencing preferences.",
        help_text="Description shown on order creation form",
        blank=True
    )
    
    # Submission Instructions
    submission_instructions = models.TextField(
        default="""<h4>Next Steps After Submission:</h4>
<ol>
<li><strong>Sample Preparation:</strong> Ensure your samples are properly labeled with the sample IDs you provided.</li>
<li><strong>Sample Shipping:</strong> Ship your samples to:
    <address>
    Sequencing Facility<br>
    Helmholtz Centre for Infection Research<br>
    Inhoffenstraße 7<br>
    38124 Braunschweig, Germany
    </address>
</li>
<li><strong>Include Documentation:</strong> Print and include your order confirmation with the samples.</li>
<li><strong>Tracking:</strong> You will receive email updates on the status of your sequencing order.</li>
</ol>
<p>For questions, contact: <a href="mailto:sequencing@helmholtz-hzi.de">sequencing@helmholtz-hzi.de</a></p>""",
        help_text="Instructions shown after order submission (HTML allowed)",
        blank=True
    )
    
    # Metadata Checklist Customization
    metadata_checklist_title = models.CharField(
        max_length=200,
        default="Configure Metadata Checklists",
        help_text="Title shown on metadata checklist selection page"
    )
    metadata_checklist_description = models.TextField(
        default="Select the appropriate MIxS (Minimum Information about any Sequence) standard for your samples. This determines what metadata fields you'll need to fill out.",
        help_text="Description shown on metadata checklist selection page",
        blank=True
    )
    
    # ENA (European Nucleotide Archive) Settings
    ena_username = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="ENA Webin account username (e.g., Webin-XXXXXX)"
    )
    ena_password = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="ENA account password (encrypted in database)"
    )
    ena_test_mode = models.BooleanField(
        default=True,
        help_text="Use ENA test server for submissions (recommended for testing)"
    )
    ena_center_name = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Center name for ENA submissions (optional)"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return f"{self.organization_name} Settings"

    def clean(self):
        """Validate ENA settings"""
        from django.core.exceptions import ValidationError
        
        # If ENA username is provided, validate format
        if self.ena_username:
            if not self.ena_username.startswith('Webin-'):
                raise ValidationError({
                    'ena_username': 'ENA username must start with "Webin-" (e.g., Webin-12345)'
                })
        
        # Warn if only username or password is set
        if self.ena_username and not self.ena_password:
            raise ValidationError({
                'ena_password': 'ENA password is required when username is set'
            })
        if self.ena_password and not self.ena_username:
            raise ValidationError({
                'ena_username': 'ENA username is required when password is set'
            })
    
    @property
    def ena_configured(self):
        """Check if ENA credentials are properly configured"""
        return bool(self.ena_username and self.ena_password)
    
    def set_ena_password(self, raw_password):
        """
        Encrypt and set the ENA password.
        Uses Fernet symmetric encryption for secure storage.
        """
        if not raw_password:
            self.ena_password = ""
            return
            
        from cryptography.fernet import Fernet
        from django.conf import settings
        
        # Get or generate encryption key
        key = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
        if not key:
            # Generate a key if not set (for development)
            # In production, this should be set in settings
            key = Fernet.generate_key()
        
        if isinstance(key, str):
            key = key.encode()
            
        f = Fernet(key)
        encrypted = f.encrypt(raw_password.encode())
        self.ena_password = encrypted.decode()
    
    def get_ena_password(self):
        """
        Decrypt and return the ENA password.
        Returns empty string if no password is set.
        """
        if not self.ena_password:
            return ""
            
        try:
            from cryptography.fernet import Fernet
            from django.conf import settings
            
            key = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
            if not key:
                return ""
                
            if isinstance(key, str):
                key = key.encode()
                
            f = Fernet(key)
            decrypted = f.decrypt(self.ena_password.encode())
            return decrypted.decode()
        except Exception:
            # If decryption fails, return empty string
            return ""

    def save(self, *args, **kwargs):
        """
        Save method that ensures only one instance exists.
        If a new instance is being created while one exists, update the existing one instead.
        """
        if not self.pk and SiteSettings.objects.exists():
            # If creating new instance but one already exists, 
            # update the existing one instead
            existing = SiteSettings.objects.first()
            self.pk = existing.pk
        
        super().save(*args, **kwargs)
        
        # Clear the cache when settings are saved
        from django.core.cache import cache
        cache.delete('site_settings')
    
    @classmethod
    def get_settings(cls):
        """
        Get the singleton instance of SiteSettings.
        Creates one with defaults if it doesn't exist.
        """
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


# Dynamic Form Models
class FormTemplate(models.Model):
    """
    Stores form templates that can be customized per facility or purpose.
    """
    FORM_TYPE_CHOICES = [
        ('project', 'Project Form'),
        ('order', 'Order Form'),
        ('sample', 'Sample Form'),
        ('custom', 'Custom Form'),
    ]
    
    name = models.CharField(
        max_length=200,
        help_text="Name of the form template"
    )
    form_type = models.CharField(
        max_length=20,
        choices=FORM_TYPE_CHOICES,
        help_text="Type of form this template represents"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of when to use this form template"
    )
    version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Version of this form template"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this form template is currently active"
    )
    facility_specific = models.BooleanField(
        default=False,
        help_text="Whether this form is specific to a facility"
    )
    facility_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Name of the facility this form is for (if facility_specific)"
    )
    json_schema = models.JSONField(
        default=dict,
        help_text="JSON schema defining the form structure"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_form_templates'
    )
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = ['name', 'version', 'facility_name']
    
    def __str__(self):
        return f"{self.name} v{self.version}"
    
    def get_form_definition(self):
        """
        Returns the form definition from the JSON schema.
        """
        return self.json_schema
    
    def clone(self, new_name=None, new_version=None):
        """
        Creates a clone of this form template.
        """
        clone = FormTemplate(
            name=new_name or f"{self.name} (Copy)",
            form_type=self.form_type,
            description=self.description,
            version=new_version or "1.0",
            is_active=False,  # Clones start as inactive
            facility_specific=self.facility_specific,
            facility_name=self.facility_name,
            json_schema=self.json_schema,
            created_by=None  # Will be set by the user cloning
        )
        return clone


class FormSubmission(models.Model):
    """
    Stores submitted form data from dynamic forms.
    """
    form_template = models.ForeignKey(
        FormTemplate,
        on_delete=models.PROTECT,
        help_text="The form template used for this submission"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        help_text="User who submitted the form"
    )
    submission_data = models.JSONField(
        help_text="The submitted form data"
    )
    # Optional relationships to existing models
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Related project (if applicable)"
    )
    order = models.ForeignKey(
        'Order',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Related order (if applicable)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.form_template.name} - {self.user.username} - {self.created_at}"


class StatusNote(models.Model):
    """
    Model to track order status changes and notes (internal and user-visible)
    """
    NOTE_TYPE_CHOICES = [
        ('internal', 'Internal Note'),
        ('user_visible', 'User Visible Note'),
        ('status_change', 'Status Change'),
        ('rejection', 'Rejection Note'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who created this note"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    note_type = models.CharField(
        max_length=20,
        choices=NOTE_TYPE_CHOICES,
        default='internal'
    )
    content = models.TextField(
        help_text="Note content or status change description"
    )
    old_status = models.CharField(
        max_length=30,
        blank=True,
        help_text="Previous status (for status changes)"
    )
    new_status = models.CharField(
        max_length=30,
        blank=True,
        help_text="New status (for status changes)"
    )
    is_rejection = models.BooleanField(
        default=False,
        help_text="Whether this note represents a rejection"
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_note_type_display()} for Order #{self.order.id} by {self.user.username if self.user else 'System'}"
    
    def is_visible_to_user(self):
        """Check if this note should be visible to the order owner"""
        return self.note_type in ['user_visible', 'status_change', 'rejection']

