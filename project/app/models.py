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
        'GSC_MIxS_wastewater_sludge': {"checklist_code": "ERC000023", 'checklist_class_name': 'GSC_MIxS_wastewater_sludge', 'unitchecklist_class_name': 'GSC_MIxS_wastewater_sludge_unit'},
'GSC_MIxS_miscellaneous_natural_or_artificial_environment': {"checklist_code": "ERC000025", 'checklist_class_name': 'GSC_MIxS_miscellaneous_natural_or_artificial_environment', 'unitchecklist_class_name': 'GSC_MIxS_miscellaneous_natural_or_artificial_environment_unit'},
'GSC_MIxS_human_skin': {"checklist_code": "ERC000017", 'checklist_class_name': 'GSC_MIxS_human_skin', 'unitchecklist_class_name': 'GSC_MIxS_human_skin_unit'},
'ENA_default_sample_checklist': {"checklist_code": "ERC000011", 'checklist_class_name': 'ENA_default_sample_checklist', 'unitchecklist_class_name': 'ENA_default_sample_checklist_unit'},
'GSC_MIxS_plant_associated': {"checklist_code": "ERC000020", 'checklist_class_name': 'GSC_MIxS_plant_associated', 'unitchecklist_class_name': 'GSC_MIxS_plant_associated_unit'},
'GSC_MIxS_water': {"checklist_code": "ERC000024", 'checklist_class_name': 'GSC_MIxS_water', 'unitchecklist_class_name': 'GSC_MIxS_water_unit'},
'GSC_MIxS_soil': {"checklist_code": "ERC000022", 'checklist_class_name': 'GSC_MIxS_soil', 'unitchecklist_class_name': 'GSC_MIxS_soil_unit'},
'GSC_MIxS_human_gut': {"checklist_code": "ERC000015", 'checklist_class_name': 'GSC_MIxS_human_gut', 'unitchecklist_class_name': 'GSC_MIxS_human_gut_unit'},
'GSC_MIxS_host_associated': {"checklist_code": "ERC000013", 'checklist_class_name': 'GSC_MIxS_host_associated', 'unitchecklist_class_name': 'GSC_MIxS_host_associated_unit'},
'GSC_MIxS_human_vaginal': {"checklist_code": "ERC000018", 'checklist_class_name': 'GSC_MIxS_human_vaginal', 'unitchecklist_class_name': 'GSC_MIxS_human_vaginal_unit'},
'GSC_MIxS_human_oral': {"checklist_code": "ERC000016", 'checklist_class_name': 'GSC_MIxS_human_oral', 'unitchecklist_class_name': 'GSC_MIxS_human_oral_unit'},
'ENA_binned_metagenome': {"checklist_code": "ERC000050", 'checklist_class_name': 'ENA_binned_metagenome', 'unitchecklist_class_name': 'ENA_binned_metagenome_unit'},
'GSC_MIxS_sediment': {"checklist_code": "ERC000021", 'checklist_class_name': 'GSC_MIxS_sediment', 'unitchecklist_class_name': 'GSC_MIxS_sediment_unit'},
'GSC_MIxS_human_associated': {"checklist_code": "ERC000014", 'checklist_class_name': 'GSC_MIxS_human_associated', 'unitchecklist_class_name': 'GSC_MIxS_human_associated_unit'},
'GSC_MIxS_air': {"checklist_code": "ERC000012", 'checklist_class_name': 'GSC_MIxS_air', 'unitchecklist_class_name': 'GSC_MIxS_air_unit'},
'GSC_MIxS_microbial_mat_biolfilm': {"checklist_code": "ERC000019", 'checklist_class_name': 'GSC_MIxS_microbial_mat_biolfilm', 'unitchecklist_class_name': 'GSC_MIxS_microbial_mat_biolfilm_unit'},
'GSC_MIMAGS': {"checklist_code": "ERC000047", 'checklist_class_name': 'GSC_MIMAGS', 'unitchecklist_class_name': 'GSC_MIMAGS_unit'},

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
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"
    
    def __str__(self):
        return f"{self.organization_name} Settings"
    
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

class GSC_MIxS_wastewater_sludge(SelfDescribingModel):

	sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	number_of_replicons_validator = "[+-]?[0-9]+"
	extrachromosomal_elements_validator = "[+-]?[0-9]+"
	estimated_size_validator = "[+-]?[0-9]+"
	sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	library_size_validator = "[+-]?[0-9]+"
	library_reads_sequenced_validator = "[+-]?[0-9]+"
	collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(\/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	depth_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	biochemical_oxygen_demand_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	chemical_oxygen_demand_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	sludge_retention_time_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	alkalinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	industrial_effluent_percent_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	pH_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	efficiency_percent_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	emulsions_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	gaseous_substances_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	inorganic_particles_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	organic_particles_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	soluble_inorganic_material_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	soluble_organic_material_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	suspended_solids_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	total_phosphate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	nitrate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	phosphate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	sodium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	total_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	project_name= models.CharField(max_length=120, blank=False,help_text="Name of th")
	experimental_factor= models.CharField(max_length=120, blank=True,help_text="Experiment")
	ploidy= models.CharField(max_length=120, blank=True,help_text="The ploidy")
	number_of_replicons= models.CharField(max_length=120, blank=True,help_text="Reports th", validators=[RegexValidator(number_of_replicons_validator)])
	extrachromosomal_elements= models.CharField(max_length=120, blank=True,help_text="Do plasmid", validators=[RegexValidator(extrachromosomal_elements_validator)])
	estimated_size= models.CharField(max_length=120, blank=True,help_text="The estima", validators=[RegexValidator(estimated_size_validator)])
	reference_for_biomaterial= models.CharField(max_length=120, blank=True,help_text="Primary pu")
	annotation_source= models.CharField(max_length=120, blank=True,help_text="For cases ")
	sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=120, blank=True,help_text="Volume (ml", validators=[RegexValidator(sample_volume_or_weight_for_DNA_extraction_validator)])
	nucleic_acid_extraction= models.CharField(max_length=120, blank=True,help_text="A link to ")
	nucleic_acid_amplification= models.CharField(max_length=120, blank=True,help_text="A link to ")
	library_size= models.CharField(max_length=120, blank=True,help_text="Total numb", validators=[RegexValidator(library_size_validator)])
	library_reads_sequenced= models.CharField(max_length=120, blank=True,help_text="Total numb", validators=[RegexValidator(library_reads_sequenced_validator)])
	library_construction_method= models.CharField(max_length=120, blank=True,help_text="Library co")
	library_vector= models.CharField(max_length=120, blank=True,help_text="Cloning ve")
	library_screening_strategy= models.CharField(max_length=120, blank=True,help_text="Specific e")
	target_gene= models.CharField(max_length=120, blank=True,help_text="Targeted g")
	target_subfragment= models.CharField(max_length=120, blank=True,help_text="Name of su")
	pcr_primers= models.CharField(max_length=120, blank=True,help_text="PCR primer")
	multiplex_identifiers= models.CharField(max_length=120, blank=True,help_text="Molecular ")
	adapters= models.CharField(max_length=120, blank=True,help_text="Adapters p")
	pcr_conditions= models.CharField(max_length=120, blank=True,help_text="Descriptio")
	sequencing_method= models.CharField(max_length=120, blank=True,help_text="Sequencing")
	sequence_quality_check= models.CharField(max_length=120, blank=True,help_text="Indicate i", choices=sequence_quality_check_choice)
	chimera_check_software= models.CharField(max_length=120, blank=True,help_text="Tool(s) us")
	relevant_electronic_resources= models.CharField(max_length=120, blank=True,help_text="A related ")
	relevant_standard_operating_procedures= models.CharField(max_length=120, blank=True,help_text="Standard o")
	negative_control_type= models.CharField(max_length=120, blank=True,help_text="The substa")
	positive_control_type= models.CharField(max_length=120, blank=True,help_text="The substa")
	collection_date= models.CharField(max_length=120, blank=False,help_text="The date t", validators=[RegexValidator(collection_date_validator)])
	geographic_location_country_and_or_sea= models.CharField(max_length=120, blank=False,help_text="The locati", choices=geographic_location_country_and_or_sea_choice)
	geographic_location_latitude= models.CharField(max_length=120, blank=False,help_text="The geogra", validators=[RegexValidator(geographic_location_latitude_validator)])
	geographic_location_longitude= models.CharField(max_length=120, blank=False,help_text="The geogra", validators=[RegexValidator(geographic_location_longitude_validator)])
	geographic_location_region_and_locality= models.CharField(max_length=120, blank=True,help_text="The geogra")
	depth= models.CharField(max_length=120, blank=True,help_text="The vertic", validators=[RegexValidator(depth_validator)])
	broad_scale_environmental_context= models.CharField(max_length=120, blank=False,help_text="Report the")
	local_environmental_context= models.CharField(max_length=120, blank=False,help_text="Report the")
	environmental_medium= models.CharField(max_length=120, blank=False,help_text="Report the")
	source_material_identifiers= models.CharField(max_length=120, blank=True,help_text="A unique i")
	sample_material_processing= models.CharField(max_length=120, blank=True,help_text="A brief de")
	isolation_and_growth_condition= models.CharField(max_length=120, blank=True,help_text="Publicatio")
	propagation= models.CharField(max_length=120, blank=True,help_text="The type o")
	amount_or_size_of_sample_collected= models.CharField(max_length=120, blank=True,help_text="The total ", validators=[RegexValidator(amount_or_size_of_sample_collected_validator)])
	oxygenation_status_of_sample= models.CharField(max_length=120, blank=True,help_text="oxygenatio", choices=oxygenation_status_of_sample_choice)
	organism_count= models.CharField(max_length=120, blank=True,help_text="Total cell")
	sample_storage_duration= models.CharField(max_length=120, blank=True,help_text="duration f", validators=[RegexValidator(sample_storage_duration_validator)])
	sample_storage_temperature= models.CharField(max_length=120, blank=True,help_text="temperatur", validators=[RegexValidator(sample_storage_temperature_validator)])
	sample_storage_location= models.CharField(max_length=120, blank=True,help_text="location a")
	sample_collection_device= models.CharField(max_length=120, blank=True,help_text="The device")
	sample_collection_method= models.CharField(max_length=120, blank=True,help_text="The method")
	biochemical_oxygen_demand= models.CharField(max_length=120, blank=True,help_text="a measure ", validators=[RegexValidator(biochemical_oxygen_demand_validator)])
	chemical_oxygen_demand= models.CharField(max_length=120, blank=True,help_text="a measure ", validators=[RegexValidator(chemical_oxygen_demand_validator)])
	pre_treatment= models.CharField(max_length=120, blank=True,help_text="the proces")
	primary_treatment= models.CharField(max_length=120, blank=True,help_text="the proces")
	reactor_type= models.CharField(max_length=120, blank=True,help_text="anaerobic ")
	secondary_treatment= models.CharField(max_length=120, blank=True,help_text="the proces")
	sludge_retention_time= models.CharField(max_length=120, blank=True,help_text="the time a", validators=[RegexValidator(sludge_retention_time_validator)])
	tertiary_treatment= models.CharField(max_length=120, blank=True,help_text="the proces")
	host_disease_status= models.CharField(max_length=120, blank=True,help_text="list of di")
	host_scientific_name= models.CharField(max_length=120, blank=True,help_text="Scientific")
	alkalinity= models.CharField(max_length=120, blank=True,help_text="alkalinity", validators=[RegexValidator(alkalinity_validator)])
	industrial_effluent_percent= models.CharField(max_length=120, blank=True,help_text="percentage", validators=[RegexValidator(industrial_effluent_percent_validator)])
	sewage_type= models.CharField(max_length=120, blank=True,help_text="Type of se")
	wastewater_type= models.CharField(max_length=120, blank=True,help_text="the origin")
	temperature= models.CharField(max_length=120, blank=True,help_text="temperatur", validators=[RegexValidator(temperature_validator)])
	pH= models.CharField(max_length=120, blank=True,help_text="pH measure", validators=[RegexValidator(pH_validator)])
	efficiency_percent= models.CharField(max_length=120, blank=True,help_text="percentage", validators=[RegexValidator(efficiency_percent_validator)])
	emulsions= models.CharField(max_length=120, blank=True,help_text="amount or ", validators=[RegexValidator(emulsions_validator)])
	gaseous_substances= models.CharField(max_length=120, blank=True,help_text="amount or ", validators=[RegexValidator(gaseous_substances_validator)])
	inorganic_particles= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(inorganic_particles_validator)])
	organic_particles= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(organic_particles_validator)])
	soluble_inorganic_material= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(soluble_inorganic_material_validator)])
	soluble_organic_material= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(soluble_organic_material_validator)])
	suspended_solids= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(suspended_solids_validator)])
	total_phosphate= models.CharField(max_length=120, blank=True,help_text="total amou", validators=[RegexValidator(total_phosphate_validator)])
	nitrate= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(nitrate_validator)])
	phosphate= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(phosphate_validator)])
	salinity= models.CharField(max_length=120, blank=True,help_text="The total ", validators=[RegexValidator(salinity_validator)])
	sodium= models.CharField(max_length=120, blank=True,help_text="sodium con", validators=[RegexValidator(sodium_validator)])
	total_nitrogen= models.CharField(max_length=120, blank=True,help_text="total nitr", validators=[RegexValidator(total_nitrogen_validator)])
	subspecific_genetic_lineage= models.CharField(max_length=120, blank=True,help_text="Informatio")
	trophic_level= models.CharField(max_length=120, blank=True,help_text="Trophic le", choices=trophic_level_choice)
	relationship_to_oxygen= models.CharField(max_length=120, blank=True,help_text="Is this or", choices=relationship_to_oxygen_choice)
	known_pathogenicity= models.CharField(max_length=120, blank=True,help_text="To what is")
	encoded_traits= models.CharField(max_length=120, blank=True,help_text="Should inc")
	observed_biotic_relationship= models.CharField(max_length=120, blank=True,help_text="Is it free", choices=observed_biotic_relationship_choice)
	chemical_administration= models.CharField(max_length=120, blank=True,help_text="list of ch")
	perturbation= models.CharField(max_length=120, blank=True,help_text="type of pe")

	fields = {
		'project_name': 'project name',
		'experimental_factor': 'experimental factor',
		'ploidy': 'ploidy',
		'number_of_replicons': 'number of replicons',
		'extrachromosomal_elements': 'extrachromosomal elements',
		'estimated_size': 'estimated size',
		'reference_for_biomaterial': 'reference for biomaterial',
		'annotation_source': 'annotation source',
		'sample_volume_or_weight_for_DNA_extraction': 'sample volume or weight for DNA extraction',
		'nucleic_acid_extraction': 'nucleic acid extraction',
		'nucleic_acid_amplification': 'nucleic acid amplification',
		'library_size': 'library size',
		'library_reads_sequenced': 'library reads sequenced',
		'library_construction_method': 'library construction method',
		'library_vector': 'library vector',
		'library_screening_strategy': 'library screening strategy',
		'target_gene': 'target gene',
		'target_subfragment': 'target subfragment',
		'pcr_primers': 'pcr primers',
		'multiplex_identifiers': 'multiplex identifiers',
		'adapters': 'adapters',
		'pcr_conditions': 'pcr conditions',
		'sequencing_method': 'sequencing method',
		'sequence_quality_check': 'sequence quality check',
		'chimera_check_software': 'chimera check software',
		'relevant_electronic_resources': 'relevant electronic resources',
		'relevant_standard_operating_procedures': 'relevant standard operating procedures',
		'negative_control_type': 'negative control type',
		'positive_control_type': 'positive control type',
		'collection_date': 'collection date',
		'geographic_location_country_and_or_sea': 'geographic location (country and/or sea)',
		'geographic_location_latitude': 'geographic location (latitude)',
		'geographic_location_longitude': 'geographic location (longitude)',
		'geographic_location_region_and_locality': 'geographic location (region and locality)',
		'depth': 'depth',
		'broad_scale_environmental_context': 'broad-scale environmental context',
		'local_environmental_context': 'local environmental context',
		'environmental_medium': 'environmental medium',
		'source_material_identifiers': 'source material identifiers',
		'sample_material_processing': 'sample material processing',
		'isolation_and_growth_condition': 'isolation and growth condition',
		'propagation': 'propagation',
		'amount_or_size_of_sample_collected': 'amount or size of sample collected',
		'oxygenation_status_of_sample': 'oxygenation status of sample',
		'organism_count': 'organism count',
		'sample_storage_duration': 'sample storage duration',
		'sample_storage_temperature': 'sample storage temperature',
		'sample_storage_location': 'sample storage location',
		'sample_collection_device': 'sample collection device',
		'sample_collection_method': 'sample collection method',
		'biochemical_oxygen_demand': 'biochemical oxygen demand',
		'chemical_oxygen_demand': 'chemical oxygen demand',
		'pre_treatment': 'pre-treatment',
		'primary_treatment': 'primary treatment',
		'reactor_type': 'reactor type',
		'secondary_treatment': 'secondary treatment',
		'sludge_retention_time': 'sludge retention time',
		'tertiary_treatment': 'tertiary treatment',
		'host_disease_status': 'host disease status',
		'host_scientific_name': 'host scientific name',
		'alkalinity': 'alkalinity',
		'industrial_effluent_percent': 'industrial effluent percent',
		'sewage_type': 'sewage type',
		'wastewater_type': 'wastewater type',
		'temperature': 'temperature',
		'pH': 'pH',
		'efficiency_percent': 'efficiency percent',
		'emulsions': 'emulsions',
		'gaseous_substances': 'gaseous substances',
		'inorganic_particles': 'inorganic particles',
		'organic_particles': 'organic particles',
		'soluble_inorganic_material': 'soluble inorganic material',
		'soluble_organic_material': 'soluble organic material',
		'suspended_solids': 'suspended solids',
		'total_phosphate': 'total phosphate',
		'nitrate': 'nitrate',
		'phosphate': 'phosphate',
		'salinity': 'salinity',
		'sodium': 'sodium',
		'total_nitrogen': 'total nitrogen',
		'subspecific_genetic_lineage': 'subspecific genetic lineage',
		'trophic_level': 'trophic level',
		'relationship_to_oxygen': 'relationship to oxygen',
		'known_pathogenicity': 'known pathogenicity',
		'encoded_traits': 'encoded traits',
		'observed_biotic_relationship': 'observed biotic relationship',
		'chemical_administration': 'chemical administration',
		'perturbation': 'perturbation',
	}

	name = 'GSC_MIxS_wastewater_sludge'

class GSC_MIxS_wastewater_sludge_unit(SelfDescribingModel):

	sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	geographic_location_latitude_units = [('DD', 'DD')]
	geographic_location_longitude_units = [('DD', 'DD')]
	depth_units = [('m', 'm')]
	amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	sample_storage_temperature_units = [('°C', '°C')]
	biochemical_oxygen_demand_units = [('mg/L (over 5 days at 20C)', 'mg/L (over 5 days at 20C)')]
	chemical_oxygen_demand_units = [('mg/L (over 5 days at 20C)', 'mg/L (over 5 days at 20C)')]
	sludge_retention_time_units = [('days', 'days'), ('hours', 'hours'), ('minutes', 'minutes'), ('weeks', 'weeks')]
	alkalinity_units = [('mEq/L', 'mEq/L')]
	industrial_effluent_percent_units = [('%', '%')]
	temperature_units = [('ºC', 'ºC')]
	efficiency_percent_units = [('%', '%')]
	emulsions_units = [('g/L', 'g/L'), ('ng/L', 'ng/L'), ('µg/L', 'µg/L')]
	gaseous_substances_units = [('µmol/L', 'µmol/L')]
	inorganic_particles_units = [('mg/L', 'mg/L'), ('mol/L', 'mol/L')]
	organic_particles_units = [('g/L', 'g/L')]
	soluble_inorganic_material_units = [('g/L', 'g/L'), ('mol/L', 'mol/L'), ('parts/million', 'parts/million')]
	soluble_organic_material_units = [('g/L', 'g/L'), ('mol/L', 'mol/L'), ('parts/million', 'parts/million')]
	suspended_solids_units = [('g/L', 'g/L'), ('mol/L', 'mol/L'), ('parts/million', 'parts/million')]
	total_phosphate_units = [('µg/L', 'µg/L'), ('µmol/L', 'µmol/L')]
	nitrate_units = [('µmol/L', 'µmol/L')]
	phosphate_units = [('µmol/L', 'µmol/L')]
	salinity_units = [('psu', 'psu')]
	sodium_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	total_nitrogen_units = [('µg/L', 'µg/L'), ('µmol/L', 'µmol/L')]

	fields = {
		'sample_volume_or_weight_for_DNA_extraction': 'sample volume or weight for DNA extraction',
		'geographic_location_latitude': 'geographic location (latitude)',
		'geographic_location_longitude': 'geographic location (longitude)',
		'depth': 'depth',
		'amount_or_size_of_sample_collected': 'amount or size of sample collected',
		'sample_storage_duration': 'sample storage duration',
		'sample_storage_temperature': 'sample storage temperature',
		'biochemical_oxygen_demand': 'biochemical oxygen demand',
		'chemical_oxygen_demand': 'chemical oxygen demand',
		'sludge_retention_time': 'sludge retention time',
		'alkalinity': 'alkalinity',
		'industrial_effluent_percent': 'industrial effluent percent',
		'temperature': 'temperature',
		'efficiency_percent': 'efficiency percent',
		'emulsions': 'emulsions',
		'gaseous_substances': 'gaseous substances',
		'inorganic_particles': 'inorganic particles',
		'organic_particles': 'organic particles',
		'soluble_inorganic_material': 'soluble inorganic material',
		'soluble_organic_material': 'soluble organic material',
		'suspended_solids': 'suspended solids',
		'total_phosphate': 'total phosphate',
		'nitrate': 'nitrate',
		'phosphate': 'phosphate',
		'salinity': 'salinity',
		'sodium': 'sodium',
		'total_nitrogen': 'total nitrogen',
	}

	name = 'GSC_MIxS_wastewater_sludge'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=120, choices=sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	geographic_location_latitude = models.CharField(max_length=120, choices=geographic_location_latitude_units, blank=False)
	geographic_location_longitude = models.CharField(max_length=120, choices=geographic_location_longitude_units, blank=False)
	depth = models.CharField(max_length=120, choices=depth_units, blank=False)
	amount_or_size_of_sample_collected = models.CharField(max_length=120, choices=amount_or_size_of_sample_collected_units, blank=False)
	sample_storage_duration = models.CharField(max_length=120, choices=sample_storage_duration_units, blank=False)
	sample_storage_temperature = models.CharField(max_length=120, choices=sample_storage_temperature_units, blank=False)
	biochemical_oxygen_demand = models.CharField(max_length=120, choices=biochemical_oxygen_demand_units, blank=False)
	chemical_oxygen_demand = models.CharField(max_length=120, choices=chemical_oxygen_demand_units, blank=False)
	sludge_retention_time = models.CharField(max_length=120, choices=sludge_retention_time_units, blank=False)
	alkalinity = models.CharField(max_length=120, choices=alkalinity_units, blank=False)
	industrial_effluent_percent = models.CharField(max_length=120, choices=industrial_effluent_percent_units, blank=False)
	temperature = models.CharField(max_length=120, choices=temperature_units, blank=False)
	efficiency_percent = models.CharField(max_length=120, choices=efficiency_percent_units, blank=False)
	emulsions = models.CharField(max_length=120, choices=emulsions_units, blank=False)
	gaseous_substances = models.CharField(max_length=120, choices=gaseous_substances_units, blank=False)
	inorganic_particles = models.CharField(max_length=120, choices=inorganic_particles_units, blank=False)
	organic_particles = models.CharField(max_length=120, choices=organic_particles_units, blank=False)
	soluble_inorganic_material = models.CharField(max_length=120, choices=soluble_inorganic_material_units, blank=False)
	soluble_organic_material = models.CharField(max_length=120, choices=soluble_organic_material_units, blank=False)
	suspended_solids = models.CharField(max_length=120, choices=suspended_solids_units, blank=False)
	total_phosphate = models.CharField(max_length=120, choices=total_phosphate_units, blank=False)
	nitrate = models.CharField(max_length=120, choices=nitrate_units, blank=False)
	phosphate = models.CharField(max_length=120, choices=phosphate_units, blank=False)
	salinity = models.CharField(max_length=120, choices=salinity_units, blank=False)
	sodium = models.CharField(max_length=120, choices=sodium_units, blank=False)
	total_nitrogen = models.CharField(max_length=120, choices=total_nitrogen_units, blank=False)

class GSC_MIxS_miscellaneous_natural_or_artificial_environment(SelfDescribingModel):


	altitude_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	elevation_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	density_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	water_current_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	pressure_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	ammonium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	bromide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	calcium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	chloride_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	chlorophyll_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	diether_lipids_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	dissolved_carbon_dioxide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	dissolved_hydrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	dissolved_inorganic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	dissolved_organic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	dissolved_oxygen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	nitrite_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	organic_matter_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	organic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	phospholipid_fatty_acid_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	potassium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	silicate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	sulfate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	sulfide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	altitude= models.CharField(max_length=120, blank=True,help_text="The altitu", validators=[RegexValidator(altitude_validator)])
	elevation= models.CharField(max_length=120, blank=True,help_text="The elevat", validators=[RegexValidator(elevation_validator)])
	biomass= models.CharField(max_length=120, blank=True,help_text="amount of ")
	density= models.CharField(max_length=120, blank=True,help_text="density of", validators=[RegexValidator(density_validator)])
	water_current= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(water_current_validator)])
	pressure= models.CharField(max_length=120, blank=True,help_text="pressure t", validators=[RegexValidator(pressure_validator)])
	ammonium= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(ammonium_validator)])
	bromide= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(bromide_validator)])
	calcium= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(calcium_validator)])
	chloride= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(chloride_validator)])
	chlorophyll= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(chlorophyll_validator)])
	diether_lipids= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(diether_lipids_validator)])
	dissolved_carbon_dioxide= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(dissolved_carbon_dioxide_validator)])
	dissolved_hydrogen= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(dissolved_hydrogen_validator)])
	dissolved_inorganic_carbon= models.CharField(max_length=120, blank=True,help_text="dissolved ", validators=[RegexValidator(dissolved_inorganic_carbon_validator)])
	dissolved_organic_nitrogen= models.CharField(max_length=120, blank=True,help_text="dissolved ", validators=[RegexValidator(dissolved_organic_nitrogen_validator)])
	dissolved_oxygen= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(dissolved_oxygen_validator)])
	nitrite= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(nitrite_validator)])
	nitrogen= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(nitrogen_validator)])
	organic_carbon= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(organic_carbon_validator)])
	organic_matter= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(organic_matter_validator)])
	organic_nitrogen= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(organic_nitrogen_validator)])
	phospholipid_fatty_acid= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(phospholipid_fatty_acid_validator)])
	potassium= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(potassium_validator)])
	silicate= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(silicate_validator)])
	sulfate= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(sulfate_validator)])
	sulfide= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(sulfide_validator)])

	fields = {
		'altitude': 'altitude',
		'elevation': 'elevation',
		'biomass': 'biomass',
		'density': 'density',
		'water_current': 'water current',
		'pressure': 'pressure',
		'ammonium': 'ammonium',
		'bromide': 'bromide',
		'calcium': 'calcium',
		'chloride': 'chloride',
		'chlorophyll': 'chlorophyll',
		'diether_lipids': 'diether lipids',
		'dissolved_carbon_dioxide': 'dissolved carbon dioxide',
		'dissolved_hydrogen': 'dissolved hydrogen',
		'dissolved_inorganic_carbon': 'dissolved inorganic carbon',
		'dissolved_organic_nitrogen': 'dissolved organic nitrogen',
		'dissolved_oxygen': 'dissolved oxygen',
		'nitrite': 'nitrite',
		'nitrogen': 'nitrogen',
		'organic_carbon': 'organic carbon',
		'organic_matter': 'organic matter',
		'organic_nitrogen': 'organic nitrogen',
		'phospholipid_fatty_acid': 'phospholipid fatty acid',
		'potassium': 'potassium',
		'silicate': 'silicate',
		'sulfate': 'sulfate',
		'sulfide': 'sulfide',
	}

	name = 'GSC_MIxS_miscellaneous_natural_or_artificial_environment'

class GSC_MIxS_miscellaneous_natural_or_artificial_environment_unit(SelfDescribingModel):

	altitude_units = [('m', 'm')]
	elevation_units = [('m', 'm')]
	biomass_units = [('g', 'g'), ('kg', 'kg'), ('t', 't')]
	density_units = [('g/m3', 'g/m3')]
	water_current_units = [('knot', 'knot'), ('m3/s', 'm3/s')]
	pressure_units = [('atm', 'atm'), ('bar', 'bar')]
	ammonium_units = [('µmol/L', 'µmol/L')]
	bromide_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	calcium_units = [('mg/L', 'mg/L'), ('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	chloride_units = [('mg/L', 'mg/L')]
	chlorophyll_units = [('mg/m3', 'mg/m3'), ('µg/L', 'µg/L')]
	diether_lipids_units = [('ng/L', 'ng/L')]
	dissolved_carbon_dioxide_units = [('µmol/L', 'µmol/L')]
	dissolved_hydrogen_units = [('µmol/L', 'µmol/L')]
	dissolved_inorganic_carbon_units = [('µg/L', 'µg/L')]
	dissolved_organic_nitrogen_units = [('mg/L', 'mg/L'), ('µg/L', 'µg/L')]
	dissolved_oxygen_units = [('µmol/kg', 'µmol/kg')]
	nitrite_units = [('µmol/L', 'µmol/L')]
	nitrogen_units = [('µmol/L', 'µmol/L')]
	organic_carbon_units = [('µmol/L', 'µmol/L')]
	organic_matter_units = [('µg/L', 'µg/L')]
	organic_nitrogen_units = [('µg/L', 'µg/L')]
	phospholipid_fatty_acid_units = [('mol/L', 'mol/L'), ('mol/g', 'mol/g')]
	potassium_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	silicate_units = [('µmol/L', 'µmol/L')]
	sulfate_units = [('mg/L', 'mg/L'), ('µmol/L', 'µmol/L')]
	sulfide_units = [('mg/L', 'mg/L'), ('µmol/L', 'µmol/L')]

	fields = {
		'altitude': 'altitude',
		'elevation': 'elevation',
		'biomass': 'biomass',
		'density': 'density',
		'water_current': 'water current',
		'pressure': 'pressure',
		'ammonium': 'ammonium',
		'bromide': 'bromide',
		'calcium': 'calcium',
		'chloride': 'chloride',
		'chlorophyll': 'chlorophyll',
		'diether_lipids': 'diether lipids',
		'dissolved_carbon_dioxide': 'dissolved carbon dioxide',
		'dissolved_hydrogen': 'dissolved hydrogen',
		'dissolved_inorganic_carbon': 'dissolved inorganic carbon',
		'dissolved_organic_nitrogen': 'dissolved organic nitrogen',
		'dissolved_oxygen': 'dissolved oxygen',
		'nitrite': 'nitrite',
		'nitrogen': 'nitrogen',
		'organic_carbon': 'organic carbon',
		'organic_matter': 'organic matter',
		'organic_nitrogen': 'organic nitrogen',
		'phospholipid_fatty_acid': 'phospholipid fatty acid',
		'potassium': 'potassium',
		'silicate': 'silicate',
		'sulfate': 'sulfate',
		'sulfide': 'sulfide',
	}

	name = 'GSC_MIxS_miscellaneous_natural_or_artificial_environment'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	altitude = models.CharField(max_length=120, choices=altitude_units, blank=False)
	elevation = models.CharField(max_length=120, choices=elevation_units, blank=False)
	biomass = models.CharField(max_length=120, choices=biomass_units, blank=False)
	density = models.CharField(max_length=120, choices=density_units, blank=False)
	water_current = models.CharField(max_length=120, choices=water_current_units, blank=False)
	pressure = models.CharField(max_length=120, choices=pressure_units, blank=False)
	ammonium = models.CharField(max_length=120, choices=ammonium_units, blank=False)
	bromide = models.CharField(max_length=120, choices=bromide_units, blank=False)
	calcium = models.CharField(max_length=120, choices=calcium_units, blank=False)
	chloride = models.CharField(max_length=120, choices=chloride_units, blank=False)
	chlorophyll = models.CharField(max_length=120, choices=chlorophyll_units, blank=False)
	diether_lipids = models.CharField(max_length=120, choices=diether_lipids_units, blank=False)
	dissolved_carbon_dioxide = models.CharField(max_length=120, choices=dissolved_carbon_dioxide_units, blank=False)
	dissolved_hydrogen = models.CharField(max_length=120, choices=dissolved_hydrogen_units, blank=False)
	dissolved_inorganic_carbon = models.CharField(max_length=120, choices=dissolved_inorganic_carbon_units, blank=False)
	dissolved_organic_nitrogen = models.CharField(max_length=120, choices=dissolved_organic_nitrogen_units, blank=False)
	dissolved_oxygen = models.CharField(max_length=120, choices=dissolved_oxygen_units, blank=False)
	nitrite = models.CharField(max_length=120, choices=nitrite_units, blank=False)
	nitrogen = models.CharField(max_length=120, choices=nitrogen_units, blank=False)
	organic_carbon = models.CharField(max_length=120, choices=organic_carbon_units, blank=False)
	organic_matter = models.CharField(max_length=120, choices=organic_matter_units, blank=False)
	organic_nitrogen = models.CharField(max_length=120, choices=organic_nitrogen_units, blank=False)
	phospholipid_fatty_acid = models.CharField(max_length=120, choices=phospholipid_fatty_acid_units, blank=False)
	potassium = models.CharField(max_length=120, choices=potassium_units, blank=False)
	silicate = models.CharField(max_length=120, choices=silicate_units, blank=False)
	sulfate = models.CharField(max_length=120, choices=sulfate_units, blank=False)
	sulfide = models.CharField(max_length=120, choices=sulfide_units, blank=False)

class GSC_MIxS_human_skin(SelfDescribingModel):

	medical_history_performed_choice = [('No', 'No'), ('Yes', 'Yes')]
	IHMC_medication_code_choice = [('01=1=Analgesics/NSAIDS', '01=1=Analgesics/NSAIDS'), ('02=2=Anesthetics', '02=2=Anesthetics'), ('03=3=Antacids/H2 antagonists', '03=3=Antacids/H2 antagonists'), ('04=4=Anti-acne', '04=4=Anti-acne'), ('05=5=Anti-asthma/bronchodilators', '05=5=Anti-asthma/bronchodilators'), ('06=6=Anti-cholesterol/Anti-hyperlipidemic', '06=6=Anti-cholesterol/Anti-hyperlipidemic'), ('07=7=Anti-coagulants', '07=7=Anti-coagulants'), ('08=8=Antibiotics/(anti)-infectives, parasitics, microbials', '08=8=Antibiotics/(anti)-infectives, parasitics, microbials'), ('09=9=Antidepressants/mood-altering drugs', '09=9=Antidepressants/mood-altering drugs'), ('10=10=Antihistamines/ Decongestants', '10=10=Antihistamines/ Decongestants'), ('11=11=Antihypertensives', '11=11=Antihypertensives'), ('12=12=Cardiovascular, other than hyperlipidemic/HTN', '12=12=Cardiovascular, other than hyperlipidemic/HTN'), ('13=13=Contraceptives (oral, implant, injectable)', '13=13=Contraceptives (oral, implant, injectable)'), ('14=14=Emergency/support medications', '14=14=Emergency/support medications'), ('15=15=Endocrine/Metabolic agents', '15=15=Endocrine/Metabolic agents'), ('16=16=GI meds (anti-diarrheal, emetic, spasmodics)', '16=16=GI meds (anti-diarrheal, emetic, spasmodics)'), ('17=17=Herbal/homeopathic products', '17=17=Herbal/homeopathic products'), ('18=18=Hormones/steroids', '18=18=Hormones/steroids'), ('19=19=OTC cold & flu', '19=19=OTC cold & flu'), ('20=20=Vaccine prophylaxis', '20=20=Vaccine prophylaxis'), ('21=21=Vitamins, minerals, food supplements', '21=21=Vitamins, minerals, food supplements'), ('99=99=Other', '99=99=Other')]
	host_occupation_choice = [('01=01 Accounting/Finance', '01=01 Accounting/Finance'), ('02=02 Advertising/Public Relations', '02=02 Advertising/Public Relations'), ('03=03 Arts/Entertainment/Publishing', '03=03 Arts/Entertainment/Publishing'), ('04=04 Automotive', '04=04 Automotive'), ('05=05 Banking/ Mortgage', '05=05 Banking/ Mortgage'), ('06=06 Biotech', '06=06 Biotech'), ('07=07 Broadcast/Journalism', '07=07 Broadcast/Journalism'), ('08=08 Business Development', '08=08 Business Development'), ('09=09 Clerical/Administrative', '09=09 Clerical/Administrative'), ('10=10 Construction/Trades', '10=10 Construction/Trades'), ('11=11 Consultant', '11=11 Consultant'), ('12=12 Customer Services', '12=12 Customer Services'), ('13=13 Design', '13=13 Design'), ('14=14 Education', '14=14 Education'), ('15=15 Engineering', '15=15 Engineering'), ('16=16 Entry Level', '16=16 Entry Level'), ('17=17 Executive', '17=17 Executive'), ('18=18 Food Service', '18=18 Food Service'), ('19=19 Government', '19=19 Government'), ('20=20 Grocery', '20=20 Grocery'), ('21=21 Healthcare', '21=21 Healthcare'), ('22=22 Hospitality', '22=22 Hospitality'), ('23=23 Human Resources', '23=23 Human Resources'), ('24=24 Information Technology', '24=24 Information Technology'), ('25=25 Insurance', '25=25 Insurance'), ('26=26 Law/Legal', '26=26 Law/Legal'), ('27=27 Management', '27=27 Management'), ('28=28 Manufacturing', '28=28 Manufacturing'), ('29=29 Marketing', '29=29 Marketing'), ('30=30 Pharmaceutical', '30=30 Pharmaceutical'), ('31=31 Professional Services', '31=31 Professional Services'), ('32=32 Purchasing', '32=32 Purchasing'), ('33=33 Quality Assurance (QA)', '33=33 Quality Assurance (QA)'), ('34=34 Research', '34=34 Research'), ('35=35 Restaurant', '35=35 Restaurant'), ('36=36 Retail', '36=36 Retail'), ('37=37 Sales', '37=37 Sales'), ('38=38 Science', '38=38 Science'), ('39=39 Security/Law Enforcement', '39=39 Security/Law Enforcement'), ('40=40 Shipping/Distribution', '40=40 Shipping/Distribution'), ('41=41 Strategy', '41=41 Strategy'), ('42=42 Student', '42=42 Student'), ('43=43 Telecommunications', '43=43 Telecommunications'), ('44=44 Training', '44=44 Training'), ('45=45 Transportation', '45=45 Transportation'), ('46=46 Warehouse', '46=46 Warehouse'), ('47=47 Other', '47=47 Other'), ('99=99 Unknown/Refused', '99=99 Unknown/Refused')]
	host_sex_choice = [('female', 'female'), ('hermaphrodite', 'hermaphrodite'), ('male', 'male'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('neuter', 'neuter'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('other', 'other'), ('restricted access', 'restricted access')]
	dominant_hand_choice = [('ambidextrous', 'ambidextrous'), ('left', 'left'), ('right', 'right')]

	host_age_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	host_height_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	host_body_mass_index_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	host_total_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	host_body_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	time_since_last_wash_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	host_pulse_validator = "[+-]?[0-9]+"

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	host_body_product= models.CharField(max_length=120, blank=True,help_text="substance ")
	medical_history_performed= models.CharField(max_length=120, blank=True,help_text="whether fu", choices=medical_history_performed_choice)
	dermatology_disorder= models.CharField(max_length=120, blank=True,help_text="History of")
	host_subject_id= models.CharField(max_length=120, blank=True,help_text="a unique i")
	IHMC_medication_code= models.CharField(max_length=120, blank=True,help_text="can includ", choices=IHMC_medication_code_choice)
	host_age= models.CharField(max_length=120, blank=True,help_text="age of hos", validators=[RegexValidator(host_age_validator)])
	host_body_site= models.CharField(max_length=120, blank=True,help_text="name of bo")
	host_height= models.CharField(max_length=120, blank=True,help_text="the height", validators=[RegexValidator(host_height_validator)])
	host_body_mass_index= models.CharField(max_length=120, blank=True,help_text="body mass ", validators=[RegexValidator(host_body_mass_index_validator)])
	ethnicity= models.CharField(max_length=120, blank=True,help_text="A category")
	host_occupation= models.CharField(max_length=120, blank=True,help_text="most frequ", choices=host_occupation_choice)
	host_total_mass= models.CharField(max_length=120, blank=True,help_text="total mass", validators=[RegexValidator(host_total_mass_validator)])
	host_phenotype= models.CharField(max_length=120, blank=True,help_text="phenotype ")
	host_body_temperature= models.CharField(max_length=120, blank=True,help_text="core body ", validators=[RegexValidator(host_body_temperature_validator)])
	host_sex= models.CharField(max_length=120, blank=True,help_text="Gender or ", choices=host_sex_choice)
	time_since_last_wash= models.CharField(max_length=120, blank=True,help_text="specificat", validators=[RegexValidator(time_since_last_wash_validator)])
	dominant_hand= models.CharField(max_length=120, blank=True,help_text="dominant h", choices=dominant_hand_choice)
	host_diet= models.CharField(max_length=120, blank=True,help_text="type of di")
	host_last_meal= models.CharField(max_length=120, blank=True,help_text="content of")
	host_family_relationship= models.CharField(max_length=120, blank=True,help_text="relationsh")
	host_genotype= models.CharField(max_length=120, blank=True,help_text="observed g")
	host_pulse= models.CharField(max_length=120, blank=True,help_text="resting pu", validators=[RegexValidator(host_pulse_validator)])

	fields = {
		'host_body_product': 'host body product',
		'medical_history_performed': 'medical history performed',
		'dermatology_disorder': 'dermatology disorder',
		'host_subject_id': 'host subject id',
		'IHMC_medication_code': 'IHMC medication code',
		'host_age': 'host age',
		'host_body_site': 'host body site',
		'host_height': 'host height',
		'host_body_mass_index': 'host body-mass index',
		'ethnicity': 'ethnicity',
		'host_occupation': 'host occupation',
		'host_total_mass': 'host total mass',
		'host_phenotype': 'host phenotype',
		'host_body_temperature': 'host body temperature',
		'host_sex': 'host sex',
		'time_since_last_wash': 'time since last wash',
		'dominant_hand': 'dominant hand',
		'host_diet': 'host diet',
		'host_last_meal': 'host last meal',
		'host_family_relationship': 'host family relationship',
		'host_genotype': 'host genotype',
		'host_pulse': 'host pulse',
	}

	name = 'GSC_MIxS_human_skin'

class GSC_MIxS_human_skin_unit(SelfDescribingModel):

	host_age_units = [('centuries', 'centuries'), ('days', 'days'), ('decades', 'decades'), ('hours', 'hours'), ('minutes', 'minutes'), ('months', 'months'), ('seconds', 'seconds'), ('weeks', 'weeks'), ('years', 'years')]
	host_height_units = [('cm', 'cm'), ('m', 'm'), ('mm', 'mm')]
	host_body_mass_index_units = [('kg/m2', 'kg/m2')]
	host_total_mass_units = [('g', 'g'), ('kg', 'kg')]
	host_body_temperature_units = [('ºC', 'ºC')]
	time_since_last_wash_units = [('hours', 'hours'), ('minutes', 'minutes')]
	host_pulse_units = [('bpm', 'bpm')]

	fields = {
		'host_age': 'host age',
		'host_height': 'host height',
		'host_body_mass_index': 'host body-mass index',
		'host_total_mass': 'host total mass',
		'host_body_temperature': 'host body temperature',
		'time_since_last_wash': 'time since last wash',
		'host_pulse': 'host pulse',
	}

	name = 'GSC_MIxS_human_skin'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	host_age = models.CharField(max_length=120, choices=host_age_units, blank=False)
	host_height = models.CharField(max_length=120, choices=host_height_units, blank=False)
	host_body_mass_index = models.CharField(max_length=120, choices=host_body_mass_index_units, blank=False)
	host_total_mass = models.CharField(max_length=120, choices=host_total_mass_units, blank=False)
	host_body_temperature = models.CharField(max_length=120, choices=host_body_temperature_units, blank=False)
	time_since_last_wash = models.CharField(max_length=120, choices=time_since_last_wash_units, blank=False)
	host_pulse = models.CharField(max_length=120, choices=host_pulse_units, blank=False)

class ENA_default_sample_checklist(SelfDescribingModel):

	environmental_sample_choice = [('No', 'No'), ('Yes', 'Yes')]


	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	cell_type= models.CharField(max_length=120, blank=True,help_text="cell type ")
	dev_stage= models.CharField(max_length=120, blank=True,help_text="if the sam")
	germline= models.CharField(max_length=120, blank=True,help_text="the sample")
	tissue_lib= models.CharField(max_length=120, blank=True,help_text="tissue lib")
	tissue_type= models.CharField(max_length=120, blank=True,help_text="tissue typ")
	isolation_source= models.CharField(max_length=120, blank=True,help_text="describes ")
	lat_lon= models.CharField(max_length=120, blank=True,help_text="geographic")
	collected_by= models.CharField(max_length=120, blank=True,help_text="name of pe")
	identified_by= models.CharField(max_length=120, blank=True,help_text="name of th")
	environmental_sample= models.CharField(max_length=120, blank=True,help_text="identifies", choices=environmental_sample_choice)
	mating_type= models.CharField(max_length=120, blank=True,help_text="mating typ")
	sex= models.CharField(max_length=120, blank=True,help_text="sex of the")
	lab_host= models.CharField(max_length=120, blank=True,help_text="scientific")
	bio_material= models.CharField(max_length=120, blank=True,help_text="Unique ide")
	culture_collection= models.CharField(max_length=120, blank=True,help_text="Unique ide")
	specimen_voucher= models.CharField(max_length=120, blank=True,help_text="Unique ide")
	cultivar= models.CharField(max_length=120, blank=True,help_text="cultivar (")
	ecotype= models.CharField(max_length=120, blank=True,help_text="a populati")
	isolate= models.CharField(max_length=120, blank=True,help_text="individual")
	sub_species= models.CharField(max_length=120, blank=True,help_text="name of su")
	variety= models.CharField(max_length=120, blank=True,help_text="variety (=")
	sub_strain= models.CharField(max_length=120, blank=True,help_text="name or id")
	cell_line= models.CharField(max_length=120, blank=True,help_text="cell line ")
	serotype= models.CharField(max_length=120, blank=True,help_text="serologica")
	serovar= models.CharField(max_length=120, blank=True,help_text="serologica")
	strain= models.CharField(max_length=120, blank=True,help_text="Name of th")

	fields = {
		'cell_type': 'cell_type',
		'dev_stage': 'dev_stage',
		'germline': 'germline',
		'tissue_lib': 'tissue_lib',
		'tissue_type': 'tissue_type',
		'isolation_source': 'isolation_source',
		'lat_lon': 'lat_lon',
		'collected_by': 'collected_by',
		'identified_by': 'identified_by',
		'environmental_sample': 'environmental_sample',
		'mating_type': 'mating_type',
		'sex': 'sex',
		'lab_host': 'lab_host',
		'bio_material': 'bio_material',
		'culture_collection': 'culture_collection',
		'specimen_voucher': 'specimen_voucher',
		'cultivar': 'cultivar',
		'ecotype': 'ecotype',
		'isolate': 'isolate',
		'sub_species': 'sub_species',
		'variety': 'variety',
		'sub_strain': 'sub_strain',
		'cell_line': 'cell_line',
		'serotype': 'serotype',
		'serovar': 'serovar',
		'strain': 'strain',
	}

	name = 'ENA_default_sample_checklist'

class ENA_default_sample_checklist_unit(SelfDescribingModel):


	fields = {
	}

	name = 'ENA_default_sample_checklist'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)

class GSC_MIxS_plant_associated(SelfDescribingModel):


	host_dry_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	host_wet_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	host_taxid_validator = "[+-]?[0-9]+"
	host_length_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	host_dry_mass= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(host_dry_mass_validator)])
	plant_product= models.CharField(max_length=120, blank=True,help_text="substance ")
	host_wet_mass= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(host_wet_mass_validator)])
	host_common_name= models.CharField(max_length=120, blank=True,help_text="common nam")
	host_taxid= models.CharField(max_length=120, blank=True,help_text="NCBI taxon", validators=[RegexValidator(host_taxid_validator)])
	host_life_stage= models.CharField(max_length=120, blank=True,help_text="descriptio")
	host_length= models.CharField(max_length=120, blank=True,help_text="the length", validators=[RegexValidator(host_length_validator)])
	plant_body_site= models.CharField(max_length=120, blank=True,help_text="name of bo")
	host_subspecific_genetic_lineage= models.CharField(max_length=120, blank=True,help_text="Informatio")
	climate_environment= models.CharField(max_length=120, blank=True,help_text="treatment ")
	gaseous_environment= models.CharField(max_length=120, blank=True,help_text="use of con")
	seasonal_environment= models.CharField(max_length=120, blank=True,help_text="treatment ")
	air_temperature_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	antibiotic_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	chemical_mutagen= models.CharField(max_length=120, blank=True,help_text="treatment ")
	fertilizer_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	fungicide_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	gravity= models.CharField(max_length=120, blank=True,help_text="informatio")
	growth_hormone_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	growth_media= models.CharField(max_length=120, blank=True,help_text="informatio")
	herbicide_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	humidity_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	mineral_nutrient_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	non_mineral_nutrient_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	pesticide_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	pH_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	radiation_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	rainfall_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	salt_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	standing_water_regimen= models.CharField(max_length=120, blank=True,help_text="treatment ")
	tissue_culture_growth_media= models.CharField(max_length=120, blank=True,help_text="descriptio")
	watering_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	water_temperature_regimen= models.CharField(max_length=120, blank=True,help_text="informatio")
	mechanical_damage= models.CharField(max_length=120, blank=True,help_text="informatio")

	fields = {
		'host_dry_mass': 'host dry mass',
		'plant_product': 'plant product',
		'host_wet_mass': 'host wet mass',
		'host_common_name': 'host common name',
		'host_taxid': 'host taxid',
		'host_life_stage': 'host life stage',
		'host_length': 'host length',
		'plant_body_site': 'plant body site',
		'host_subspecific_genetic_lineage': 'host subspecific genetic lineage',
		'climate_environment': 'climate environment',
		'gaseous_environment': 'gaseous environment',
		'seasonal_environment': 'seasonal environment',
		'air_temperature_regimen': 'air temperature regimen',
		'antibiotic_regimen': 'antibiotic regimen',
		'chemical_mutagen': 'chemical mutagen',
		'fertilizer_regimen': 'fertilizer regimen',
		'fungicide_regimen': 'fungicide regimen',
		'gravity': 'gravity',
		'growth_hormone_regimen': 'growth hormone regimen',
		'growth_media': 'growth media',
		'herbicide_regimen': 'herbicide regimen',
		'humidity_regimen': 'humidity regimen',
		'mineral_nutrient_regimen': 'mineral nutrient regimen',
		'non_mineral_nutrient_regimen': 'non-mineral nutrient regimen',
		'pesticide_regimen': 'pesticide regimen',
		'pH_regimen': 'pH regimen',
		'radiation_regimen': 'radiation regimen',
		'rainfall_regimen': 'rainfall regimen',
		'salt_regimen': 'salt regimen',
		'standing_water_regimen': 'standing water regimen',
		'tissue_culture_growth_media': 'tissue culture growth media',
		'watering_regimen': 'watering regimen',
		'water_temperature_regimen': 'water temperature regimen',
		'mechanical_damage': 'mechanical damage',
	}

	name = 'GSC_MIxS_plant_associated'

class GSC_MIxS_plant_associated_unit(SelfDescribingModel):

	host_dry_mass_units = [('g', 'g'), ('kg', 'kg'), ('mg', 'mg')]
	host_wet_mass_units = [('g', 'g'), ('kg', 'kg'), ('mg', 'mg')]
	host_length_units = [('cm', 'cm'), ('m', 'm'), ('mm', 'mm')]

	fields = {
		'host_dry_mass': 'host dry mass',
		'host_wet_mass': 'host wet mass',
		'host_length': 'host length',
	}

	name = 'GSC_MIxS_plant_associated'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	host_dry_mass = models.CharField(max_length=120, choices=host_dry_mass_units, blank=False)
	host_wet_mass = models.CharField(max_length=120, choices=host_wet_mass_units, blank=False)
	host_length = models.CharField(max_length=120, choices=host_length_units, blank=False)

class GSC_MIxS_water(SelfDescribingModel):

	tidal_stage_choice = [('high', 'high'), ('low', 'low')]

	conductivity_validator = "[1-9][0-9]*\.?[0-9]*([Ee][+-]?[0-9]+)?"
	fluorescence_validator = "[1-9][0-9]*\.?[0-9]*([Ee][+-]?[0-9]+)?"
	light_intensity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	mean_friction_velocity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	mean_peak_friction_velocity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	downward_PAR_validator = "[1-9][0-9]*\.?[0-9]*([Ee][+-]?[0-9]+)?"
	photon_flux_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	total_depth_of_water_column_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	alkyl_diethers_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	aminopeptidase_activity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	bacterial_carbon_production_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	bacterial_production_validator = "[1-9][0-9]*\.?[0-9]*([Ee][+-]?[0-9]+)?"
	bacterial_respiration_validator = "[1-9][0-9]*\.?[0-9]*([Ee][+-]?[0-9]+)?"
	bishomohopanol_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	carbon_nitrogen_ratio_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	dissolved_inorganic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	dissolved_inorganic_phosphorus_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	dissolved_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	glucosidase_activity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	magnesium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	n_alkanes_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	particulate_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	particulate_organic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	petroleum_hydrocarbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	phaeopigments_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	primary_production_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	redox_potential_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	soluble_reactive_phosphorus_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	suspended_particulate_matter_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	total_dissolved_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	total_inorganic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	total_particulate_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	total_phosphorus_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	atmospheric_data= models.CharField(max_length=120, blank=True,help_text="measuremen")
	conductivity= models.CharField(max_length=120, blank=True,help_text="electrical", validators=[RegexValidator(conductivity_validator)])
	fluorescence= models.CharField(max_length=120, blank=True,help_text="raw (volts", validators=[RegexValidator(fluorescence_validator)])
	light_intensity= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(light_intensity_validator)])
	mean_friction_velocity= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(mean_friction_velocity_validator)])
	mean_peak_friction_velocity= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(mean_peak_friction_velocity_validator)])
	downward_PAR= models.CharField(max_length=120, blank=True,help_text="visible wa", validators=[RegexValidator(downward_PAR_validator)])
	photon_flux= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(photon_flux_validator)])
	tidal_stage= models.CharField(max_length=120, blank=True,help_text="stage of t", choices=tidal_stage_choice)
	total_depth_of_water_column= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(total_depth_of_water_column_validator)])
	alkyl_diethers= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(alkyl_diethers_validator)])
	aminopeptidase_activity= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(aminopeptidase_activity_validator)])
	bacterial_carbon_production= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(bacterial_carbon_production_validator)])
	bacterial_production= models.CharField(max_length=120, blank=True,help_text="bacterial ", validators=[RegexValidator(bacterial_production_validator)])
	bacterial_respiration= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(bacterial_respiration_validator)])
	bishomohopanol= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(bishomohopanol_validator)])
	carbon_nitrogen_ratio= models.CharField(max_length=120, blank=True,help_text="ratio of a", validators=[RegexValidator(carbon_nitrogen_ratio_validator)])
	dissolved_inorganic_nitrogen= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(dissolved_inorganic_nitrogen_validator)])
	dissolved_inorganic_phosphorus= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(dissolved_inorganic_phosphorus_validator)])
	dissolved_organic_carbon= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(dissolved_organic_carbon_validator)])
	glucosidase_activity= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(glucosidase_activity_validator)])
	magnesium= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(magnesium_validator)])
	n_alkanes= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(n_alkanes_validator)])
	particulate_organic_carbon= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(particulate_organic_carbon_validator)])
	particulate_organic_nitrogen= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(particulate_organic_nitrogen_validator)])
	petroleum_hydrocarbon= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(petroleum_hydrocarbon_validator)])
	phaeopigments= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(phaeopigments_validator)])
	primary_production= models.CharField(max_length=120, blank=True,help_text="measuremen", validators=[RegexValidator(primary_production_validator)])
	redox_potential= models.CharField(max_length=120, blank=True,help_text="redox pote", validators=[RegexValidator(redox_potential_validator)])
	soluble_reactive_phosphorus= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(soluble_reactive_phosphorus_validator)])
	suspended_particulate_matter= models.CharField(max_length=120, blank=True,help_text="concentrat", validators=[RegexValidator(suspended_particulate_matter_validator)])
	total_dissolved_nitrogen= models.CharField(max_length=120, blank=True,help_text="total diss", validators=[RegexValidator(total_dissolved_nitrogen_validator)])
	total_inorganic_nitrogen= models.CharField(max_length=120, blank=True,help_text="total inor", validators=[RegexValidator(total_inorganic_nitrogen_validator)])
	total_particulate_carbon= models.CharField(max_length=120, blank=True,help_text="total part", validators=[RegexValidator(total_particulate_carbon_validator)])
	total_phosphorus= models.CharField(max_length=120, blank=True,help_text="total phos", validators=[RegexValidator(total_phosphorus_validator)])

	fields = {
		'atmospheric_data': 'atmospheric data',
		'conductivity': 'conductivity',
		'fluorescence': 'fluorescence',
		'light_intensity': 'light intensity',
		'mean_friction_velocity': 'mean friction velocity',
		'mean_peak_friction_velocity': 'mean peak friction velocity',
		'downward_PAR': 'downward PAR',
		'photon_flux': 'photon flux',
		'tidal_stage': 'tidal stage',
		'total_depth_of_water_column': 'total depth of water column',
		'alkyl_diethers': 'alkyl diethers',
		'aminopeptidase_activity': 'aminopeptidase activity',
		'bacterial_carbon_production': 'bacterial carbon production',
		'bacterial_production': 'bacterial production',
		'bacterial_respiration': 'bacterial respiration',
		'bishomohopanol': 'bishomohopanol',
		'carbon_nitrogen_ratio': 'carbon/nitrogen ratio',
		'dissolved_inorganic_nitrogen': 'dissolved inorganic nitrogen',
		'dissolved_inorganic_phosphorus': 'dissolved inorganic phosphorus',
		'dissolved_organic_carbon': 'dissolved organic carbon',
		'glucosidase_activity': 'glucosidase activity',
		'magnesium': 'magnesium',
		'n_alkanes': 'n-alkanes',
		'particulate_organic_carbon': 'particulate organic carbon',
		'particulate_organic_nitrogen': 'particulate organic nitrogen',
		'petroleum_hydrocarbon': 'petroleum hydrocarbon',
		'phaeopigments': 'phaeopigments',
		'primary_production': 'primary production',
		'redox_potential': 'redox potential',
		'soluble_reactive_phosphorus': 'soluble reactive phosphorus',
		'suspended_particulate_matter': 'suspended particulate matter',
		'total_dissolved_nitrogen': 'total dissolved nitrogen',
		'total_inorganic_nitrogen': 'total inorganic nitrogen',
		'total_particulate_carbon': 'total particulate carbon',
		'total_phosphorus': 'total phosphorus',
	}

	name = 'GSC_MIxS_water'

class GSC_MIxS_water_unit(SelfDescribingModel):

	conductivity_units = [('mS/cm', 'mS/cm')]
	fluorescence_units = [('V', 'V'), ('mg Chla/m3', 'mg Chla/m3')]
	light_intensity_units = [('lux', 'lux')]
	mean_friction_velocity_units = [('m/s', 'm/s')]
	mean_peak_friction_velocity_units = [('m/s', 'm/s')]
	downward_PAR_units = [('µE/m2/s', 'µE/m2/s')]
	photon_flux_units = [('µmol/m2/s', 'µmol/m2/s')]
	total_depth_of_water_column_units = [('m', 'm')]
	alkyl_diethers_units = [('M/L', 'M/L'), ('µg/L', 'µg/L')]
	aminopeptidase_activity_units = [('mol/L/h', 'mol/L/h')]
	bacterial_carbon_production_units = [('ng/h', 'ng/h')]
	bacterial_production_units = [('mg/m3/d', 'mg/m3/d')]
	bacterial_respiration_units = [('mg/m3/d', 'mg/m3/d')]
	bishomohopanol_units = [('µg/L', 'µg/L'), ('µg/g', 'µg/g')]
	dissolved_inorganic_nitrogen_units = [('µg/L', 'µg/L')]
	dissolved_inorganic_phosphorus_units = [('µg/L', 'µg/L')]
	dissolved_organic_carbon_units = [('µmol/L', 'µmol/L')]
	glucosidase_activity_units = [('mol/L/h', 'mol/L/h')]
	magnesium_units = [('mg/L', 'mg/L'), ('mol/L', 'mol/L'), ('parts/million', 'parts/million')]
	n_alkanes_units = [('µmol/L', 'µmol/L')]
	particulate_organic_carbon_units = [('µg/L', 'µg/L')]
	particulate_organic_nitrogen_units = [('µg/L', 'µg/L')]
	petroleum_hydrocarbon_units = [('µmol/L', 'µmol/L')]
	phaeopigments_units = [('mg/m3', 'mg/m3'), ('µg/L', 'µg/L')]
	primary_production_units = [('g/m2/day', 'g/m2/day'), ('mg/m3/day', 'mg/m3/day')]
	redox_potential_units = [('mV', 'mV')]
	soluble_reactive_phosphorus_units = [('µmol/L', 'µmol/L')]
	suspended_particulate_matter_units = [('mg/L', 'mg/L')]
	total_dissolved_nitrogen_units = [('µg/L', 'µg/L')]
	total_inorganic_nitrogen_units = [('µg/L', 'µg/L')]
	total_particulate_carbon_units = [('µg/L', 'µg/L'), ('µmol/L', 'µmol/L')]
	total_phosphorus_units = [('µmol/L', 'µmol/L')]

	fields = {
		'conductivity': 'conductivity',
		'fluorescence': 'fluorescence',
		'light_intensity': 'light intensity',
		'mean_friction_velocity': 'mean friction velocity',
		'mean_peak_friction_velocity': 'mean peak friction velocity',
		'downward_PAR': 'downward PAR',
		'photon_flux': 'photon flux',
		'total_depth_of_water_column': 'total depth of water column',
		'alkyl_diethers': 'alkyl diethers',
		'aminopeptidase_activity': 'aminopeptidase activity',
		'bacterial_carbon_production': 'bacterial carbon production',
		'bacterial_production': 'bacterial production',
		'bacterial_respiration': 'bacterial respiration',
		'bishomohopanol': 'bishomohopanol',
		'dissolved_inorganic_nitrogen': 'dissolved inorganic nitrogen',
		'dissolved_inorganic_phosphorus': 'dissolved inorganic phosphorus',
		'dissolved_organic_carbon': 'dissolved organic carbon',
		'glucosidase_activity': 'glucosidase activity',
		'magnesium': 'magnesium',
		'n_alkanes': 'n-alkanes',
		'particulate_organic_carbon': 'particulate organic carbon',
		'particulate_organic_nitrogen': 'particulate organic nitrogen',
		'petroleum_hydrocarbon': 'petroleum hydrocarbon',
		'phaeopigments': 'phaeopigments',
		'primary_production': 'primary production',
		'redox_potential': 'redox potential',
		'soluble_reactive_phosphorus': 'soluble reactive phosphorus',
		'suspended_particulate_matter': 'suspended particulate matter',
		'total_dissolved_nitrogen': 'total dissolved nitrogen',
		'total_inorganic_nitrogen': 'total inorganic nitrogen',
		'total_particulate_carbon': 'total particulate carbon',
		'total_phosphorus': 'total phosphorus',
	}

	name = 'GSC_MIxS_water'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	conductivity = models.CharField(max_length=120, choices=conductivity_units, blank=False)
	fluorescence = models.CharField(max_length=120, choices=fluorescence_units, blank=False)
	light_intensity = models.CharField(max_length=120, choices=light_intensity_units, blank=False)
	mean_friction_velocity = models.CharField(max_length=120, choices=mean_friction_velocity_units, blank=False)
	mean_peak_friction_velocity = models.CharField(max_length=120, choices=mean_peak_friction_velocity_units, blank=False)
	downward_PAR = models.CharField(max_length=120, choices=downward_PAR_units, blank=False)
	photon_flux = models.CharField(max_length=120, choices=photon_flux_units, blank=False)
	total_depth_of_water_column = models.CharField(max_length=120, choices=total_depth_of_water_column_units, blank=False)
	alkyl_diethers = models.CharField(max_length=120, choices=alkyl_diethers_units, blank=False)
	aminopeptidase_activity = models.CharField(max_length=120, choices=aminopeptidase_activity_units, blank=False)
	bacterial_carbon_production = models.CharField(max_length=120, choices=bacterial_carbon_production_units, blank=False)
	bacterial_production = models.CharField(max_length=120, choices=bacterial_production_units, blank=False)
	bacterial_respiration = models.CharField(max_length=120, choices=bacterial_respiration_units, blank=False)
	bishomohopanol = models.CharField(max_length=120, choices=bishomohopanol_units, blank=False)
	dissolved_inorganic_nitrogen = models.CharField(max_length=120, choices=dissolved_inorganic_nitrogen_units, blank=False)
	dissolved_inorganic_phosphorus = models.CharField(max_length=120, choices=dissolved_inorganic_phosphorus_units, blank=False)
	dissolved_organic_carbon = models.CharField(max_length=120, choices=dissolved_organic_carbon_units, blank=False)
	glucosidase_activity = models.CharField(max_length=120, choices=glucosidase_activity_units, blank=False)
	magnesium = models.CharField(max_length=120, choices=magnesium_units, blank=False)
	n_alkanes = models.CharField(max_length=120, choices=n_alkanes_units, blank=False)
	particulate_organic_carbon = models.CharField(max_length=120, choices=particulate_organic_carbon_units, blank=False)
	particulate_organic_nitrogen = models.CharField(max_length=120, choices=particulate_organic_nitrogen_units, blank=False)
	petroleum_hydrocarbon = models.CharField(max_length=120, choices=petroleum_hydrocarbon_units, blank=False)
	phaeopigments = models.CharField(max_length=120, choices=phaeopigments_units, blank=False)
	primary_production = models.CharField(max_length=120, choices=primary_production_units, blank=False)
	redox_potential = models.CharField(max_length=120, choices=redox_potential_units, blank=False)
	soluble_reactive_phosphorus = models.CharField(max_length=120, choices=soluble_reactive_phosphorus_units, blank=False)
	suspended_particulate_matter = models.CharField(max_length=120, choices=suspended_particulate_matter_units, blank=False)
	total_dissolved_nitrogen = models.CharField(max_length=120, choices=total_dissolved_nitrogen_units, blank=False)
	total_inorganic_nitrogen = models.CharField(max_length=120, choices=total_inorganic_nitrogen_units, blank=False)
	total_particulate_carbon = models.CharField(max_length=120, choices=total_particulate_carbon_units, blank=False)
	total_phosphorus = models.CharField(max_length=120, choices=total_phosphorus_units, blank=False)

class GSC_MIxS_soil(SelfDescribingModel):

	profile_position_choice = [('backslope', 'backslope'), ('footslope', 'footslope'), ('shoulder', 'shoulder'), ('summit', 'summit'), ('toeslope', 'toeslope')]
	soil_horizon_choice = [('A horizon', 'A horizon'), ('B horizon', 'B horizon'), ('C horizon', 'C horizon'), ('E horizon', 'E horizon'), ('O horizon', 'O horizon'), ('Permafrost', 'Permafrost'), ('R layer', 'R layer')]
	soil_type_choice = [('Acrisol', 'Acrisol'), ('Albeluvisol', 'Albeluvisol'), ('Alisol', 'Alisol'), ('Andosol', 'Andosol'), ('Anthrosol', 'Anthrosol'), ('Arenosol', 'Arenosol'), ('Calcisol', 'Calcisol'), ('Cambisol', 'Cambisol'), ('Chernozem', 'Chernozem'), ('Cryosol', 'Cryosol'), ('Durisol', 'Durisol'), ('Ferralsol', 'Ferralsol'), ('Fluvisol', 'Fluvisol'), ('Gleysol', 'Gleysol'), ('Gypsisol', 'Gypsisol'), ('Histosol', 'Histosol'), ('Kastanozem', 'Kastanozem'), ('Leptosol', 'Leptosol'), ('Lixisol', 'Lixisol'), ('Luvisol', 'Luvisol'), ('Nitisol', 'Nitisol'), ('Phaeozem', 'Phaeozem'), ('Planosol', 'Planosol'), ('Plinthosol', 'Plinthosol'), ('Podzol', 'Podzol'), ('Regosol', 'Regosol'), ('Solonchak', 'Solonchak'), ('Solonetz', 'Solonetz'), ('Stagnosol', 'Stagnosol'), ('Technosol', 'Technosol'), ('Umbrisol', 'Umbrisol'), ('Vertisol', 'Vertisol')]
	drainage_classification_choice = [('excessively drained', 'excessively drained'), ('moderately well', 'moderately well'), ('poorly', 'poorly'), ('somewhat poorly', 'somewhat poorly'), ('very poorly', 'very poorly'), ('well', 'well')]
	history_tillage_choice = [('chisel', 'chisel'), ('cutting disc', 'cutting disc'), ('disc plough', 'disc plough'), ('drill', 'drill'), ('mouldboard', 'mouldboard'), ('ridge till', 'ridge till'), ('strip tillage', 'strip tillage'), ('tined', 'tined'), ('zonal tillage', 'zonal tillage')]

	slope_gradient_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	sample_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	microbial_biomass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	extreme_unusual_properties_Al_saturation_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	mean_annual_and_seasonal_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	mean_annual_and_seasonal_precipitation_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	total_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	water_content_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	slope_gradient= models.CharField(max_length=120, blank=True,help_text="commonly c", validators=[RegexValidator(slope_gradient_validator)])
	slope_aspect= models.CharField(max_length=120, blank=True,help_text="the direct")
	profile_position= models.CharField(max_length=120, blank=True,help_text="cross-sect", choices=profile_position_choice)
	pooling_of_DNA_extracts_if_done= models.CharField(max_length=120, blank=True,help_text="were multi")
	composite_design_sieving_if_any= models.CharField(max_length=120, blank=True,help_text="collection")
	sample_weight_for_DNA_extraction= models.CharField(max_length=120, blank=True,help_text="weight (g)", validators=[RegexValidator(sample_weight_for_DNA_extraction_validator)])
	storage_conditions_fresh_frozen_other= models.CharField(max_length=120, blank=True,help_text="explain ho")
	microbial_biomass= models.CharField(max_length=120, blank=True,help_text="the part o", validators=[RegexValidator(microbial_biomass_validator)])
	microbial_biomass_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	salinity_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	extreme_unusual_properties_heavy_metals= models.CharField(max_length=120, blank=True,help_text="heavy meta")
	extreme_unusual_properties_heavy_metals_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	extreme_unusual_properties_Al_saturation= models.CharField(max_length=120, blank=True,help_text="aluminum s", validators=[RegexValidator(extreme_unusual_properties_Al_saturation_validator)])
	extreme_unusual_properties_Al_saturation_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	link_to_climate_information= models.CharField(max_length=120, blank=True,help_text="link to cl")
	link_to_classification_information= models.CharField(max_length=120, blank=True,help_text="link to di")
	links_to_additional_analysis= models.CharField(max_length=120, blank=True,help_text="link to ad")
	current_land_use= models.CharField(max_length=120, blank=True,help_text="present st")
	current_vegetation= models.CharField(max_length=120, blank=True,help_text="vegetation")
	current_vegetation_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	soil_horizon= models.CharField(max_length=120, blank=True,help_text="specific l", choices=soil_horizon_choice)
	soil_horizon_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	mean_annual_and_seasonal_temperature= models.CharField(max_length=120, blank=True,help_text="mean annua", validators=[RegexValidator(mean_annual_and_seasonal_temperature_validator)])
	mean_annual_and_seasonal_precipitation= models.CharField(max_length=120, blank=True,help_text="mean annua", validators=[RegexValidator(mean_annual_and_seasonal_precipitation_validator)])
	soil_taxonomic_FAO_classification= models.CharField(max_length=120, blank=True,help_text="soil class")
	soil_taxonomic_local_classification= models.CharField(max_length=120, blank=True,help_text="soil class")
	soil_taxonomic_local_classification_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	soil_type= models.CharField(max_length=120, blank=True,help_text="Descriptio", choices=soil_type_choice)
	soil_type_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	drainage_classification= models.CharField(max_length=120, blank=True,help_text="drainage c", choices=drainage_classification_choice)
	soil_texture_measurement= models.CharField(max_length=120, blank=True,help_text="the relati")
	soil_texture_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	pH_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	water_content_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	total_organic_C_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	total_nitrogen_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	total_organic_carbon= models.CharField(max_length=120, blank=True,help_text="Definition", validators=[RegexValidator(total_organic_carbon_validator)])
	water_content= models.CharField(max_length=120, blank=True,help_text="water cont", validators=[RegexValidator(water_content_validator)])
	history_previous_land_use= models.CharField(max_length=120, blank=True,help_text="previous l")
	history_previous_land_use_method= models.CharField(max_length=120, blank=True,help_text="reference ")
	history_crop_rotation= models.CharField(max_length=120, blank=True,help_text="whether or")
	history_agrochemical_additions= models.CharField(max_length=120, blank=True,help_text="addition o")
	history_tillage= models.CharField(max_length=120, blank=True,help_text="note metho", choices=history_tillage_choice)
	history_fire= models.CharField(max_length=120, blank=True,help_text="historical")
	history_flooding= models.CharField(max_length=120, blank=True,help_text="historical")
	history_extreme_events= models.CharField(max_length=120, blank=True,help_text="unusual ph")

	fields = {
		'slope_gradient': 'slope gradient',
		'slope_aspect': 'slope aspect',
		'profile_position': 'profile position',
		'pooling_of_DNA_extracts_if_done': 'pooling of DNA extracts (if done)',
		'composite_design_sieving_if_any': 'composite design/sieving (if any)',
		'sample_weight_for_DNA_extraction': 'sample weight for DNA extraction',
		'storage_conditions_fresh_frozen_other': 'storage conditions (fresh/frozen/other)',
		'microbial_biomass': 'microbial biomass',
		'microbial_biomass_method': 'microbial biomass method',
		'salinity_method': 'salinity method',
		'extreme_unusual_properties_heavy_metals': 'extreme_unusual_properties/heavy metals',
		'extreme_unusual_properties_heavy_metals_method': 'extreme_unusual_properties/heavy metals method',
		'extreme_unusual_properties_Al_saturation': 'extreme_unusual_properties/Al saturation',
		'extreme_unusual_properties_Al_saturation_method': 'extreme_unusual_properties/Al saturation method',
		'link_to_climate_information': 'link to climate information',
		'link_to_classification_information': 'link to classification information',
		'links_to_additional_analysis': 'links to additional analysis',
		'current_land_use': 'current land use',
		'current_vegetation': 'current vegetation',
		'current_vegetation_method': 'current vegetation method',
		'soil_horizon': 'soil horizon',
		'soil_horizon_method': 'soil horizon method',
		'mean_annual_and_seasonal_temperature': 'mean annual and seasonal temperature',
		'mean_annual_and_seasonal_precipitation': 'mean annual and seasonal precipitation',
		'soil_taxonomic_FAO_classification': 'soil_taxonomic/FAO classification',
		'soil_taxonomic_local_classification': 'soil_taxonomic/local classification',
		'soil_taxonomic_local_classification_method': 'soil_taxonomic/local classification method',
		'soil_type': 'soil type',
		'soil_type_method': 'soil type method',
		'drainage_classification': 'drainage classification',
		'soil_texture_measurement': 'soil texture measurement',
		'soil_texture_method': 'soil texture method',
		'pH_method': 'pH method',
		'water_content_method': 'water content method',
		'total_organic_C_method': 'total organic C method',
		'total_nitrogen_method': 'total nitrogen method',
		'total_organic_carbon': 'total organic carbon',
		'water_content': 'water content',
		'history_previous_land_use': 'history/previous land use',
		'history_previous_land_use_method': 'history/previous land use method',
		'history_crop_rotation': 'history/crop rotation',
		'history_agrochemical_additions': 'history/agrochemical additions',
		'history_tillage': 'history/tillage',
		'history_fire': 'history/fire',
		'history_flooding': 'history/flooding',
		'history_extreme_events': 'history/extreme events',
	}

	name = 'GSC_MIxS_soil'

class GSC_MIxS_soil_unit(SelfDescribingModel):

	slope_gradient_units = [('%', '%')]
	sample_weight_for_DNA_extraction_units = [('g', 'g')]
	microbial_biomass_units = [('g/kg', 'g/kg')]
	extreme_unusual_properties_Al_saturation_units = [('%', '%')]
	mean_annual_and_seasonal_temperature_units = [('ºC', 'ºC')]
	mean_annual_and_seasonal_precipitation_units = [('mm', 'mm')]
	soil_texture_measurement_units = [('% sand/silt/clay', '% sand/silt/clay')]
	total_organic_carbon_units = [('g/kg', 'g/kg')]
	water_content_units = [('cm3/cm3', 'cm3/cm3'), ('g/g', 'g/g')]

	fields = {
		'slope_gradient': 'slope gradient',
		'sample_weight_for_DNA_extraction': 'sample weight for DNA extraction',
		'microbial_biomass': 'microbial biomass',
		'extreme_unusual_properties_Al_saturation': 'extreme_unusual_properties/Al saturation',
		'mean_annual_and_seasonal_temperature': 'mean annual and seasonal temperature',
		'mean_annual_and_seasonal_precipitation': 'mean annual and seasonal precipitation',
		'soil_texture_measurement': 'soil texture measurement',
		'total_organic_carbon': 'total organic carbon',
		'water_content': 'water content',
	}

	name = 'GSC_MIxS_soil'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	slope_gradient = models.CharField(max_length=120, choices=slope_gradient_units, blank=False)
	sample_weight_for_DNA_extraction = models.CharField(max_length=120, choices=sample_weight_for_DNA_extraction_units, blank=False)
	microbial_biomass = models.CharField(max_length=120, choices=microbial_biomass_units, blank=False)
	extreme_unusual_properties_Al_saturation = models.CharField(max_length=120, choices=extreme_unusual_properties_Al_saturation_units, blank=False)
	mean_annual_and_seasonal_temperature = models.CharField(max_length=120, choices=mean_annual_and_seasonal_temperature_units, blank=False)
	mean_annual_and_seasonal_precipitation = models.CharField(max_length=120, choices=mean_annual_and_seasonal_precipitation_units, blank=False)
	soil_texture_measurement = models.CharField(max_length=120, choices=soil_texture_measurement_units, blank=False)
	total_organic_carbon = models.CharField(max_length=120, choices=total_organic_carbon_units, blank=False)
	water_content = models.CharField(max_length=120, choices=water_content_units, blank=False)

class GSC_MIxS_human_gut(SelfDescribingModel):



	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	gastrointestinal_tract_disorder= models.CharField(max_length=120, blank=True,help_text="History of")
	liver_disorder= models.CharField(max_length=120, blank=True,help_text="History of")
	special_diet= models.CharField(max_length=120, blank=True,help_text="specificat")

	fields = {
		'gastrointestinal_tract_disorder': 'gastrointestinal tract disorder',
		'liver_disorder': 'liver disorder',
		'special_diet': 'special diet',
	}

	name = 'GSC_MIxS_human_gut'

class GSC_MIxS_human_gut_unit(SelfDescribingModel):


	fields = {
	}

	name = 'GSC_MIxS_human_gut'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)

class GSC_MIxS_host_associated(SelfDescribingModel):


	host_blood_pressure_diastolic_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	host_blood_pressure_systolic_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	host_body_habitat= models.CharField(max_length=120, blank=True,help_text="original b")
	host_growth_conditions= models.CharField(max_length=120, blank=True,help_text="literature")
	host_substrate= models.CharField(max_length=120, blank=True,help_text="the growth")
	host_color= models.CharField(max_length=120, blank=True,help_text="the color ")
	host_shape= models.CharField(max_length=120, blank=True,help_text="morphologi")
	host_blood_pressure_diastolic= models.CharField(max_length=120, blank=True,help_text="resting di", validators=[RegexValidator(host_blood_pressure_diastolic_validator)])
	host_blood_pressure_systolic= models.CharField(max_length=120, blank=True,help_text="resting sy", validators=[RegexValidator(host_blood_pressure_systolic_validator)])
	gravidity= models.CharField(max_length=120, blank=True,help_text="Whether or")

	fields = {
		'host_body_habitat': 'host body habitat',
		'host_growth_conditions': 'host growth conditions',
		'host_substrate': 'host substrate',
		'host_color': 'host color',
		'host_shape': 'host shape',
		'host_blood_pressure_diastolic': 'host blood pressure diastolic',
		'host_blood_pressure_systolic': 'host blood pressure systolic',
		'gravidity': 'gravidity',
	}

	name = 'GSC_MIxS_host_associated'

class GSC_MIxS_host_associated_unit(SelfDescribingModel):

	host_blood_pressure_diastolic_units = [('mm Hg', 'mm Hg')]
	host_blood_pressure_systolic_units = [('mm Hg', 'mm Hg')]

	fields = {
		'host_blood_pressure_diastolic': 'host blood pressure diastolic',
		'host_blood_pressure_systolic': 'host blood pressure systolic',
	}

	name = 'GSC_MIxS_host_associated'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	host_blood_pressure_diastolic = models.CharField(max_length=120, choices=host_blood_pressure_diastolic_units, blank=False)
	host_blood_pressure_systolic = models.CharField(max_length=120, choices=host_blood_pressure_systolic_units, blank=False)

class GSC_MIxS_human_vaginal(SelfDescribingModel):

	hysterectomy_choice = [('No', 'No'), ('Yes', 'Yes')]


	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	gynecological_disorder= models.CharField(max_length=120, blank=True,help_text="History of")
	urogenital_disorder= models.CharField(max_length=120, blank=True,help_text="History of")
	menarche= models.CharField(max_length=120, blank=True,help_text="date of mo")
	sexual_activity= models.CharField(max_length=120, blank=True,help_text="current se")
	pregnancy= models.CharField(max_length=120, blank=True,help_text="date due o")
	douche= models.CharField(max_length=120, blank=True,help_text="date of mo")
	birth_control= models.CharField(max_length=120, blank=True,help_text="specificat")
	menopause= models.CharField(max_length=120, blank=True,help_text="date of on")
	HRT= models.CharField(max_length=120, blank=True,help_text="whether su")
	hysterectomy= models.CharField(max_length=120, blank=True,help_text="specificat", choices=hysterectomy_choice)

	fields = {
		'gynecological_disorder': 'gynecological disorder',
		'urogenital_disorder': 'urogenital disorder',
		'menarche': 'menarche',
		'sexual_activity': 'sexual activity',
		'pregnancy': 'pregnancy',
		'douche': 'douche',
		'birth_control': 'birth control',
		'menopause': 'menopause',
		'HRT': 'HRT',
		'hysterectomy': 'hysterectomy',
	}

	name = 'GSC_MIxS_human_vaginal'

class GSC_MIxS_human_vaginal_unit(SelfDescribingModel):


	fields = {
	}

	name = 'GSC_MIxS_human_vaginal'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)

class GSC_MIxS_human_oral(SelfDescribingModel):


	time_since_last_toothbrushing_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	nose_mouth_teeth_throat_disorder= models.CharField(max_length=120, blank=True,help_text="History of")
	time_since_last_toothbrushing= models.CharField(max_length=120, blank=True,help_text="specificat", validators=[RegexValidator(time_since_last_toothbrushing_validator)])

	fields = {
		'nose_mouth_teeth_throat_disorder': 'nose/mouth/teeth/throat disorder',
		'time_since_last_toothbrushing': 'time since last toothbrushing',
	}

	name = 'GSC_MIxS_human_oral'

class GSC_MIxS_human_oral_unit(SelfDescribingModel):

	time_since_last_toothbrushing_units = [('hours', 'hours'), ('minutes', 'minutes')]

	fields = {
		'time_since_last_toothbrushing': 'time since last toothbrushing',
	}

	name = 'GSC_MIxS_human_oral'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	time_since_last_toothbrushing = models.CharField(max_length=120, choices=time_since_last_toothbrushing_units, blank=False)

class ENA_binned_metagenome(SelfDescribingModel):

	sixteen_s_recovered_choice = [('No', 'No'), ('Yes', 'Yes')]
	contamination_screening_input_choice = [('contigs', 'contigs'), ('reads', 'reads')]
	reassembly_post_binning_choice = [('No', 'No'), ('Yes', 'Yes')]
	assembly_quality_choice = [('Many fragments with little to no review of assembly other than reporting of standard assembly statistics', 'Many fragments with little to no review of assembly other than reporting of standard assembly statistics'), ('Multiple fragments where gaps span repetitive regions. Presence of the 23S, 16S, and 5S rRNA genes and at least 18 tRNAs', 'Multiple fragments where gaps span repetitive regions. Presence of the 23S, 16S, and 5S rRNA genes and at least 18 tRNAs'), ('Single contiguous sequence without gaps or ambiguities with a consensus error rate equivalent to Q50 or better', 'Single contiguous sequence without gaps or ambiguities with a consensus error rate equivalent to Q50 or better')]
	investigation_type_choice = [('bacteria_archaea', 'bacteria_archaea'), ('eukaryote', 'eukaryote'), ('metagenome', 'metagenome'), ('metagenome-assembled genome', 'metagenome-assembled genome'), ('metatranscriptome', 'metatranscriptome'), ('mimarks-specimen', 'mimarks-specimen'), ('mimarks-survey', 'mimarks-survey'), ('organelle', 'organelle'), ('plasmid', 'plasmid'), ('single amplified genome', 'single amplified genome'), ('uncultivated viral genomes', 'uncultivated viral genomes'), ('virus', 'virus')]

	sample_derived_from_validator = "(^[ESD]R[SR]\d{6,}(,[ESD]R[SR]\d{6,})*$)|(^SAM[END][AG]?\d+(,SAM[END][AG]?\d+)*$)|(^EGA[NR]\d{11}(,EGA[NR]\d{11})*$)|(^[ESD]R[SR]\d{6,}-[ESD]R[SR]\d{6,}$)|(^SAM[END][AG]?\d+-SAM[END][AG]?\d+$)|(^EGA[NR]\d{11}-EGA[NR]\d{11}$)"
	number_of_standard_tRNAs_extracted_validator = "[+-]?[0-9]+"
	completeness_score_validator = "^(\d|[1-9]\d|\d\.\d{1,2}|[1-9]\d\.\d{1,2}|100)$"
	contamination_score_validator = "^(\d|[1-9]\d|\d\.\d{1,2}|[1-9]\d\.\d{1,2}|100)$"

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	metagenomic_source= models.CharField(max_length=120, blank=False,help_text="The metage")
	sample_derived_from= models.CharField(max_length=120, blank=False,help_text="Reference ", validators=[RegexValidator(sample_derived_from_validator)])
	number_of_standard_tRNAs_extracted= models.CharField(max_length=120, blank=True,help_text="The total ", validators=[RegexValidator(number_of_standard_tRNAs_extracted_validator)])
	sixteen_s_recovered= models.CharField(max_length=120, blank=True,help_text="Can a 16S ", choices=sixteen_s_recovered_choice)
	sixteen_s_recovery_software= models.CharField(max_length=120, blank=True,help_text="Tools used")
	tRNA_extraction_software= models.CharField(max_length=120, blank=True,help_text="Tools used")
	completeness_score= models.CharField(max_length=120, blank=False,help_text="Completene", validators=[RegexValidator(completeness_score_validator)])
	completeness_software= models.CharField(max_length=120, blank=False,help_text="Tools used")
	completeness_approach= models.CharField(max_length=120, blank=True,help_text="The approa")
	contamination_score= models.CharField(max_length=120, blank=False,help_text="The contam", validators=[RegexValidator(contamination_score_validator)])
	contamination_screening_input= models.CharField(max_length=120, blank=True,help_text="The type o", choices=contamination_screening_input_choice)
	contamination_screening_parameters= models.CharField(max_length=120, blank=True,help_text="Specific p")
	decontamination_software= models.CharField(max_length=120, blank=True,help_text="Tool(s) us")
	binning_software= models.CharField(max_length=120, blank=False,help_text="Tool(s) us")
	reassembly_post_binning= models.CharField(max_length=120, blank=True,help_text="Has an ass", choices=reassembly_post_binning_choice)
	MAG_coverage_software= models.CharField(max_length=120, blank=True,help_text="Tool(s) us")
	assembly_quality= models.CharField(max_length=120, blank=False,help_text="The assemb", choices=assembly_quality_choice)
	investigation_type= models.CharField(max_length=120, blank=True,help_text="Nucleic Ac", choices=investigation_type_choice)
	binning_parameters= models.CharField(max_length=120, blank=False,help_text="The parame")
	taxonomic_identity_marker= models.CharField(max_length=120, blank=False,help_text="The phylog")
	size_fraction_selected= models.CharField(max_length=120, blank=True,help_text="Filtering ")
	taxonomic_classification= models.CharField(max_length=120, blank=True,help_text="Method use")
	assembly_software= models.CharField(max_length=120, blank=False,help_text="Tool(s) us")

	fields = {
		'metagenomic_source': 'metagenomic source',
		'sample_derived_from': 'sample derived from',
		'number_of_standard_tRNAs_extracted': 'number of standard tRNAs extracted',
		'sixteen_s_recovered': '16s recovered',
		'sixteen_s_recovery_software': '16S recovery software',
		'tRNA_extraction_software': 'tRNA extraction software',
		'completeness_score': 'completeness score',
		'completeness_software': 'completeness software',
		'completeness_approach': 'completeness approach',
		'contamination_score': 'contamination score',
		'contamination_screening_input': 'contamination screening input',
		'contamination_screening_parameters': 'contamination screening parameters',
		'decontamination_software': 'decontamination software',
		'binning_software': 'binning software',
		'reassembly_post_binning': 'reassembly post binning',
		'MAG_coverage_software': 'MAG coverage software',
		'assembly_quality': 'assembly quality',
		'investigation_type': 'investigation type',
		'binning_parameters': 'binning parameters',
		'taxonomic_identity_marker': 'taxonomic identity marker',
		'size_fraction_selected': 'size fraction selected',
		'taxonomic_classification': 'taxonomic classification',
		'assembly_software': 'assembly software',
	}

	name = 'ENA_binned_metagenome'

class ENA_binned_metagenome_unit(SelfDescribingModel):

	completeness_score_units = [('%', '%')]
	contamination_score_units = [('%', '%')]
	reassembly_post_binning_units = [('No', 'No'), ('Yes', 'Yes')]

	fields = {
		'completeness_score': 'completeness score',
		'contamination_score': 'contamination score',
		'reassembly_post_binning': 'reassembly post binning',
	}

	name = 'ENA_binned_metagenome'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	completeness_score = models.CharField(max_length=120, choices=completeness_score_units, blank=False)
	contamination_score = models.CharField(max_length=120, choices=contamination_score_units, blank=False)
	reassembly_post_binning = models.CharField(max_length=120, choices=reassembly_post_binning_units, blank=False)

class GSC_MIxS_sediment(SelfDescribingModel):


	methane_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	total_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	methane= models.CharField(max_length=120, blank=True,help_text="methane (g", validators=[RegexValidator(methane_validator)])
	total_carbon= models.CharField(max_length=120, blank=True,help_text="total carb", validators=[RegexValidator(total_carbon_validator)])

	fields = {
		'methane': 'methane',
		'total_carbon': 'total carbon',
	}

	name = 'GSC_MIxS_sediment'

class GSC_MIxS_sediment_unit(SelfDescribingModel):

	methane_units = [('µM/L', 'µM/L')]
	total_carbon_units = [('µg/L', 'µg/L')]

	fields = {
		'methane': 'methane',
		'total_carbon': 'total carbon',
	}

	name = 'GSC_MIxS_sediment'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	methane = models.CharField(max_length=120, choices=methane_units, blank=False)
	total_carbon = models.CharField(max_length=120, choices=total_carbon_units, blank=False)

class GSC_MIxS_human_associated(SelfDescribingModel):

	study_completion_status_choice = [('No - adverse event', 'No - adverse event'), ('No - lost to follow up', 'No - lost to follow up'), ('No - non-compliance', 'No - non-compliance'), ('No - other', 'No - other'), ('Yes', 'Yes')]
	urine_collection_method_choice = [('catheter', 'catheter'), ('clean catch', 'clean catch')]
	host_HIV_status_choice = [('No', 'No'), ('Yes', 'Yes')]
	smoker_choice = [('ex-smoker', 'ex-smoker'), ('non-smoker', 'non-smoker'), ('smoker', 'smoker')]


	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	study_completion_status= models.CharField(max_length=120, blank=True,help_text="specificat", choices=study_completion_status_choice)
	urine_collection_method= models.CharField(max_length=120, blank=True,help_text="specificat", choices=urine_collection_method_choice)
	host_HIV_status= models.CharField(max_length=120, blank=True,help_text="HIV status", choices=host_HIV_status_choice)
	lung_pulmonary_disorder= models.CharField(max_length=120, blank=True,help_text="History of")
	lung_nose_throat_disorder= models.CharField(max_length=120, blank=True,help_text="History of")
	blood_blood_disorder= models.CharField(max_length=120, blank=True,help_text="History of")
	urine_kidney_disorder= models.CharField(max_length=120, blank=True,help_text="History of")
	urine_urogenital_tract_disorder= models.CharField(max_length=120, blank=True,help_text="History of")
	drug_usage= models.CharField(max_length=120, blank=True,help_text="any drug u")
	presence_of_pets_or_farm_animals= models.CharField(max_length=120, blank=True,help_text="specificat")
	smoker= models.CharField(max_length=120, blank=True,help_text="specificat", choices=smoker_choice)
	major_diet_change_in_last_six_months= models.CharField(max_length=120, blank=True,help_text="specificat")
	weight_loss_in_last_three_months= models.CharField(max_length=120, blank=True,help_text="specificat")
	travel_outside_the_country_in_last_six_months= models.CharField(max_length=120, blank=True,help_text="specificat")
	twin_sibling_presence= models.CharField(max_length=120, blank=True,help_text="specificat")
	amniotic_fluid_gestation_state= models.CharField(max_length=120, blank=True,help_text="specificat")
	amniotic_fluid_maternal_health_status= models.CharField(max_length=120, blank=True,help_text="specificat")
	amniotic_fluid_foetal_health_status= models.CharField(max_length=120, blank=True,help_text="specificat")
	amniotic_fluid_color= models.CharField(max_length=120, blank=True,help_text="specificat")

	fields = {
		'study_completion_status': 'study completion status',
		'urine_collection_method': 'urine/collection method',
		'host_HIV_status': 'host HIV status',
		'lung_pulmonary_disorder': 'lung/pulmonary disorder',
		'lung_nose_throat_disorder': 'lung/nose-throat disorder',
		'blood_blood_disorder': 'blood/blood disorder',
		'urine_kidney_disorder': 'urine/kidney disorder',
		'urine_urogenital_tract_disorder': 'urine/urogenital tract disorder',
		'drug_usage': 'drug usage',
		'presence_of_pets_or_farm_animals': 'presence of pets or farm animals',
		'smoker': 'smoker',
		'major_diet_change_in_last_six_months': 'major diet change in last six months',
		'weight_loss_in_last_three_months': 'weight loss in last three months',
		'travel_outside_the_country_in_last_six_months': 'travel outside the country in last six months',
		'twin_sibling_presence': 'twin sibling presence',
		'amniotic_fluid_gestation_state': 'amniotic fluid/gestation state',
		'amniotic_fluid_maternal_health_status': 'amniotic fluid/maternal health status',
		'amniotic_fluid_foetal_health_status': 'amniotic fluid/foetal health status',
		'amniotic_fluid_color': 'amniotic fluid/color',
	}

	name = 'GSC_MIxS_human_associated'

class GSC_MIxS_human_associated_unit(SelfDescribingModel):

	weight_loss_in_last_three_months_units = [('g', 'g'), ('kg', 'kg')]

	fields = {
		'weight_loss_in_last_three_months': 'weight loss in last three months',
	}

	name = 'GSC_MIxS_human_associated'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	weight_loss_in_last_three_months = models.CharField(max_length=120, choices=weight_loss_in_last_three_months_units, blank=False)

class GSC_MIxS_air(SelfDescribingModel):

	ventilation_type_choice = [('forced ventilation', 'forced ventilation'), ('mechanical ventilation', 'mechanical ventilation'), ('natural ventilation', 'natural ventilation')]

	ventilation_rate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	barometric_pressure_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	humidity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	solar_irradiance_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	wind_speed_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	carbon_dioxide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	carbon_monoxide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	oxygen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	air_particulate_matter_concentration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	ventilation_rate= models.CharField(max_length=120, blank=True,help_text="ventilatio", validators=[RegexValidator(ventilation_rate_validator)])
	ventilation_type= models.CharField(max_length=120, blank=True,help_text="The intent", choices=ventilation_type_choice)
	barometric_pressure= models.CharField(max_length=120, blank=True,help_text="force per ", validators=[RegexValidator(barometric_pressure_validator)])
	humidity= models.CharField(max_length=120, blank=True,help_text="amount of ", validators=[RegexValidator(humidity_validator)])
	pollutants= models.CharField(max_length=120, blank=True,help_text="pollutant ")
	solar_irradiance= models.CharField(max_length=120, blank=True,help_text="the amount", validators=[RegexValidator(solar_irradiance_validator)])
	wind_direction= models.CharField(max_length=120, blank=True,help_text="wind direc")
	wind_speed= models.CharField(max_length=120, blank=True,help_text="speed of w", validators=[RegexValidator(wind_speed_validator)])
	carbon_dioxide= models.CharField(max_length=120, blank=True,help_text="carbon dio", validators=[RegexValidator(carbon_dioxide_validator)])
	carbon_monoxide= models.CharField(max_length=120, blank=True,help_text="carbon mon", validators=[RegexValidator(carbon_monoxide_validator)])
	oxygen= models.CharField(max_length=120, blank=True,help_text="oxygen (ga", validators=[RegexValidator(oxygen_validator)])
	air_particulate_matter_concentration= models.CharField(max_length=120, blank=True,help_text="Concentrat", validators=[RegexValidator(air_particulate_matter_concentration_validator)])
	volatile_organic_compounds= models.CharField(max_length=120, blank=True,help_text="concentrat")

	fields = {
		'ventilation_rate': 'ventilation rate',
		'ventilation_type': 'ventilation type',
		'barometric_pressure': 'barometric pressure',
		'humidity': 'humidity',
		'pollutants': 'pollutants',
		'solar_irradiance': 'solar irradiance',
		'wind_direction': 'wind direction',
		'wind_speed': 'wind speed',
		'carbon_dioxide': 'carbon dioxide',
		'carbon_monoxide': 'carbon monoxide',
		'oxygen': 'oxygen',
		'air_particulate_matter_concentration': 'air particulate matter concentration',
		'volatile_organic_compounds': 'volatile organic compounds',
	}

	name = 'GSC_MIxS_air'

class GSC_MIxS_air_unit(SelfDescribingModel):

	ventilation_rate_units = [('L/sec', 'L/sec'), ('m3/min', 'm3/min')]
	barometric_pressure_units = [('Torr', 'Torr'), ('in. Hg', 'in. Hg'), ('millibar(hPa)', 'millibar(hPa)'), ('mm Hg', 'mm Hg')]
	humidity_units = [('%', '%'), ('g/m3', 'g/m3')]
	pollutants_units = [('M/L', 'M/L'), ('g', 'g'), ('mg/L', 'mg/L')]
	solar_irradiance_units = [('W/m2', 'W/m2')]
	wind_speed_units = [('km/h', 'km/h'), ('m/s', 'm/s')]
	carbon_dioxide_units = [('µmol/L', 'µmol/L')]
	carbon_monoxide_units = [('µM/L', 'µM/L')]
	oxygen_units = [('mg/L', 'mg/L'), ('parts/million', 'parts/million')]
	air_particulate_matter_concentration_units = [('µg/m3', 'µg/m3')]
	volatile_organic_compounds_units = [('parts/million', 'parts/million'), ('µg/m3', 'µg/m3')]

	fields = {
		'ventilation_rate': 'ventilation rate',
		'barometric_pressure': 'barometric pressure',
		'humidity': 'humidity',
		'pollutants': 'pollutants',
		'solar_irradiance': 'solar irradiance',
		'wind_speed': 'wind speed',
		'carbon_dioxide': 'carbon dioxide',
		'carbon_monoxide': 'carbon monoxide',
		'oxygen': 'oxygen',
		'air_particulate_matter_concentration': 'air particulate matter concentration',
		'volatile_organic_compounds': 'volatile organic compounds',
	}

	name = 'GSC_MIxS_air'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	ventilation_rate = models.CharField(max_length=120, choices=ventilation_rate_units, blank=False)
	barometric_pressure = models.CharField(max_length=120, choices=barometric_pressure_units, blank=False)
	humidity = models.CharField(max_length=120, choices=humidity_units, blank=False)
	pollutants = models.CharField(max_length=120, choices=pollutants_units, blank=False)
	solar_irradiance = models.CharField(max_length=120, choices=solar_irradiance_units, blank=False)
	wind_speed = models.CharField(max_length=120, choices=wind_speed_units, blank=False)
	carbon_dioxide = models.CharField(max_length=120, choices=carbon_dioxide_units, blank=False)
	carbon_monoxide = models.CharField(max_length=120, choices=carbon_monoxide_units, blank=False)
	oxygen = models.CharField(max_length=120, choices=oxygen_units, blank=False)
	air_particulate_matter_concentration = models.CharField(max_length=120, choices=air_particulate_matter_concentration_units, blank=False)
	volatile_organic_compounds = models.CharField(max_length=120, choices=volatile_organic_compounds_units, blank=False)

class GSC_MIxS_microbial_mat_biolfilm(SelfDescribingModel):


	turbidity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	turbidity= models.CharField(max_length=120, blank=True,help_text="turbidity ", validators=[RegexValidator(turbidity_validator)])

	fields = {
		'turbidity': 'turbidity',
	}

	name = 'GSC_MIxS_microbial_mat_biolfilm'

class GSC_MIxS_microbial_mat_biolfilm_unit(SelfDescribingModel):

	turbidity_units = [('FTU', 'FTU'), ('NTU', 'NTU')]

	fields = {
		'turbidity': 'turbidity',
	}

	name = 'GSC_MIxS_microbial_mat_biolfilm'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	turbidity = models.CharField(max_length=120, choices=turbidity_units, blank=False)

class GSC_MIMAGS(SelfDescribingModel):



	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)
	feature_prediction= models.CharField(max_length=120, blank=True,help_text="Method use")
	similarity_search_method= models.CharField(max_length=120, blank=True,help_text="Tool used ")
	reference_databases= models.CharField(max_length=120, blank=True,help_text="List of da")

	fields = {
		'feature_prediction': 'feature prediction',
		'similarity_search_method': 'similarity search method',
		'reference_databases': 'reference database(s)',
	}

	name = 'GSC_MIMAGS'

class GSC_MIMAGS_unit(SelfDescribingModel):


	fields = {
	}

	name = 'GSC_MIMAGS'

	sampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)
	sample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)
	sample_type = models.IntegerField(default=1)


