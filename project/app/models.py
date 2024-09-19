from django.db import models
from django.contrib.auth.models import User
from .mixs_metadata_standards import MIXS_METADATA_STANDARDS, MIXS_METADATA_STANDARDS_FULL
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models import JSONField
from django.core.validators import RegexValidator

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
                    headers = headers + f"{{title: '{k}', data: '{k}'}},\n"
                    # if class attribute (k) is of type text choices then get choices class
                        # set type: 'dropdown', source: choices class value
        else:
            for k, v in self.fields.items():
                if k not in exclude:
                    headers =   headers + f"{{title: '{k}', data: '{k}'}},\n" 

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
    }
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

class GSC_MIxS_wastewater_sludge(SelfDescribingModel):

	GSC_MIxS_wastewater_sludge_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_wastewater_sludge_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_wastewater_sludge_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_wastewater_sludge_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_wastewater_sludge_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_wastewater_sludge_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_wastewater_sludge_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_wastewater_sludge_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_wastewater_sludge_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_wastewater_sludge_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_wastewater_sludge_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_wastewater_sludge_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_wastewater_sludge_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_wastewater_sludge_depth_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_biochemical_oxygen_demand_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_chemical_oxygen_demand_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_sludge_retention_time_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_alkalinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_industrial_effluent_percent_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_pH_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_efficiency_percent_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_emulsions_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_gaseous_substances_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_inorganic_particles_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_organic_particles_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_soluble_inorganic_material_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_soluble_organic_material_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_suspended_solids_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_total_phosphate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_nitrate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_phosphate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_sodium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_wastewater_sludge_total_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_wastewater_sludge_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_wastewater_sludge_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_wastewater_sludge_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_wastewater_sludge_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_number_of_replicons_validator)])
	GSC_MIxS_wastewater_sludge_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_extrachromosomal_elements_validator)])
	GSC_MIxS_wastewater_sludge_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_estimated_size_validator)])
	GSC_MIxS_wastewater_sludge_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_wastewater_sludge_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_wastewater_sludge_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_wastewater_sludge_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_wastewater_sludge_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_library_size_validator)])
	GSC_MIxS_wastewater_sludge_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_library_reads_sequenced_validator)])
	GSC_MIxS_wastewater_sludge_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_wastewater_sludge_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_wastewater_sludge_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_wastewater_sludge_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_wastewater_sludge_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_wastewater_sludge_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_wastewater_sludge_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_wastewater_sludge_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_wastewater_sludge_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_wastewater_sludge_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_wastewater_sludge_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_wastewater_sludge_sequence_quality_check_choice)
	GSC_MIxS_wastewater_sludge_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_wastewater_sludge_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_wastewater_sludge_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_wastewater_sludge_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_wastewater_sludge_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_wastewater_sludge_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_collection_date_validator)])
	GSC_MIxS_wastewater_sludge_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_wastewater_sludge_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_wastewater_sludge_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_geographic_location_latitude_validator)])
	GSC_MIxS_wastewater_sludge_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_geographic_location_longitude_validator)])
	GSC_MIxS_wastewater_sludge_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_wastewater_sludge_depth= models.CharField(max_length=100, blank=True,help_text="The vertic", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_depth_validator)])
	GSC_MIxS_wastewater_sludge_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_wastewater_sludge_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_wastewater_sludge_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_wastewater_sludge_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_wastewater_sludge_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_wastewater_sludge_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_wastewater_sludge_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_wastewater_sludge_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_wastewater_sludge_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_wastewater_sludge_oxygenation_status_of_sample_choice)
	GSC_MIxS_wastewater_sludge_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_wastewater_sludge_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_sample_storage_duration_validator)])
	GSC_MIxS_wastewater_sludge_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_sample_storage_temperature_validator)])
	GSC_MIxS_wastewater_sludge_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_wastewater_sludge_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_wastewater_sludge_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_wastewater_sludge_biochemical_oxygen_demand= models.CharField(max_length=100, blank=True,help_text="a measure ", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_biochemical_oxygen_demand_validator)])
	GSC_MIxS_wastewater_sludge_chemical_oxygen_demand= models.CharField(max_length=100, blank=True,help_text="a measure ", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_chemical_oxygen_demand_validator)])
	GSC_MIxS_wastewater_sludge_pre_treatment= models.CharField(max_length=100, blank=True,help_text="the proces")
	GSC_MIxS_wastewater_sludge_primary_treatment= models.CharField(max_length=100, blank=True,help_text="the proces")
	GSC_MIxS_wastewater_sludge_reactor_type= models.CharField(max_length=100, blank=True,help_text="anaerobic ")
	GSC_MIxS_wastewater_sludge_secondary_treatment= models.CharField(max_length=100, blank=True,help_text="the proces")
	GSC_MIxS_wastewater_sludge_sludge_retention_time= models.CharField(max_length=100, blank=True,help_text="the time a", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_sludge_retention_time_validator)])
	GSC_MIxS_wastewater_sludge_tertiary_treatment= models.CharField(max_length=100, blank=True,help_text="the proces")
	GSC_MIxS_wastewater_sludge_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_wastewater_sludge_host_scientific_name= models.CharField(max_length=100, blank=True,help_text="Scientific")
	GSC_MIxS_wastewater_sludge_alkalinity= models.CharField(max_length=100, blank=True,help_text="alkalinity", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_alkalinity_validator)])
	GSC_MIxS_wastewater_sludge_industrial_effluent_percent= models.CharField(max_length=100, blank=True,help_text="percentage", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_industrial_effluent_percent_validator)])
	GSC_MIxS_wastewater_sludge_sewage_type= models.CharField(max_length=100, blank=True,help_text="Type of se")
	GSC_MIxS_wastewater_sludge_wastewater_type= models.CharField(max_length=100, blank=True,help_text="the origin")
	GSC_MIxS_wastewater_sludge_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_temperature_validator)])
	GSC_MIxS_wastewater_sludge_pH= models.CharField(max_length=100, blank=True,help_text="pH measure", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_pH_validator)])
	GSC_MIxS_wastewater_sludge_efficiency_percent= models.CharField(max_length=100, blank=True,help_text="percentage", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_efficiency_percent_validator)])
	GSC_MIxS_wastewater_sludge_emulsions= models.CharField(max_length=100, blank=True,help_text="amount or ", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_emulsions_validator)])
	GSC_MIxS_wastewater_sludge_gaseous_substances= models.CharField(max_length=100, blank=True,help_text="amount or ", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_gaseous_substances_validator)])
	GSC_MIxS_wastewater_sludge_inorganic_particles= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_inorganic_particles_validator)])
	GSC_MIxS_wastewater_sludge_organic_particles= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_organic_particles_validator)])
	GSC_MIxS_wastewater_sludge_soluble_inorganic_material= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_soluble_inorganic_material_validator)])
	GSC_MIxS_wastewater_sludge_soluble_organic_material= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_soluble_organic_material_validator)])
	GSC_MIxS_wastewater_sludge_suspended_solids= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_suspended_solids_validator)])
	GSC_MIxS_wastewater_sludge_total_phosphate= models.CharField(max_length=100, blank=True,help_text="total amou", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_total_phosphate_validator)])
	GSC_MIxS_wastewater_sludge_nitrate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_nitrate_validator)])
	GSC_MIxS_wastewater_sludge_phosphate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_phosphate_validator)])
	GSC_MIxS_wastewater_sludge_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_salinity_validator)])
	GSC_MIxS_wastewater_sludge_sodium= models.CharField(max_length=100, blank=True,help_text="sodium con", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_sodium_validator)])
	GSC_MIxS_wastewater_sludge_total_nitrogen= models.CharField(max_length=100, blank=True,help_text="total nitr", validators=[RegexValidator(GSC_MIxS_wastewater_sludge_total_nitrogen_validator)])
	GSC_MIxS_wastewater_sludge_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_wastewater_sludge_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_wastewater_sludge_trophic_level_choice)
	GSC_MIxS_wastewater_sludge_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_wastewater_sludge_relationship_to_oxygen_choice)
	GSC_MIxS_wastewater_sludge_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_wastewater_sludge_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_wastewater_sludge_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_wastewater_sludge_observed_biotic_relationship_choice)
	GSC_MIxS_wastewater_sludge_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_wastewater_sludge_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_wastewater_sludge_project_name': GSC_MIxS_wastewater_sludge_project_name,
		'GSC_MIxS_wastewater_sludge_experimental_factor': GSC_MIxS_wastewater_sludge_experimental_factor,
		'GSC_MIxS_wastewater_sludge_ploidy': GSC_MIxS_wastewater_sludge_ploidy,
		'GSC_MIxS_wastewater_sludge_number_of_replicons': GSC_MIxS_wastewater_sludge_number_of_replicons,
		'GSC_MIxS_wastewater_sludge_extrachromosomal_elements': GSC_MIxS_wastewater_sludge_extrachromosomal_elements,
		'GSC_MIxS_wastewater_sludge_estimated_size': GSC_MIxS_wastewater_sludge_estimated_size,
		'GSC_MIxS_wastewater_sludge_reference_for_biomaterial': GSC_MIxS_wastewater_sludge_reference_for_biomaterial,
		'GSC_MIxS_wastewater_sludge_annotation_source': GSC_MIxS_wastewater_sludge_annotation_source,
		'GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_wastewater_sludge_nucleic_acid_extraction': GSC_MIxS_wastewater_sludge_nucleic_acid_extraction,
		'GSC_MIxS_wastewater_sludge_nucleic_acid_amplification': GSC_MIxS_wastewater_sludge_nucleic_acid_amplification,
		'GSC_MIxS_wastewater_sludge_library_size': GSC_MIxS_wastewater_sludge_library_size,
		'GSC_MIxS_wastewater_sludge_library_reads_sequenced': GSC_MIxS_wastewater_sludge_library_reads_sequenced,
		'GSC_MIxS_wastewater_sludge_library_construction_method': GSC_MIxS_wastewater_sludge_library_construction_method,
		'GSC_MIxS_wastewater_sludge_library_vector': GSC_MIxS_wastewater_sludge_library_vector,
		'GSC_MIxS_wastewater_sludge_library_screening_strategy': GSC_MIxS_wastewater_sludge_library_screening_strategy,
		'GSC_MIxS_wastewater_sludge_target_gene': GSC_MIxS_wastewater_sludge_target_gene,
		'GSC_MIxS_wastewater_sludge_target_subfragment': GSC_MIxS_wastewater_sludge_target_subfragment,
		'GSC_MIxS_wastewater_sludge_pcr_primers': GSC_MIxS_wastewater_sludge_pcr_primers,
		'GSC_MIxS_wastewater_sludge_multiplex_identifiers': GSC_MIxS_wastewater_sludge_multiplex_identifiers,
		'GSC_MIxS_wastewater_sludge_adapters': GSC_MIxS_wastewater_sludge_adapters,
		'GSC_MIxS_wastewater_sludge_pcr_conditions': GSC_MIxS_wastewater_sludge_pcr_conditions,
		'GSC_MIxS_wastewater_sludge_sequencing_method': GSC_MIxS_wastewater_sludge_sequencing_method,
		'GSC_MIxS_wastewater_sludge_sequence_quality_check': GSC_MIxS_wastewater_sludge_sequence_quality_check,
		'GSC_MIxS_wastewater_sludge_chimera_check_software': GSC_MIxS_wastewater_sludge_chimera_check_software,
		'GSC_MIxS_wastewater_sludge_relevant_electronic_resources': GSC_MIxS_wastewater_sludge_relevant_electronic_resources,
		'GSC_MIxS_wastewater_sludge_relevant_standard_operating_procedures': GSC_MIxS_wastewater_sludge_relevant_standard_operating_procedures,
		'GSC_MIxS_wastewater_sludge_negative_control_type': GSC_MIxS_wastewater_sludge_negative_control_type,
		'GSC_MIxS_wastewater_sludge_positive_control_type': GSC_MIxS_wastewater_sludge_positive_control_type,
		'GSC_MIxS_wastewater_sludge_collection_date': GSC_MIxS_wastewater_sludge_collection_date,
		'GSC_MIxS_wastewater_sludge_geographic_location_country_and_or_sea': GSC_MIxS_wastewater_sludge_geographic_location_country_and_or_sea,
		'GSC_MIxS_wastewater_sludge_geographic_location_latitude': GSC_MIxS_wastewater_sludge_geographic_location_latitude,
		'GSC_MIxS_wastewater_sludge_geographic_location_longitude': GSC_MIxS_wastewater_sludge_geographic_location_longitude,
		'GSC_MIxS_wastewater_sludge_geographic_location_region_and_locality': GSC_MIxS_wastewater_sludge_geographic_location_region_and_locality,
		'GSC_MIxS_wastewater_sludge_depth': GSC_MIxS_wastewater_sludge_depth,
		'GSC_MIxS_wastewater_sludge_broad_scale_environmental_context': GSC_MIxS_wastewater_sludge_broad_scale_environmental_context,
		'GSC_MIxS_wastewater_sludge_local_environmental_context': GSC_MIxS_wastewater_sludge_local_environmental_context,
		'GSC_MIxS_wastewater_sludge_environmental_medium': GSC_MIxS_wastewater_sludge_environmental_medium,
		'GSC_MIxS_wastewater_sludge_source_material_identifiers': GSC_MIxS_wastewater_sludge_source_material_identifiers,
		'GSC_MIxS_wastewater_sludge_sample_material_processing': GSC_MIxS_wastewater_sludge_sample_material_processing,
		'GSC_MIxS_wastewater_sludge_isolation_and_growth_condition': GSC_MIxS_wastewater_sludge_isolation_and_growth_condition,
		'GSC_MIxS_wastewater_sludge_propagation': GSC_MIxS_wastewater_sludge_propagation,
		'GSC_MIxS_wastewater_sludge_amount_or_size_of_sample_collected': GSC_MIxS_wastewater_sludge_amount_or_size_of_sample_collected,
		'GSC_MIxS_wastewater_sludge_oxygenation_status_of_sample': GSC_MIxS_wastewater_sludge_oxygenation_status_of_sample,
		'GSC_MIxS_wastewater_sludge_organism_count': GSC_MIxS_wastewater_sludge_organism_count,
		'GSC_MIxS_wastewater_sludge_sample_storage_duration': GSC_MIxS_wastewater_sludge_sample_storage_duration,
		'GSC_MIxS_wastewater_sludge_sample_storage_temperature': GSC_MIxS_wastewater_sludge_sample_storage_temperature,
		'GSC_MIxS_wastewater_sludge_sample_storage_location': GSC_MIxS_wastewater_sludge_sample_storage_location,
		'GSC_MIxS_wastewater_sludge_sample_collection_device': GSC_MIxS_wastewater_sludge_sample_collection_device,
		'GSC_MIxS_wastewater_sludge_sample_collection_method': GSC_MIxS_wastewater_sludge_sample_collection_method,
		'GSC_MIxS_wastewater_sludge_biochemical_oxygen_demand': GSC_MIxS_wastewater_sludge_biochemical_oxygen_demand,
		'GSC_MIxS_wastewater_sludge_chemical_oxygen_demand': GSC_MIxS_wastewater_sludge_chemical_oxygen_demand,
		'GSC_MIxS_wastewater_sludge_pre_treatment': GSC_MIxS_wastewater_sludge_pre_treatment,
		'GSC_MIxS_wastewater_sludge_primary_treatment': GSC_MIxS_wastewater_sludge_primary_treatment,
		'GSC_MIxS_wastewater_sludge_reactor_type': GSC_MIxS_wastewater_sludge_reactor_type,
		'GSC_MIxS_wastewater_sludge_secondary_treatment': GSC_MIxS_wastewater_sludge_secondary_treatment,
		'GSC_MIxS_wastewater_sludge_sludge_retention_time': GSC_MIxS_wastewater_sludge_sludge_retention_time,
		'GSC_MIxS_wastewater_sludge_tertiary_treatment': GSC_MIxS_wastewater_sludge_tertiary_treatment,
		'GSC_MIxS_wastewater_sludge_host_disease_status': GSC_MIxS_wastewater_sludge_host_disease_status,
		'GSC_MIxS_wastewater_sludge_host_scientific_name': GSC_MIxS_wastewater_sludge_host_scientific_name,
		'GSC_MIxS_wastewater_sludge_alkalinity': GSC_MIxS_wastewater_sludge_alkalinity,
		'GSC_MIxS_wastewater_sludge_industrial_effluent_percent': GSC_MIxS_wastewater_sludge_industrial_effluent_percent,
		'GSC_MIxS_wastewater_sludge_sewage_type': GSC_MIxS_wastewater_sludge_sewage_type,
		'GSC_MIxS_wastewater_sludge_wastewater_type': GSC_MIxS_wastewater_sludge_wastewater_type,
		'GSC_MIxS_wastewater_sludge_temperature': GSC_MIxS_wastewater_sludge_temperature,
		'GSC_MIxS_wastewater_sludge_pH': GSC_MIxS_wastewater_sludge_pH,
		'GSC_MIxS_wastewater_sludge_efficiency_percent': GSC_MIxS_wastewater_sludge_efficiency_percent,
		'GSC_MIxS_wastewater_sludge_emulsions': GSC_MIxS_wastewater_sludge_emulsions,
		'GSC_MIxS_wastewater_sludge_gaseous_substances': GSC_MIxS_wastewater_sludge_gaseous_substances,
		'GSC_MIxS_wastewater_sludge_inorganic_particles': GSC_MIxS_wastewater_sludge_inorganic_particles,
		'GSC_MIxS_wastewater_sludge_organic_particles': GSC_MIxS_wastewater_sludge_organic_particles,
		'GSC_MIxS_wastewater_sludge_soluble_inorganic_material': GSC_MIxS_wastewater_sludge_soluble_inorganic_material,
		'GSC_MIxS_wastewater_sludge_soluble_organic_material': GSC_MIxS_wastewater_sludge_soluble_organic_material,
		'GSC_MIxS_wastewater_sludge_suspended_solids': GSC_MIxS_wastewater_sludge_suspended_solids,
		'GSC_MIxS_wastewater_sludge_total_phosphate': GSC_MIxS_wastewater_sludge_total_phosphate,
		'GSC_MIxS_wastewater_sludge_nitrate': GSC_MIxS_wastewater_sludge_nitrate,
		'GSC_MIxS_wastewater_sludge_phosphate': GSC_MIxS_wastewater_sludge_phosphate,
		'GSC_MIxS_wastewater_sludge_salinity': GSC_MIxS_wastewater_sludge_salinity,
		'GSC_MIxS_wastewater_sludge_sodium': GSC_MIxS_wastewater_sludge_sodium,
		'GSC_MIxS_wastewater_sludge_total_nitrogen': GSC_MIxS_wastewater_sludge_total_nitrogen,
		'GSC_MIxS_wastewater_sludge_subspecific_genetic_lineage': GSC_MIxS_wastewater_sludge_subspecific_genetic_lineage,
		'GSC_MIxS_wastewater_sludge_trophic_level': GSC_MIxS_wastewater_sludge_trophic_level,
		'GSC_MIxS_wastewater_sludge_relationship_to_oxygen': GSC_MIxS_wastewater_sludge_relationship_to_oxygen,
		'GSC_MIxS_wastewater_sludge_known_pathogenicity': GSC_MIxS_wastewater_sludge_known_pathogenicity,
		'GSC_MIxS_wastewater_sludge_encoded_traits': GSC_MIxS_wastewater_sludge_encoded_traits,
		'GSC_MIxS_wastewater_sludge_observed_biotic_relationship': GSC_MIxS_wastewater_sludge_observed_biotic_relationship,
		'GSC_MIxS_wastewater_sludge_chemical_administration': GSC_MIxS_wastewater_sludge_chemical_administration,
		'GSC_MIxS_wastewater_sludge_perturbation': GSC_MIxS_wastewater_sludge_perturbation,
	}

class GSC_MIxS_wastewater_sludge_unit(SelfDescribingModel):

	GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_wastewater_sludge_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_wastewater_sludge_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_wastewater_sludge_depth_units = [('m', 'm')]
	GSC_MIxS_wastewater_sludge_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_wastewater_sludge_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_wastewater_sludge_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_wastewater_sludge_biochemical_oxygen_demand_units = [('m', 'm'), ('g', 'g'), ('/', '/'), ('L', 'L'), (' ', ' '), ('(', '('), ('o', 'o'), ('v', 'v'), ('e', 'e'), ('r', 'r'), (' ', ' '), ('5', '5'), (' ', ' '), ('d', 'd'), ('a', 'a'), ('y', 'y'), ('s', 's'), (' ', ' '), ('a', 'a'), ('t', 't'), (' ', ' '), ('2', '2'), ('0', '0'), ('C', 'C'), (')', ')')]
	GSC_MIxS_wastewater_sludge_chemical_oxygen_demand_units = [('m', 'm'), ('g', 'g'), ('/', '/'), ('L', 'L'), (' ', ' '), ('(', '('), ('o', 'o'), ('v', 'v'), ('e', 'e'), ('r', 'r'), (' ', ' '), ('5', '5'), (' ', ' '), ('d', 'd'), ('a', 'a'), ('y', 'y'), ('s', 's'), (' ', ' '), ('a', 'a'), ('t', 't'), (' ', ' '), ('2', '2'), ('0', '0'), ('C', 'C'), (')', ')')]
	GSC_MIxS_wastewater_sludge_sludge_retention_time_units = [('days', 'days'), ('hours', 'hours'), ('minutes', 'minutes'), ('weeks', 'weeks')]
	GSC_MIxS_wastewater_sludge_alkalinity_units = [('m', 'm'), ('E', 'E'), ('q', 'q'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_wastewater_sludge_industrial_effluent_percent_units = [('%', '%')]
	GSC_MIxS_wastewater_sludge_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_wastewater_sludge_efficiency_percent_units = [('%', '%')]
	GSC_MIxS_wastewater_sludge_emulsions_units = [('g/L', 'g/L'), ('ng/L', 'ng/L'), ('µg/L', 'µg/L')]
	GSC_MIxS_wastewater_sludge_gaseous_substances_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_wastewater_sludge_inorganic_particles_units = [('mg/L', 'mg/L'), ('mol/L', 'mol/L')]
	GSC_MIxS_wastewater_sludge_organic_particles_units = [('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_wastewater_sludge_soluble_inorganic_material_units = [('g/L', 'g/L'), ('mol/L', 'mol/L'), ('parts/million', 'parts/million')]
	GSC_MIxS_wastewater_sludge_soluble_organic_material_units = [('g/L', 'g/L'), ('mol/L', 'mol/L'), ('parts/million', 'parts/million')]
	GSC_MIxS_wastewater_sludge_suspended_solids_units = [('g/L', 'g/L'), ('mol/L', 'mol/L'), ('parts/million', 'parts/million')]
	GSC_MIxS_wastewater_sludge_total_phosphate_units = [('µg/L', 'µg/L'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_wastewater_sludge_nitrate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_wastewater_sludge_phosphate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_wastewater_sludge_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]
	GSC_MIxS_wastewater_sludge_sodium_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_wastewater_sludge_total_nitrogen_units = [('µg/L', 'µg/L'), ('µmol/L', 'µmol/L')]

	fields = {
		'GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_wastewater_sludge_geographic_location_latitude_units': GSC_MIxS_wastewater_sludge_geographic_location_latitude_units,
		'GSC_MIxS_wastewater_sludge_geographic_location_longitude_units': GSC_MIxS_wastewater_sludge_geographic_location_longitude_units,
		'GSC_MIxS_wastewater_sludge_depth_units': GSC_MIxS_wastewater_sludge_depth_units,
		'GSC_MIxS_wastewater_sludge_amount_or_size_of_sample_collected_units': GSC_MIxS_wastewater_sludge_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_wastewater_sludge_sample_storage_duration_units': GSC_MIxS_wastewater_sludge_sample_storage_duration_units,
		'GSC_MIxS_wastewater_sludge_sample_storage_temperature_units': GSC_MIxS_wastewater_sludge_sample_storage_temperature_units,
		'GSC_MIxS_wastewater_sludge_biochemical_oxygen_demand_units': GSC_MIxS_wastewater_sludge_biochemical_oxygen_demand_units,
		'GSC_MIxS_wastewater_sludge_chemical_oxygen_demand_units': GSC_MIxS_wastewater_sludge_chemical_oxygen_demand_units,
		'GSC_MIxS_wastewater_sludge_sludge_retention_time_units': GSC_MIxS_wastewater_sludge_sludge_retention_time_units,
		'GSC_MIxS_wastewater_sludge_alkalinity_units': GSC_MIxS_wastewater_sludge_alkalinity_units,
		'GSC_MIxS_wastewater_sludge_industrial_effluent_percent_units': GSC_MIxS_wastewater_sludge_industrial_effluent_percent_units,
		'GSC_MIxS_wastewater_sludge_temperature_units': GSC_MIxS_wastewater_sludge_temperature_units,
		'GSC_MIxS_wastewater_sludge_efficiency_percent_units': GSC_MIxS_wastewater_sludge_efficiency_percent_units,
		'GSC_MIxS_wastewater_sludge_emulsions_units': GSC_MIxS_wastewater_sludge_emulsions_units,
		'GSC_MIxS_wastewater_sludge_gaseous_substances_units': GSC_MIxS_wastewater_sludge_gaseous_substances_units,
		'GSC_MIxS_wastewater_sludge_inorganic_particles_units': GSC_MIxS_wastewater_sludge_inorganic_particles_units,
		'GSC_MIxS_wastewater_sludge_organic_particles_units': GSC_MIxS_wastewater_sludge_organic_particles_units,
		'GSC_MIxS_wastewater_sludge_soluble_inorganic_material_units': GSC_MIxS_wastewater_sludge_soluble_inorganic_material_units,
		'GSC_MIxS_wastewater_sludge_soluble_organic_material_units': GSC_MIxS_wastewater_sludge_soluble_organic_material_units,
		'GSC_MIxS_wastewater_sludge_suspended_solids_units': GSC_MIxS_wastewater_sludge_suspended_solids_units,
		'GSC_MIxS_wastewater_sludge_total_phosphate_units': GSC_MIxS_wastewater_sludge_total_phosphate_units,
		'GSC_MIxS_wastewater_sludge_nitrate_units': GSC_MIxS_wastewater_sludge_nitrate_units,
		'GSC_MIxS_wastewater_sludge_phosphate_units': GSC_MIxS_wastewater_sludge_phosphate_units,
		'GSC_MIxS_wastewater_sludge_salinity_units': GSC_MIxS_wastewater_sludge_salinity_units,
		'GSC_MIxS_wastewater_sludge_sodium_units': GSC_MIxS_wastewater_sludge_sodium_units,
		'GSC_MIxS_wastewater_sludge_total_nitrogen_units': GSC_MIxS_wastewater_sludge_total_nitrogen_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_wastewater_sludge_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_geographic_location_latitude_units, blank=False)
	GSC_MIxS_wastewater_sludge_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_geographic_location_longitude_units, blank=False)
	GSC_MIxS_wastewater_sludge_depth = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_depth_units, blank=False)
	GSC_MIxS_wastewater_sludge_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_wastewater_sludge_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_sample_storage_duration_units, blank=False)
	GSC_MIxS_wastewater_sludge_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_sample_storage_temperature_units, blank=False)
	GSC_MIxS_wastewater_sludge_biochemical_oxygen_demand = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_biochemical_oxygen_demand_units, blank=False)
	GSC_MIxS_wastewater_sludge_chemical_oxygen_demand = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_chemical_oxygen_demand_units, blank=False)
	GSC_MIxS_wastewater_sludge_sludge_retention_time = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_sludge_retention_time_units, blank=False)
	GSC_MIxS_wastewater_sludge_alkalinity = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_alkalinity_units, blank=False)
	GSC_MIxS_wastewater_sludge_industrial_effluent_percent = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_industrial_effluent_percent_units, blank=False)
	GSC_MIxS_wastewater_sludge_temperature = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_temperature_units, blank=False)
	GSC_MIxS_wastewater_sludge_efficiency_percent = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_efficiency_percent_units, blank=False)
	GSC_MIxS_wastewater_sludge_emulsions = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_emulsions_units, blank=False)
	GSC_MIxS_wastewater_sludge_gaseous_substances = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_gaseous_substances_units, blank=False)
	GSC_MIxS_wastewater_sludge_inorganic_particles = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_inorganic_particles_units, blank=False)
	GSC_MIxS_wastewater_sludge_organic_particles = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_organic_particles_units, blank=False)
	GSC_MIxS_wastewater_sludge_soluble_inorganic_material = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_soluble_inorganic_material_units, blank=False)
	GSC_MIxS_wastewater_sludge_soluble_organic_material = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_soluble_organic_material_units, blank=False)
	GSC_MIxS_wastewater_sludge_suspended_solids = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_suspended_solids_units, blank=False)
	GSC_MIxS_wastewater_sludge_total_phosphate = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_total_phosphate_units, blank=False)
	GSC_MIxS_wastewater_sludge_nitrate = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_nitrate_units, blank=False)
	GSC_MIxS_wastewater_sludge_phosphate = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_phosphate_units, blank=False)
	GSC_MIxS_wastewater_sludge_salinity = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_salinity_units, blank=False)
	GSC_MIxS_wastewater_sludge_sodium = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_sodium_units, blank=False)
	GSC_MIxS_wastewater_sludge_total_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_wastewater_sludge_total_nitrogen_units, blank=False)

class GSC_MIxS_miscellaneous_natural_or_artificial_environment(SelfDescribingModel):

	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_miscellaneous_natural_or_artificial_environment_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_altitude_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_depth_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_elevation_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_density_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_alkalinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_water_current_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_pressure_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_pH_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_ammonium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_bromide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_calcium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_chloride_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_chlorophyll_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_diether_lipids_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_carbon_dioxide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_hydrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_inorganic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_organic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_oxygen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrite_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_matter_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_phosphate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_phospholipid_fatty_acid_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_potassium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_silicate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sodium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_number_of_replicons_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_extrachromosomal_elements_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_estimated_size_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_size_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_reads_sequenced_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_sequence_quality_check_choice)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_collection_date_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_altitude= models.CharField(max_length=100, blank=True,help_text="The altitu", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_altitude_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_latitude_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_longitude_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_depth= models.CharField(max_length=100, blank=True,help_text="The vertic", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_depth_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_elevation= models.CharField(max_length=100, blank=True,help_text="The elevat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_elevation_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_biomass= models.CharField(max_length=100, blank=True,help_text="amount of ")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_density= models.CharField(max_length=100, blank=True,help_text="density of", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_density_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_oxygenation_status_of_sample_choice)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_duration_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_temperature_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_host_scientific_name= models.CharField(max_length=100, blank=True,help_text="Scientific")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_alkalinity= models.CharField(max_length=100, blank=True,help_text="alkalinity", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_alkalinity_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_water_current= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_water_current_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_pressure= models.CharField(max_length=100, blank=True,help_text="pressure t", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_pressure_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_temperature_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_pH= models.CharField(max_length=100, blank=True,help_text="pH measure", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_pH_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_ammonium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_ammonium_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_bromide= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_bromide_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_calcium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_calcium_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_chloride= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_chloride_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_chlorophyll= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_chlorophyll_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_diether_lipids= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_diether_lipids_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_carbon_dioxide= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_carbon_dioxide_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_hydrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_hydrogen_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_inorganic_carbon= models.CharField(max_length=100, blank=True,help_text="dissolved ", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_inorganic_carbon_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_organic_nitrogen= models.CharField(max_length=100, blank=True,help_text="dissolved ", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_organic_nitrogen_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_oxygen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_oxygen_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrate_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrite= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrite_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrogen_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_carbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_carbon_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_matter= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_matter_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_nitrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_nitrogen_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_phosphate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_phosphate_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_phospholipid_fatty_acid= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_phospholipid_fatty_acid_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_potassium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_potassium_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_salinity_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_silicate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_silicate_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sodium= models.CharField(max_length=100, blank=True,help_text="sodium con", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_sodium_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfate_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfide= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfide_validator)])
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_trophic_level_choice)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_relationship_to_oxygen_choice)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_observed_biotic_relationship_choice)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_project_name': GSC_MIxS_miscellaneous_natural_or_artificial_environment_project_name,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_experimental_factor': GSC_MIxS_miscellaneous_natural_or_artificial_environment_experimental_factor,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_ploidy': GSC_MIxS_miscellaneous_natural_or_artificial_environment_ploidy,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_number_of_replicons': GSC_MIxS_miscellaneous_natural_or_artificial_environment_number_of_replicons,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_extrachromosomal_elements': GSC_MIxS_miscellaneous_natural_or_artificial_environment_extrachromosomal_elements,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_estimated_size': GSC_MIxS_miscellaneous_natural_or_artificial_environment_estimated_size,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_reference_for_biomaterial': GSC_MIxS_miscellaneous_natural_or_artificial_environment_reference_for_biomaterial,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_annotation_source': GSC_MIxS_miscellaneous_natural_or_artificial_environment_annotation_source,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_nucleic_acid_extraction': GSC_MIxS_miscellaneous_natural_or_artificial_environment_nucleic_acid_extraction,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_nucleic_acid_amplification': GSC_MIxS_miscellaneous_natural_or_artificial_environment_nucleic_acid_amplification,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_size': GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_size,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_reads_sequenced': GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_reads_sequenced,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_construction_method': GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_construction_method,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_vector': GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_vector,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_screening_strategy': GSC_MIxS_miscellaneous_natural_or_artificial_environment_library_screening_strategy,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_target_gene': GSC_MIxS_miscellaneous_natural_or_artificial_environment_target_gene,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_target_subfragment': GSC_MIxS_miscellaneous_natural_or_artificial_environment_target_subfragment,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_pcr_primers': GSC_MIxS_miscellaneous_natural_or_artificial_environment_pcr_primers,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_multiplex_identifiers': GSC_MIxS_miscellaneous_natural_or_artificial_environment_multiplex_identifiers,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_adapters': GSC_MIxS_miscellaneous_natural_or_artificial_environment_adapters,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_pcr_conditions': GSC_MIxS_miscellaneous_natural_or_artificial_environment_pcr_conditions,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sequencing_method': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sequencing_method,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sequence_quality_check': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sequence_quality_check,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_chimera_check_software': GSC_MIxS_miscellaneous_natural_or_artificial_environment_chimera_check_software,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_relevant_electronic_resources': GSC_MIxS_miscellaneous_natural_or_artificial_environment_relevant_electronic_resources,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_relevant_standard_operating_procedures': GSC_MIxS_miscellaneous_natural_or_artificial_environment_relevant_standard_operating_procedures,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_negative_control_type': GSC_MIxS_miscellaneous_natural_or_artificial_environment_negative_control_type,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_positive_control_type': GSC_MIxS_miscellaneous_natural_or_artificial_environment_positive_control_type,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_collection_date': GSC_MIxS_miscellaneous_natural_or_artificial_environment_collection_date,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_altitude': GSC_MIxS_miscellaneous_natural_or_artificial_environment_altitude,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_country_and_or_sea': GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_country_and_or_sea,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_latitude': GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_latitude,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_longitude': GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_longitude,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_region_and_locality': GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_region_and_locality,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_depth': GSC_MIxS_miscellaneous_natural_or_artificial_environment_depth,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_broad_scale_environmental_context': GSC_MIxS_miscellaneous_natural_or_artificial_environment_broad_scale_environmental_context,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_local_environmental_context': GSC_MIxS_miscellaneous_natural_or_artificial_environment_local_environmental_context,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_environmental_medium': GSC_MIxS_miscellaneous_natural_or_artificial_environment_environmental_medium,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_elevation': GSC_MIxS_miscellaneous_natural_or_artificial_environment_elevation,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_source_material_identifiers': GSC_MIxS_miscellaneous_natural_or_artificial_environment_source_material_identifiers,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_material_processing': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_material_processing,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_isolation_and_growth_condition': GSC_MIxS_miscellaneous_natural_or_artificial_environment_isolation_and_growth_condition,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_propagation': GSC_MIxS_miscellaneous_natural_or_artificial_environment_propagation,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_amount_or_size_of_sample_collected': GSC_MIxS_miscellaneous_natural_or_artificial_environment_amount_or_size_of_sample_collected,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_biomass': GSC_MIxS_miscellaneous_natural_or_artificial_environment_biomass,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_density': GSC_MIxS_miscellaneous_natural_or_artificial_environment_density,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_oxygenation_status_of_sample': GSC_MIxS_miscellaneous_natural_or_artificial_environment_oxygenation_status_of_sample,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_organism_count': GSC_MIxS_miscellaneous_natural_or_artificial_environment_organism_count,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_duration': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_duration,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_temperature': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_temperature,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_location': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_location,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_collection_device': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_collection_device,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_collection_method': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_collection_method,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_host_disease_status': GSC_MIxS_miscellaneous_natural_or_artificial_environment_host_disease_status,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_host_scientific_name': GSC_MIxS_miscellaneous_natural_or_artificial_environment_host_scientific_name,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_alkalinity': GSC_MIxS_miscellaneous_natural_or_artificial_environment_alkalinity,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_water_current': GSC_MIxS_miscellaneous_natural_or_artificial_environment_water_current,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_pressure': GSC_MIxS_miscellaneous_natural_or_artificial_environment_pressure,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_temperature': GSC_MIxS_miscellaneous_natural_or_artificial_environment_temperature,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_pH': GSC_MIxS_miscellaneous_natural_or_artificial_environment_pH,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_ammonium': GSC_MIxS_miscellaneous_natural_or_artificial_environment_ammonium,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_bromide': GSC_MIxS_miscellaneous_natural_or_artificial_environment_bromide,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_calcium': GSC_MIxS_miscellaneous_natural_or_artificial_environment_calcium,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_chloride': GSC_MIxS_miscellaneous_natural_or_artificial_environment_chloride,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_chlorophyll': GSC_MIxS_miscellaneous_natural_or_artificial_environment_chlorophyll,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_diether_lipids': GSC_MIxS_miscellaneous_natural_or_artificial_environment_diether_lipids,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_carbon_dioxide': GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_carbon_dioxide,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_hydrogen': GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_hydrogen,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_inorganic_carbon': GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_inorganic_carbon,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_organic_nitrogen': GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_organic_nitrogen,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_oxygen': GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_oxygen,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrate': GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrate,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrite': GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrite,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrogen': GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrogen,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_carbon': GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_carbon,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_matter': GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_matter,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_nitrogen': GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_nitrogen,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_phosphate': GSC_MIxS_miscellaneous_natural_or_artificial_environment_phosphate,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_phospholipid_fatty_acid': GSC_MIxS_miscellaneous_natural_or_artificial_environment_phospholipid_fatty_acid,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_potassium': GSC_MIxS_miscellaneous_natural_or_artificial_environment_potassium,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_salinity': GSC_MIxS_miscellaneous_natural_or_artificial_environment_salinity,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_silicate': GSC_MIxS_miscellaneous_natural_or_artificial_environment_silicate,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sodium': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sodium,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfate': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfate,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfide': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfide,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_subspecific_genetic_lineage': GSC_MIxS_miscellaneous_natural_or_artificial_environment_subspecific_genetic_lineage,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_trophic_level': GSC_MIxS_miscellaneous_natural_or_artificial_environment_trophic_level,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_relationship_to_oxygen': GSC_MIxS_miscellaneous_natural_or_artificial_environment_relationship_to_oxygen,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_known_pathogenicity': GSC_MIxS_miscellaneous_natural_or_artificial_environment_known_pathogenicity,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_encoded_traits': GSC_MIxS_miscellaneous_natural_or_artificial_environment_encoded_traits,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_observed_biotic_relationship': GSC_MIxS_miscellaneous_natural_or_artificial_environment_observed_biotic_relationship,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_chemical_administration': GSC_MIxS_miscellaneous_natural_or_artificial_environment_chemical_administration,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_perturbation': GSC_MIxS_miscellaneous_natural_or_artificial_environment_perturbation,
	}

class GSC_MIxS_miscellaneous_natural_or_artificial_environment_unit(SelfDescribingModel):

	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_altitude_units = [('m', 'm')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_depth_units = [('m', 'm')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_elevation_units = [('m', 'm')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_biomass_units = [('g', 'g'), ('kg', 'kg'), ('t', 't')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_density_units = [('g', 'g'), ('/', '/'), ('m', 'm'), ('3', '3')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_alkalinity_units = [('m', 'm'), ('E', 'E'), ('q', 'q'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_water_current_units = [('knot', 'knot'), ('m3/s', 'm3/s')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_pressure_units = [('atm', 'atm'), ('bar', 'bar')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_ammonium_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_bromide_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_calcium_units = [('mg/L', 'mg/L'), ('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_chloride_units = [('m', 'm'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_chlorophyll_units = [('mg/m3', 'mg/m3'), ('µg/L', 'µg/L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_diether_lipids_units = [('n', 'n'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_carbon_dioxide_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_hydrogen_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_inorganic_carbon_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_organic_nitrogen_units = [('mg/L', 'mg/L'), ('µg/L', 'µg/L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_oxygen_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('k', 'k'), ('g', 'g')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrite_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrogen_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_carbon_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_matter_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_nitrogen_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_phosphate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_phospholipid_fatty_acid_units = [('mol/L', 'mol/L'), ('mol/g', 'mol/g')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_potassium_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_silicate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sodium_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfate_units = [('mg/L', 'mg/L'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfide_units = [('mg/L', 'mg/L'), ('µmol/L', 'µmol/L')]

	fields = {
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_altitude_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_altitude_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_latitude_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_latitude_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_longitude_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_longitude_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_depth_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_depth_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_elevation_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_elevation_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_amount_or_size_of_sample_collected_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_biomass_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_biomass_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_density_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_density_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_duration_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_duration_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_temperature_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_temperature_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_alkalinity_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_alkalinity_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_water_current_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_water_current_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_pressure_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_pressure_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_temperature_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_temperature_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_ammonium_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_ammonium_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_bromide_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_bromide_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_calcium_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_calcium_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_chloride_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_chloride_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_chlorophyll_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_chlorophyll_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_diether_lipids_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_diether_lipids_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_carbon_dioxide_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_carbon_dioxide_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_hydrogen_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_hydrogen_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_inorganic_carbon_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_inorganic_carbon_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_organic_nitrogen_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_organic_nitrogen_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_oxygen_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_oxygen_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrate_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrate_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrite_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrite_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrogen_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrogen_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_carbon_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_carbon_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_matter_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_matter_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_nitrogen_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_nitrogen_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_phosphate_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_phosphate_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_phospholipid_fatty_acid_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_phospholipid_fatty_acid_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_potassium_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_potassium_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_salinity_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_salinity_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_silicate_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_silicate_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sodium_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sodium_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfate_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfate_units,
		'GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfide_units': GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfide_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_altitude = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_altitude_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_latitude_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_geographic_location_longitude_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_depth = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_depth_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_elevation = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_elevation_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_biomass = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_biomass_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_density = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_density_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_duration_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_sample_storage_temperature_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_alkalinity = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_alkalinity_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_water_current = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_water_current_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_pressure = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_pressure_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_temperature = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_temperature_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_ammonium = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_ammonium_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_bromide = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_bromide_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_calcium = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_calcium_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_chloride = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_chloride_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_chlorophyll = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_chlorophyll_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_diether_lipids = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_diether_lipids_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_carbon_dioxide = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_carbon_dioxide_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_hydrogen = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_hydrogen_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_inorganic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_inorganic_carbon_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_organic_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_organic_nitrogen_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_oxygen = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_dissolved_oxygen_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrate = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrate_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrite = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrite_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_nitrogen_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_carbon_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_matter = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_matter_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_organic_nitrogen_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_phosphate = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_phosphate_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_phospholipid_fatty_acid = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_phospholipid_fatty_acid_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_potassium = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_potassium_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_salinity = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_salinity_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_silicate = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_silicate_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sodium = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_sodium_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfate = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfate_units, blank=False)
	GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfide = models.CharField(max_length=100, choices=GSC_MIxS_miscellaneous_natural_or_artificial_environment_sulfide_units, blank=False)

class GSC_MIxS_human_skin(SelfDescribingModel):

	GSC_MIxS_human_skin_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_human_skin_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_human_skin_medical_history_performed_choice = [('No', 'No'), ('Yes', 'Yes')]
	GSC_MIxS_human_skin_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_human_skin_IHMC_medication_code_choice = [('01=1=Analgesics/NSAIDS', '01=1=Analgesics/NSAIDS'), ('02=2=Anesthetics', '02=2=Anesthetics'), ('03=3=Antacids/H2 antagonists', '03=3=Antacids/H2 antagonists'), ('04=4=Anti-acne', '04=4=Anti-acne'), ('05=5=Anti-asthma/bronchodilators', '05=5=Anti-asthma/bronchodilators'), ('06=6=Anti-cholesterol/Anti-hyperlipidemic', '06=6=Anti-cholesterol/Anti-hyperlipidemic'), ('07=7=Anti-coagulants', '07=7=Anti-coagulants'), ('08=8=Antibiotics/(anti)-infectives, parasitics, microbials', '08=8=Antibiotics/(anti)-infectives, parasitics, microbials'), ('09=9=Antidepressants/mood-altering drugs', '09=9=Antidepressants/mood-altering drugs'), ('10=10=Antihistamines/ Decongestants', '10=10=Antihistamines/ Decongestants'), ('11=11=Antihypertensives', '11=11=Antihypertensives'), ('12=12=Cardiovascular, other than hyperlipidemic/HTN', '12=12=Cardiovascular, other than hyperlipidemic/HTN'), ('13=13=Contraceptives (oral, implant, injectable)', '13=13=Contraceptives (oral, implant, injectable)'), ('14=14=Emergency/support medications', '14=14=Emergency/support medications'), ('15=15=Endocrine/Metabolic agents', '15=15=Endocrine/Metabolic agents'), ('16=16=GI meds (anti-diarrheal, emetic, spasmodics)', '16=16=GI meds (anti-diarrheal, emetic, spasmodics)'), ('17=17=Herbal/homeopathic products', '17=17=Herbal/homeopathic products'), ('18=18=Hormones/steroids', '18=18=Hormones/steroids'), ('19=19=OTC cold & flu', '19=19=OTC cold & flu'), ('20=20=Vaccine prophylaxis', '20=20=Vaccine prophylaxis'), ('21=21=Vitamins, minerals, food supplements', '21=21=Vitamins, minerals, food supplements'), ('99=99=Other', '99=99=Other')]
	GSC_MIxS_human_skin_host_occupation_choice = [('01=01 Accounting/Finance', '01=01 Accounting/Finance'), ('02=02 Advertising/Public Relations', '02=02 Advertising/Public Relations'), ('03=03 Arts/Entertainment/Publishing', '03=03 Arts/Entertainment/Publishing'), ('04=04 Automotive', '04=04 Automotive'), ('05=05 Banking/ Mortgage', '05=05 Banking/ Mortgage'), ('06=06 Biotech', '06=06 Biotech'), ('07=07 Broadcast/Journalism', '07=07 Broadcast/Journalism'), ('08=08 Business Development', '08=08 Business Development'), ('09=09 Clerical/Administrative', '09=09 Clerical/Administrative'), ('10=10 Construction/Trades', '10=10 Construction/Trades'), ('11=11 Consultant', '11=11 Consultant'), ('12=12 Customer Services', '12=12 Customer Services'), ('13=13 Design', '13=13 Design'), ('14=14 Education', '14=14 Education'), ('15=15 Engineering', '15=15 Engineering'), ('16=16 Entry Level', '16=16 Entry Level'), ('17=17 Executive', '17=17 Executive'), ('18=18 Food Service', '18=18 Food Service'), ('19=19 Government', '19=19 Government'), ('20=20 Grocery', '20=20 Grocery'), ('21=21 Healthcare', '21=21 Healthcare'), ('22=22 Hospitality', '22=22 Hospitality'), ('23=23 Human Resources', '23=23 Human Resources'), ('24=24 Information Technology', '24=24 Information Technology'), ('25=25 Insurance', '25=25 Insurance'), ('26=26 Law/Legal', '26=26 Law/Legal'), ('27=27 Management', '27=27 Management'), ('28=28 Manufacturing', '28=28 Manufacturing'), ('29=29 Marketing', '29=29 Marketing'), ('30=30 Pharmaceutical', '30=30 Pharmaceutical'), ('31=31 Professional Services', '31=31 Professional Services'), ('32=32 Purchasing', '32=32 Purchasing'), ('33=33 Quality Assurance (QA)', '33=33 Quality Assurance (QA)'), ('34=34 Research', '34=34 Research'), ('35=35 Restaurant', '35=35 Restaurant'), ('36=36 Retail', '36=36 Retail'), ('37=37 Sales', '37=37 Sales'), ('38=38 Science', '38=38 Science'), ('39=39 Security/Law Enforcement', '39=39 Security/Law Enforcement'), ('40=40 Shipping/Distribution', '40=40 Shipping/Distribution'), ('41=41 Strategy', '41=41 Strategy'), ('42=42 Student', '42=42 Student'), ('43=43 Telecommunications', '43=43 Telecommunications'), ('44=44 Training', '44=44 Training'), ('45=45 Transportation', '45=45 Transportation'), ('46=46 Warehouse', '46=46 Warehouse'), ('47=47 Other', '47=47 Other'), ('99=99 Unknown/Refused', '99=99 Unknown/Refused')]
	GSC_MIxS_human_skin_host_sex_choice = [('female', 'female'), ('hermaphrodite', 'hermaphrodite'), ('male', 'male'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('neuter', 'neuter'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('other', 'other'), ('restricted access', 'restricted access')]
	GSC_MIxS_human_skin_dominant_hand_choice = [('ambidextrous', 'ambidextrous'), ('left', 'left'), ('right', 'right')]
	GSC_MIxS_human_skin_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_human_skin_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_human_skin_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_human_skin_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_skin_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_skin_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_skin_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_skin_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_skin_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_skin_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_skin_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_skin_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_skin_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_skin_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_skin_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_skin_host_age_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_skin_host_height_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_skin_host_body_mass_index_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_skin_host_total_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_skin_host_body_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_skin_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_skin_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_skin_time_since_last_wash_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_skin_host_pulse_validator = "[+-]?[0-9]+"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_human_skin_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_human_skin_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_human_skin_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_human_skin_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_human_skin_number_of_replicons_validator)])
	GSC_MIxS_human_skin_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_human_skin_extrachromosomal_elements_validator)])
	GSC_MIxS_human_skin_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_human_skin_estimated_size_validator)])
	GSC_MIxS_human_skin_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_human_skin_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_human_skin_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_human_skin_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_human_skin_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_human_skin_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_human_skin_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_human_skin_library_size_validator)])
	GSC_MIxS_human_skin_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_human_skin_library_reads_sequenced_validator)])
	GSC_MIxS_human_skin_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_human_skin_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_human_skin_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_human_skin_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_human_skin_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_human_skin_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_human_skin_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_human_skin_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_human_skin_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_human_skin_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_human_skin_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_human_skin_sequence_quality_check_choice)
	GSC_MIxS_human_skin_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_human_skin_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_human_skin_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_human_skin_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_human_skin_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_human_skin_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_human_skin_collection_date_validator)])
	GSC_MIxS_human_skin_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_human_skin_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_human_skin_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_human_skin_geographic_location_latitude_validator)])
	GSC_MIxS_human_skin_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_human_skin_geographic_location_longitude_validator)])
	GSC_MIxS_human_skin_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_human_skin_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_skin_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_skin_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_skin_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_human_skin_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_human_skin_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_human_skin_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_human_skin_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_human_skin_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_human_skin_host_body_product= models.CharField(max_length=100, blank=True,help_text="substance ")
	GSC_MIxS_human_skin_medical_history_performed= models.CharField(max_length=100, blank=True,help_text="whether fu", choices=GSC_MIxS_human_skin_medical_history_performed_choice)
	GSC_MIxS_human_skin_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_human_skin_oxygenation_status_of_sample_choice)
	GSC_MIxS_human_skin_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_human_skin_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_human_skin_sample_storage_duration_validator)])
	GSC_MIxS_human_skin_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_human_skin_sample_storage_temperature_validator)])
	GSC_MIxS_human_skin_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_human_skin_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_human_skin_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_human_skin_dermatology_disorder= models.CharField(max_length=100, blank=True,help_text="History of")
	GSC_MIxS_human_skin_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_human_skin_host_subject_id= models.CharField(max_length=100, blank=True,help_text="a unique i")
	GSC_MIxS_human_skin_IHMC_medication_code= models.CharField(max_length=100, blank=True,help_text="can includ", choices=GSC_MIxS_human_skin_IHMC_medication_code_choice)
	GSC_MIxS_human_skin_host_age= models.CharField(max_length=100, blank=True,help_text="age of hos", validators=[RegexValidator(GSC_MIxS_human_skin_host_age_validator)])
	GSC_MIxS_human_skin_host_body_site= models.CharField(max_length=100, blank=True,help_text="name of bo")
	GSC_MIxS_human_skin_host_height= models.CharField(max_length=100, blank=True,help_text="the height", validators=[RegexValidator(GSC_MIxS_human_skin_host_height_validator)])
	GSC_MIxS_human_skin_host_body_mass_index= models.CharField(max_length=100, blank=True,help_text="body mass ", validators=[RegexValidator(GSC_MIxS_human_skin_host_body_mass_index_validator)])
	GSC_MIxS_human_skin_ethnicity= models.CharField(max_length=100, blank=True,help_text="A category")
	GSC_MIxS_human_skin_host_occupation= models.CharField(max_length=100, blank=True,help_text="most frequ", choices=GSC_MIxS_human_skin_host_occupation_choice)
	GSC_MIxS_human_skin_host_total_mass= models.CharField(max_length=100, blank=True,help_text="total mass", validators=[RegexValidator(GSC_MIxS_human_skin_host_total_mass_validator)])
	GSC_MIxS_human_skin_host_phenotype= models.CharField(max_length=100, blank=True,help_text="phenotype ")
	GSC_MIxS_human_skin_host_body_temperature= models.CharField(max_length=100, blank=True,help_text="core body ", validators=[RegexValidator(GSC_MIxS_human_skin_host_body_temperature_validator)])
	GSC_MIxS_human_skin_host_sex= models.CharField(max_length=100, blank=True,help_text="Gender or ", choices=GSC_MIxS_human_skin_host_sex_choice)
	GSC_MIxS_human_skin_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_human_skin_temperature_validator)])
	GSC_MIxS_human_skin_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_human_skin_salinity_validator)])
	GSC_MIxS_human_skin_time_since_last_wash= models.CharField(max_length=100, blank=True,help_text="specificat", validators=[RegexValidator(GSC_MIxS_human_skin_time_since_last_wash_validator)])
	GSC_MIxS_human_skin_dominant_hand= models.CharField(max_length=100, blank=True,help_text="dominant h", choices=GSC_MIxS_human_skin_dominant_hand_choice)
	GSC_MIxS_human_skin_host_diet= models.CharField(max_length=100, blank=True,help_text="type of di")
	GSC_MIxS_human_skin_host_last_meal= models.CharField(max_length=100, blank=True,help_text="content of")
	GSC_MIxS_human_skin_host_family_relationship= models.CharField(max_length=100, blank=True,help_text="relationsh")
	GSC_MIxS_human_skin_host_genotype= models.CharField(max_length=100, blank=True,help_text="observed g")
	GSC_MIxS_human_skin_host_pulse= models.CharField(max_length=100, blank=True,help_text="resting pu", validators=[RegexValidator(GSC_MIxS_human_skin_host_pulse_validator)])
	GSC_MIxS_human_skin_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_human_skin_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_human_skin_trophic_level_choice)
	GSC_MIxS_human_skin_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_human_skin_relationship_to_oxygen_choice)
	GSC_MIxS_human_skin_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_human_skin_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_human_skin_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_human_skin_observed_biotic_relationship_choice)
	GSC_MIxS_human_skin_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_human_skin_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_human_skin_project_name': GSC_MIxS_human_skin_project_name,
		'GSC_MIxS_human_skin_experimental_factor': GSC_MIxS_human_skin_experimental_factor,
		'GSC_MIxS_human_skin_ploidy': GSC_MIxS_human_skin_ploidy,
		'GSC_MIxS_human_skin_number_of_replicons': GSC_MIxS_human_skin_number_of_replicons,
		'GSC_MIxS_human_skin_extrachromosomal_elements': GSC_MIxS_human_skin_extrachromosomal_elements,
		'GSC_MIxS_human_skin_estimated_size': GSC_MIxS_human_skin_estimated_size,
		'GSC_MIxS_human_skin_reference_for_biomaterial': GSC_MIxS_human_skin_reference_for_biomaterial,
		'GSC_MIxS_human_skin_annotation_source': GSC_MIxS_human_skin_annotation_source,
		'GSC_MIxS_human_skin_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_human_skin_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_human_skin_nucleic_acid_extraction': GSC_MIxS_human_skin_nucleic_acid_extraction,
		'GSC_MIxS_human_skin_nucleic_acid_amplification': GSC_MIxS_human_skin_nucleic_acid_amplification,
		'GSC_MIxS_human_skin_library_size': GSC_MIxS_human_skin_library_size,
		'GSC_MIxS_human_skin_library_reads_sequenced': GSC_MIxS_human_skin_library_reads_sequenced,
		'GSC_MIxS_human_skin_library_construction_method': GSC_MIxS_human_skin_library_construction_method,
		'GSC_MIxS_human_skin_library_vector': GSC_MIxS_human_skin_library_vector,
		'GSC_MIxS_human_skin_library_screening_strategy': GSC_MIxS_human_skin_library_screening_strategy,
		'GSC_MIxS_human_skin_target_gene': GSC_MIxS_human_skin_target_gene,
		'GSC_MIxS_human_skin_target_subfragment': GSC_MIxS_human_skin_target_subfragment,
		'GSC_MIxS_human_skin_pcr_primers': GSC_MIxS_human_skin_pcr_primers,
		'GSC_MIxS_human_skin_multiplex_identifiers': GSC_MIxS_human_skin_multiplex_identifiers,
		'GSC_MIxS_human_skin_adapters': GSC_MIxS_human_skin_adapters,
		'GSC_MIxS_human_skin_pcr_conditions': GSC_MIxS_human_skin_pcr_conditions,
		'GSC_MIxS_human_skin_sequencing_method': GSC_MIxS_human_skin_sequencing_method,
		'GSC_MIxS_human_skin_sequence_quality_check': GSC_MIxS_human_skin_sequence_quality_check,
		'GSC_MIxS_human_skin_chimera_check_software': GSC_MIxS_human_skin_chimera_check_software,
		'GSC_MIxS_human_skin_relevant_electronic_resources': GSC_MIxS_human_skin_relevant_electronic_resources,
		'GSC_MIxS_human_skin_relevant_standard_operating_procedures': GSC_MIxS_human_skin_relevant_standard_operating_procedures,
		'GSC_MIxS_human_skin_negative_control_type': GSC_MIxS_human_skin_negative_control_type,
		'GSC_MIxS_human_skin_positive_control_type': GSC_MIxS_human_skin_positive_control_type,
		'GSC_MIxS_human_skin_collection_date': GSC_MIxS_human_skin_collection_date,
		'GSC_MIxS_human_skin_geographic_location_country_and_or_sea': GSC_MIxS_human_skin_geographic_location_country_and_or_sea,
		'GSC_MIxS_human_skin_geographic_location_latitude': GSC_MIxS_human_skin_geographic_location_latitude,
		'GSC_MIxS_human_skin_geographic_location_longitude': GSC_MIxS_human_skin_geographic_location_longitude,
		'GSC_MIxS_human_skin_geographic_location_region_and_locality': GSC_MIxS_human_skin_geographic_location_region_and_locality,
		'GSC_MIxS_human_skin_broad_scale_environmental_context': GSC_MIxS_human_skin_broad_scale_environmental_context,
		'GSC_MIxS_human_skin_local_environmental_context': GSC_MIxS_human_skin_local_environmental_context,
		'GSC_MIxS_human_skin_environmental_medium': GSC_MIxS_human_skin_environmental_medium,
		'GSC_MIxS_human_skin_source_material_identifiers': GSC_MIxS_human_skin_source_material_identifiers,
		'GSC_MIxS_human_skin_sample_material_processing': GSC_MIxS_human_skin_sample_material_processing,
		'GSC_MIxS_human_skin_isolation_and_growth_condition': GSC_MIxS_human_skin_isolation_and_growth_condition,
		'GSC_MIxS_human_skin_propagation': GSC_MIxS_human_skin_propagation,
		'GSC_MIxS_human_skin_amount_or_size_of_sample_collected': GSC_MIxS_human_skin_amount_or_size_of_sample_collected,
		'GSC_MIxS_human_skin_host_body_product': GSC_MIxS_human_skin_host_body_product,
		'GSC_MIxS_human_skin_medical_history_performed': GSC_MIxS_human_skin_medical_history_performed,
		'GSC_MIxS_human_skin_oxygenation_status_of_sample': GSC_MIxS_human_skin_oxygenation_status_of_sample,
		'GSC_MIxS_human_skin_organism_count': GSC_MIxS_human_skin_organism_count,
		'GSC_MIxS_human_skin_sample_storage_duration': GSC_MIxS_human_skin_sample_storage_duration,
		'GSC_MIxS_human_skin_sample_storage_temperature': GSC_MIxS_human_skin_sample_storage_temperature,
		'GSC_MIxS_human_skin_sample_storage_location': GSC_MIxS_human_skin_sample_storage_location,
		'GSC_MIxS_human_skin_sample_collection_device': GSC_MIxS_human_skin_sample_collection_device,
		'GSC_MIxS_human_skin_sample_collection_method': GSC_MIxS_human_skin_sample_collection_method,
		'GSC_MIxS_human_skin_dermatology_disorder': GSC_MIxS_human_skin_dermatology_disorder,
		'GSC_MIxS_human_skin_host_disease_status': GSC_MIxS_human_skin_host_disease_status,
		'GSC_MIxS_human_skin_host_subject_id': GSC_MIxS_human_skin_host_subject_id,
		'GSC_MIxS_human_skin_IHMC_medication_code': GSC_MIxS_human_skin_IHMC_medication_code,
		'GSC_MIxS_human_skin_host_age': GSC_MIxS_human_skin_host_age,
		'GSC_MIxS_human_skin_host_body_site': GSC_MIxS_human_skin_host_body_site,
		'GSC_MIxS_human_skin_host_height': GSC_MIxS_human_skin_host_height,
		'GSC_MIxS_human_skin_host_body_mass_index': GSC_MIxS_human_skin_host_body_mass_index,
		'GSC_MIxS_human_skin_ethnicity': GSC_MIxS_human_skin_ethnicity,
		'GSC_MIxS_human_skin_host_occupation': GSC_MIxS_human_skin_host_occupation,
		'GSC_MIxS_human_skin_host_total_mass': GSC_MIxS_human_skin_host_total_mass,
		'GSC_MIxS_human_skin_host_phenotype': GSC_MIxS_human_skin_host_phenotype,
		'GSC_MIxS_human_skin_host_body_temperature': GSC_MIxS_human_skin_host_body_temperature,
		'GSC_MIxS_human_skin_host_sex': GSC_MIxS_human_skin_host_sex,
		'GSC_MIxS_human_skin_temperature': GSC_MIxS_human_skin_temperature,
		'GSC_MIxS_human_skin_salinity': GSC_MIxS_human_skin_salinity,
		'GSC_MIxS_human_skin_time_since_last_wash': GSC_MIxS_human_skin_time_since_last_wash,
		'GSC_MIxS_human_skin_dominant_hand': GSC_MIxS_human_skin_dominant_hand,
		'GSC_MIxS_human_skin_host_diet': GSC_MIxS_human_skin_host_diet,
		'GSC_MIxS_human_skin_host_last_meal': GSC_MIxS_human_skin_host_last_meal,
		'GSC_MIxS_human_skin_host_family_relationship': GSC_MIxS_human_skin_host_family_relationship,
		'GSC_MIxS_human_skin_host_genotype': GSC_MIxS_human_skin_host_genotype,
		'GSC_MIxS_human_skin_host_pulse': GSC_MIxS_human_skin_host_pulse,
		'GSC_MIxS_human_skin_subspecific_genetic_lineage': GSC_MIxS_human_skin_subspecific_genetic_lineage,
		'GSC_MIxS_human_skin_trophic_level': GSC_MIxS_human_skin_trophic_level,
		'GSC_MIxS_human_skin_relationship_to_oxygen': GSC_MIxS_human_skin_relationship_to_oxygen,
		'GSC_MIxS_human_skin_known_pathogenicity': GSC_MIxS_human_skin_known_pathogenicity,
		'GSC_MIxS_human_skin_encoded_traits': GSC_MIxS_human_skin_encoded_traits,
		'GSC_MIxS_human_skin_observed_biotic_relationship': GSC_MIxS_human_skin_observed_biotic_relationship,
		'GSC_MIxS_human_skin_chemical_administration': GSC_MIxS_human_skin_chemical_administration,
		'GSC_MIxS_human_skin_perturbation': GSC_MIxS_human_skin_perturbation,
	}

class GSC_MIxS_human_skin_unit(SelfDescribingModel):

	GSC_MIxS_human_skin_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_human_skin_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_human_skin_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_human_skin_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_human_skin_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_human_skin_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_human_skin_host_age_units = [('centuries', 'centuries'), ('days', 'days'), ('decades', 'decades'), ('hours', 'hours'), ('minutes', 'minutes'), ('months', 'months'), ('seconds', 'seconds'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_human_skin_host_height_units = [('cm', 'cm'), ('m', 'm'), ('mm', 'mm')]
	GSC_MIxS_human_skin_host_body_mass_index_units = [('k', 'k'), ('g', 'g'), ('/', '/'), ('m', 'm'), ('2', '2')]
	GSC_MIxS_human_skin_host_total_mass_units = [('g', 'g'), ('kg', 'kg')]
	GSC_MIxS_human_skin_host_body_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_human_skin_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_human_skin_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]
	GSC_MIxS_human_skin_time_since_last_wash_units = [('hours', 'hours'), ('minutes', 'minutes')]
	GSC_MIxS_human_skin_host_pulse_units = [('b', 'b'), ('p', 'p'), ('m', 'm')]

	fields = {
		'GSC_MIxS_human_skin_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_human_skin_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_human_skin_geographic_location_latitude_units': GSC_MIxS_human_skin_geographic_location_latitude_units,
		'GSC_MIxS_human_skin_geographic_location_longitude_units': GSC_MIxS_human_skin_geographic_location_longitude_units,
		'GSC_MIxS_human_skin_amount_or_size_of_sample_collected_units': GSC_MIxS_human_skin_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_human_skin_sample_storage_duration_units': GSC_MIxS_human_skin_sample_storage_duration_units,
		'GSC_MIxS_human_skin_sample_storage_temperature_units': GSC_MIxS_human_skin_sample_storage_temperature_units,
		'GSC_MIxS_human_skin_host_age_units': GSC_MIxS_human_skin_host_age_units,
		'GSC_MIxS_human_skin_host_height_units': GSC_MIxS_human_skin_host_height_units,
		'GSC_MIxS_human_skin_host_body_mass_index_units': GSC_MIxS_human_skin_host_body_mass_index_units,
		'GSC_MIxS_human_skin_host_total_mass_units': GSC_MIxS_human_skin_host_total_mass_units,
		'GSC_MIxS_human_skin_host_body_temperature_units': GSC_MIxS_human_skin_host_body_temperature_units,
		'GSC_MIxS_human_skin_temperature_units': GSC_MIxS_human_skin_temperature_units,
		'GSC_MIxS_human_skin_salinity_units': GSC_MIxS_human_skin_salinity_units,
		'GSC_MIxS_human_skin_time_since_last_wash_units': GSC_MIxS_human_skin_time_since_last_wash_units,
		'GSC_MIxS_human_skin_host_pulse_units': GSC_MIxS_human_skin_host_pulse_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_human_skin_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_human_skin_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_geographic_location_latitude_units, blank=False)
	GSC_MIxS_human_skin_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_geographic_location_longitude_units, blank=False)
	GSC_MIxS_human_skin_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_human_skin_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_sample_storage_duration_units, blank=False)
	GSC_MIxS_human_skin_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_sample_storage_temperature_units, blank=False)
	GSC_MIxS_human_skin_host_age = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_host_age_units, blank=False)
	GSC_MIxS_human_skin_host_height = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_host_height_units, blank=False)
	GSC_MIxS_human_skin_host_body_mass_index = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_host_body_mass_index_units, blank=False)
	GSC_MIxS_human_skin_host_total_mass = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_host_total_mass_units, blank=False)
	GSC_MIxS_human_skin_host_body_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_host_body_temperature_units, blank=False)
	GSC_MIxS_human_skin_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_temperature_units, blank=False)
	GSC_MIxS_human_skin_salinity = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_salinity_units, blank=False)
	GSC_MIxS_human_skin_time_since_last_wash = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_time_since_last_wash_units, blank=False)
	GSC_MIxS_human_skin_host_pulse = models.CharField(max_length=100, choices=GSC_MIxS_human_skin_host_pulse_units, blank=False)

class ENA_default_sample_checklist(SelfDescribingModel):

	ENA_default_sample_checklist_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	ENA_default_sample_checklist_environmental_sample_choice = [('No', 'No'), ('Yes', 'Yes')]

	ENA_default_sample_checklist_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	ENA_default_sample_checklist_cell_type= models.CharField(max_length=100, blank=True,help_text="cell type ")
	ENA_default_sample_checklist_dev_stage= models.CharField(max_length=100, blank=True,help_text="if the sam")
	ENA_default_sample_checklist_germline= models.CharField(max_length=100, blank=True,help_text="the sample")
	ENA_default_sample_checklist_tissue_lib= models.CharField(max_length=100, blank=True,help_text="tissue lib")
	ENA_default_sample_checklist_tissue_type= models.CharField(max_length=100, blank=True,help_text="tissue typ")
	ENA_default_sample_checklist_isolation_source= models.CharField(max_length=100, blank=True,help_text="describes ")
	ENA_default_sample_checklist_lat_lon= models.CharField(max_length=100, blank=True,help_text="geographic")
	ENA_default_sample_checklist_collected_by= models.CharField(max_length=100, blank=True,help_text="name of pe")
	ENA_default_sample_checklist_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(ENA_default_sample_checklist_collection_date_validator)])
	ENA_default_sample_checklist_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=ENA_default_sample_checklist_geographic_location_country_and_or_sea_choice)
	ENA_default_sample_checklist_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	ENA_default_sample_checklist_identified_by= models.CharField(max_length=100, blank=True,help_text="name of th")
	ENA_default_sample_checklist_environmental_sample= models.CharField(max_length=100, blank=True,help_text="identifies", choices=ENA_default_sample_checklist_environmental_sample_choice)
	ENA_default_sample_checklist_mating_type= models.CharField(max_length=100, blank=True,help_text="mating typ")
	ENA_default_sample_checklist_sex= models.CharField(max_length=100, blank=True,help_text="sex of the")
	ENA_default_sample_checklist_lab_host= models.CharField(max_length=100, blank=True,help_text="scientific")
	ENA_default_sample_checklist_host_scientific_name= models.CharField(max_length=100, blank=True,help_text="Scientific")
	ENA_default_sample_checklist_bio_material= models.CharField(max_length=100, blank=True,help_text="Unique ide")
	ENA_default_sample_checklist_culture_collection= models.CharField(max_length=100, blank=True,help_text="Unique ide")
	ENA_default_sample_checklist_specimen_voucher= models.CharField(max_length=100, blank=True,help_text="Unique ide")
	ENA_default_sample_checklist_cultivar= models.CharField(max_length=100, blank=True,help_text="cultivar (")
	ENA_default_sample_checklist_ecotype= models.CharField(max_length=100, blank=True,help_text="a populati")
	ENA_default_sample_checklist_isolate= models.CharField(max_length=100, blank=True,help_text="individual")
	ENA_default_sample_checklist_sub_species= models.CharField(max_length=100, blank=True,help_text="name of su")
	ENA_default_sample_checklist_variety= models.CharField(max_length=100, blank=True,help_text="variety (=")
	ENA_default_sample_checklist_sub_strain= models.CharField(max_length=100, blank=True,help_text="name or id")
	ENA_default_sample_checklist_cell_line= models.CharField(max_length=100, blank=True,help_text="cell line ")
	ENA_default_sample_checklist_serotype= models.CharField(max_length=100, blank=True,help_text="serologica")
	ENA_default_sample_checklist_serovar= models.CharField(max_length=100, blank=True,help_text="serologica")
	ENA_default_sample_checklist_strain= models.CharField(max_length=100, blank=True,help_text="Name of th")

	fields = {
		'ENA_default_sample_checklist_cell_type': ENA_default_sample_checklist_cell_type,
		'ENA_default_sample_checklist_dev_stage': ENA_default_sample_checklist_dev_stage,
		'ENA_default_sample_checklist_germline': ENA_default_sample_checklist_germline,
		'ENA_default_sample_checklist_tissue_lib': ENA_default_sample_checklist_tissue_lib,
		'ENA_default_sample_checklist_tissue_type': ENA_default_sample_checklist_tissue_type,
		'ENA_default_sample_checklist_isolation_source': ENA_default_sample_checklist_isolation_source,
		'ENA_default_sample_checklist_lat_lon': ENA_default_sample_checklist_lat_lon,
		'ENA_default_sample_checklist_collected_by': ENA_default_sample_checklist_collected_by,
		'ENA_default_sample_checklist_collection_date': ENA_default_sample_checklist_collection_date,
		'ENA_default_sample_checklist_geographic_location_country_and_or_sea': ENA_default_sample_checklist_geographic_location_country_and_or_sea,
		'ENA_default_sample_checklist_geographic_location_region_and_locality': ENA_default_sample_checklist_geographic_location_region_and_locality,
		'ENA_default_sample_checklist_identified_by': ENA_default_sample_checklist_identified_by,
		'ENA_default_sample_checklist_environmental_sample': ENA_default_sample_checklist_environmental_sample,
		'ENA_default_sample_checklist_mating_type': ENA_default_sample_checklist_mating_type,
		'ENA_default_sample_checklist_sex': ENA_default_sample_checklist_sex,
		'ENA_default_sample_checklist_lab_host': ENA_default_sample_checklist_lab_host,
		'ENA_default_sample_checklist_host_scientific_name': ENA_default_sample_checklist_host_scientific_name,
		'ENA_default_sample_checklist_bio_material': ENA_default_sample_checklist_bio_material,
		'ENA_default_sample_checklist_culture_collection': ENA_default_sample_checklist_culture_collection,
		'ENA_default_sample_checklist_specimen_voucher': ENA_default_sample_checklist_specimen_voucher,
		'ENA_default_sample_checklist_cultivar': ENA_default_sample_checklist_cultivar,
		'ENA_default_sample_checklist_ecotype': ENA_default_sample_checklist_ecotype,
		'ENA_default_sample_checklist_isolate': ENA_default_sample_checklist_isolate,
		'ENA_default_sample_checklist_sub_species': ENA_default_sample_checklist_sub_species,
		'ENA_default_sample_checklist_variety': ENA_default_sample_checklist_variety,
		'ENA_default_sample_checklist_sub_strain': ENA_default_sample_checklist_sub_strain,
		'ENA_default_sample_checklist_cell_line': ENA_default_sample_checklist_cell_line,
		'ENA_default_sample_checklist_serotype': ENA_default_sample_checklist_serotype,
		'ENA_default_sample_checklist_serovar': ENA_default_sample_checklist_serovar,
		'ENA_default_sample_checklist_strain': ENA_default_sample_checklist_strain,
	}

class ENA_default_sample_checklist_unit(SelfDescribingModel):


	fields = {
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)

class GSC_MIxS_plant_associated(SelfDescribingModel):

	GSC_MIxS_plant_associated_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_plant_associated_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_plant_associated_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_plant_associated_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_plant_associated_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_plant_associated_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_plant_associated_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_plant_associated_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_plant_associated_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_plant_associated_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_plant_associated_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_plant_associated_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_plant_associated_altitude_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_plant_associated_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_plant_associated_depth_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_elevation_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_host_dry_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_host_wet_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_host_age_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_host_taxid_validator = "[+-]?[0-9]+"
	GSC_MIxS_plant_associated_host_height_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_host_length_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_host_total_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_plant_associated_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_plant_associated_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_plant_associated_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_plant_associated_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_plant_associated_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_plant_associated_number_of_replicons_validator)])
	GSC_MIxS_plant_associated_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_plant_associated_extrachromosomal_elements_validator)])
	GSC_MIxS_plant_associated_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_plant_associated_estimated_size_validator)])
	GSC_MIxS_plant_associated_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_plant_associated_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_plant_associated_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_plant_associated_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_plant_associated_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_plant_associated_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_plant_associated_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_plant_associated_library_size_validator)])
	GSC_MIxS_plant_associated_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_plant_associated_library_reads_sequenced_validator)])
	GSC_MIxS_plant_associated_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_plant_associated_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_plant_associated_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_plant_associated_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_plant_associated_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_plant_associated_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_plant_associated_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_plant_associated_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_plant_associated_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_plant_associated_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_plant_associated_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_plant_associated_sequence_quality_check_choice)
	GSC_MIxS_plant_associated_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_plant_associated_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_plant_associated_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_plant_associated_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_plant_associated_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_plant_associated_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_plant_associated_collection_date_validator)])
	GSC_MIxS_plant_associated_altitude= models.CharField(max_length=100, blank=True,help_text="The altitu", validators=[RegexValidator(GSC_MIxS_plant_associated_altitude_validator)])
	GSC_MIxS_plant_associated_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_plant_associated_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_plant_associated_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_plant_associated_geographic_location_latitude_validator)])
	GSC_MIxS_plant_associated_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_plant_associated_geographic_location_longitude_validator)])
	GSC_MIxS_plant_associated_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_plant_associated_depth= models.CharField(max_length=100, blank=True,help_text="The vertic", validators=[RegexValidator(GSC_MIxS_plant_associated_depth_validator)])
	GSC_MIxS_plant_associated_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_plant_associated_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_plant_associated_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_plant_associated_elevation= models.CharField(max_length=100, blank=True,help_text="The elevat", validators=[RegexValidator(GSC_MIxS_plant_associated_elevation_validator)])
	GSC_MIxS_plant_associated_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_plant_associated_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_plant_associated_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_plant_associated_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_plant_associated_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_plant_associated_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_plant_associated_host_dry_mass= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_plant_associated_host_dry_mass_validator)])
	GSC_MIxS_plant_associated_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_plant_associated_oxygenation_status_of_sample_choice)
	GSC_MIxS_plant_associated_plant_product= models.CharField(max_length=100, blank=True,help_text="substance ")
	GSC_MIxS_plant_associated_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_plant_associated_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_plant_associated_sample_storage_duration_validator)])
	GSC_MIxS_plant_associated_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_plant_associated_sample_storage_temperature_validator)])
	GSC_MIxS_plant_associated_host_wet_mass= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_plant_associated_host_wet_mass_validator)])
	GSC_MIxS_plant_associated_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_plant_associated_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_plant_associated_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_plant_associated_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_plant_associated_host_common_name= models.CharField(max_length=100, blank=True,help_text="common nam")
	GSC_MIxS_plant_associated_host_age= models.CharField(max_length=100, blank=True,help_text="age of hos", validators=[RegexValidator(GSC_MIxS_plant_associated_host_age_validator)])
	GSC_MIxS_plant_associated_host_taxid= models.CharField(max_length=100, blank=True,help_text="NCBI taxon", validators=[RegexValidator(GSC_MIxS_plant_associated_host_taxid_validator)])
	GSC_MIxS_plant_associated_host_life_stage= models.CharField(max_length=100, blank=True,help_text="descriptio")
	GSC_MIxS_plant_associated_host_height= models.CharField(max_length=100, blank=True,help_text="the height", validators=[RegexValidator(GSC_MIxS_plant_associated_host_height_validator)])
	GSC_MIxS_plant_associated_host_length= models.CharField(max_length=100, blank=True,help_text="the length", validators=[RegexValidator(GSC_MIxS_plant_associated_host_length_validator)])
	GSC_MIxS_plant_associated_plant_body_site= models.CharField(max_length=100, blank=True,help_text="name of bo")
	GSC_MIxS_plant_associated_host_total_mass= models.CharField(max_length=100, blank=True,help_text="total mass", validators=[RegexValidator(GSC_MIxS_plant_associated_host_total_mass_validator)])
	GSC_MIxS_plant_associated_host_phenotype= models.CharField(max_length=100, blank=True,help_text="phenotype ")
	GSC_MIxS_plant_associated_host_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_plant_associated_climate_environment= models.CharField(max_length=100, blank=True,help_text="treatment ")
	GSC_MIxS_plant_associated_gaseous_environment= models.CharField(max_length=100, blank=True,help_text="use of con")
	GSC_MIxS_plant_associated_seasonal_environment= models.CharField(max_length=100, blank=True,help_text="treatment ")
	GSC_MIxS_plant_associated_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_plant_associated_temperature_validator)])
	GSC_MIxS_plant_associated_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_plant_associated_salinity_validator)])
	GSC_MIxS_plant_associated_host_genotype= models.CharField(max_length=100, blank=True,help_text="observed g")
	GSC_MIxS_plant_associated_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_plant_associated_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_plant_associated_trophic_level_choice)
	GSC_MIxS_plant_associated_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_plant_associated_relationship_to_oxygen_choice)
	GSC_MIxS_plant_associated_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_plant_associated_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_plant_associated_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_plant_associated_observed_biotic_relationship_choice)
	GSC_MIxS_plant_associated_air_temperature_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_antibiotic_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_chemical_mutagen= models.CharField(max_length=100, blank=True,help_text="treatment ")
	GSC_MIxS_plant_associated_fertilizer_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_fungicide_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_gravity= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_growth_hormone_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_growth_media= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_herbicide_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_humidity_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_mineral_nutrient_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_non_mineral_nutrient_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_pesticide_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_pH_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_radiation_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_rainfall_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_salt_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_standing_water_regimen= models.CharField(max_length=100, blank=True,help_text="treatment ")
	GSC_MIxS_plant_associated_tissue_culture_growth_media= models.CharField(max_length=100, blank=True,help_text="descriptio")
	GSC_MIxS_plant_associated_watering_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_water_temperature_regimen= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_mechanical_damage= models.CharField(max_length=100, blank=True,help_text="informatio")
	GSC_MIxS_plant_associated_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_plant_associated_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_plant_associated_project_name': GSC_MIxS_plant_associated_project_name,
		'GSC_MIxS_plant_associated_experimental_factor': GSC_MIxS_plant_associated_experimental_factor,
		'GSC_MIxS_plant_associated_ploidy': GSC_MIxS_plant_associated_ploidy,
		'GSC_MIxS_plant_associated_number_of_replicons': GSC_MIxS_plant_associated_number_of_replicons,
		'GSC_MIxS_plant_associated_extrachromosomal_elements': GSC_MIxS_plant_associated_extrachromosomal_elements,
		'GSC_MIxS_plant_associated_estimated_size': GSC_MIxS_plant_associated_estimated_size,
		'GSC_MIxS_plant_associated_reference_for_biomaterial': GSC_MIxS_plant_associated_reference_for_biomaterial,
		'GSC_MIxS_plant_associated_annotation_source': GSC_MIxS_plant_associated_annotation_source,
		'GSC_MIxS_plant_associated_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_plant_associated_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_plant_associated_nucleic_acid_extraction': GSC_MIxS_plant_associated_nucleic_acid_extraction,
		'GSC_MIxS_plant_associated_nucleic_acid_amplification': GSC_MIxS_plant_associated_nucleic_acid_amplification,
		'GSC_MIxS_plant_associated_library_size': GSC_MIxS_plant_associated_library_size,
		'GSC_MIxS_plant_associated_library_reads_sequenced': GSC_MIxS_plant_associated_library_reads_sequenced,
		'GSC_MIxS_plant_associated_library_construction_method': GSC_MIxS_plant_associated_library_construction_method,
		'GSC_MIxS_plant_associated_library_vector': GSC_MIxS_plant_associated_library_vector,
		'GSC_MIxS_plant_associated_library_screening_strategy': GSC_MIxS_plant_associated_library_screening_strategy,
		'GSC_MIxS_plant_associated_target_gene': GSC_MIxS_plant_associated_target_gene,
		'GSC_MIxS_plant_associated_target_subfragment': GSC_MIxS_plant_associated_target_subfragment,
		'GSC_MIxS_plant_associated_pcr_primers': GSC_MIxS_plant_associated_pcr_primers,
		'GSC_MIxS_plant_associated_multiplex_identifiers': GSC_MIxS_plant_associated_multiplex_identifiers,
		'GSC_MIxS_plant_associated_adapters': GSC_MIxS_plant_associated_adapters,
		'GSC_MIxS_plant_associated_pcr_conditions': GSC_MIxS_plant_associated_pcr_conditions,
		'GSC_MIxS_plant_associated_sequencing_method': GSC_MIxS_plant_associated_sequencing_method,
		'GSC_MIxS_plant_associated_sequence_quality_check': GSC_MIxS_plant_associated_sequence_quality_check,
		'GSC_MIxS_plant_associated_chimera_check_software': GSC_MIxS_plant_associated_chimera_check_software,
		'GSC_MIxS_plant_associated_relevant_electronic_resources': GSC_MIxS_plant_associated_relevant_electronic_resources,
		'GSC_MIxS_plant_associated_relevant_standard_operating_procedures': GSC_MIxS_plant_associated_relevant_standard_operating_procedures,
		'GSC_MIxS_plant_associated_negative_control_type': GSC_MIxS_plant_associated_negative_control_type,
		'GSC_MIxS_plant_associated_positive_control_type': GSC_MIxS_plant_associated_positive_control_type,
		'GSC_MIxS_plant_associated_collection_date': GSC_MIxS_plant_associated_collection_date,
		'GSC_MIxS_plant_associated_altitude': GSC_MIxS_plant_associated_altitude,
		'GSC_MIxS_plant_associated_geographic_location_country_and_or_sea': GSC_MIxS_plant_associated_geographic_location_country_and_or_sea,
		'GSC_MIxS_plant_associated_geographic_location_latitude': GSC_MIxS_plant_associated_geographic_location_latitude,
		'GSC_MIxS_plant_associated_geographic_location_longitude': GSC_MIxS_plant_associated_geographic_location_longitude,
		'GSC_MIxS_plant_associated_geographic_location_region_and_locality': GSC_MIxS_plant_associated_geographic_location_region_and_locality,
		'GSC_MIxS_plant_associated_depth': GSC_MIxS_plant_associated_depth,
		'GSC_MIxS_plant_associated_broad_scale_environmental_context': GSC_MIxS_plant_associated_broad_scale_environmental_context,
		'GSC_MIxS_plant_associated_local_environmental_context': GSC_MIxS_plant_associated_local_environmental_context,
		'GSC_MIxS_plant_associated_environmental_medium': GSC_MIxS_plant_associated_environmental_medium,
		'GSC_MIxS_plant_associated_elevation': GSC_MIxS_plant_associated_elevation,
		'GSC_MIxS_plant_associated_source_material_identifiers': GSC_MIxS_plant_associated_source_material_identifiers,
		'GSC_MIxS_plant_associated_sample_material_processing': GSC_MIxS_plant_associated_sample_material_processing,
		'GSC_MIxS_plant_associated_isolation_and_growth_condition': GSC_MIxS_plant_associated_isolation_and_growth_condition,
		'GSC_MIxS_plant_associated_propagation': GSC_MIxS_plant_associated_propagation,
		'GSC_MIxS_plant_associated_amount_or_size_of_sample_collected': GSC_MIxS_plant_associated_amount_or_size_of_sample_collected,
		'GSC_MIxS_plant_associated_host_dry_mass': GSC_MIxS_plant_associated_host_dry_mass,
		'GSC_MIxS_plant_associated_oxygenation_status_of_sample': GSC_MIxS_plant_associated_oxygenation_status_of_sample,
		'GSC_MIxS_plant_associated_plant_product': GSC_MIxS_plant_associated_plant_product,
		'GSC_MIxS_plant_associated_organism_count': GSC_MIxS_plant_associated_organism_count,
		'GSC_MIxS_plant_associated_sample_storage_duration': GSC_MIxS_plant_associated_sample_storage_duration,
		'GSC_MIxS_plant_associated_sample_storage_temperature': GSC_MIxS_plant_associated_sample_storage_temperature,
		'GSC_MIxS_plant_associated_host_wet_mass': GSC_MIxS_plant_associated_host_wet_mass,
		'GSC_MIxS_plant_associated_sample_storage_location': GSC_MIxS_plant_associated_sample_storage_location,
		'GSC_MIxS_plant_associated_sample_collection_device': GSC_MIxS_plant_associated_sample_collection_device,
		'GSC_MIxS_plant_associated_sample_collection_method': GSC_MIxS_plant_associated_sample_collection_method,
		'GSC_MIxS_plant_associated_host_disease_status': GSC_MIxS_plant_associated_host_disease_status,
		'GSC_MIxS_plant_associated_host_common_name': GSC_MIxS_plant_associated_host_common_name,
		'GSC_MIxS_plant_associated_host_age': GSC_MIxS_plant_associated_host_age,
		'GSC_MIxS_plant_associated_host_taxid': GSC_MIxS_plant_associated_host_taxid,
		'GSC_MIxS_plant_associated_host_life_stage': GSC_MIxS_plant_associated_host_life_stage,
		'GSC_MIxS_plant_associated_host_height': GSC_MIxS_plant_associated_host_height,
		'GSC_MIxS_plant_associated_host_length': GSC_MIxS_plant_associated_host_length,
		'GSC_MIxS_plant_associated_plant_body_site': GSC_MIxS_plant_associated_plant_body_site,
		'GSC_MIxS_plant_associated_host_total_mass': GSC_MIxS_plant_associated_host_total_mass,
		'GSC_MIxS_plant_associated_host_phenotype': GSC_MIxS_plant_associated_host_phenotype,
		'GSC_MIxS_plant_associated_host_subspecific_genetic_lineage': GSC_MIxS_plant_associated_host_subspecific_genetic_lineage,
		'GSC_MIxS_plant_associated_climate_environment': GSC_MIxS_plant_associated_climate_environment,
		'GSC_MIxS_plant_associated_gaseous_environment': GSC_MIxS_plant_associated_gaseous_environment,
		'GSC_MIxS_plant_associated_seasonal_environment': GSC_MIxS_plant_associated_seasonal_environment,
		'GSC_MIxS_plant_associated_temperature': GSC_MIxS_plant_associated_temperature,
		'GSC_MIxS_plant_associated_salinity': GSC_MIxS_plant_associated_salinity,
		'GSC_MIxS_plant_associated_host_genotype': GSC_MIxS_plant_associated_host_genotype,
		'GSC_MIxS_plant_associated_subspecific_genetic_lineage': GSC_MIxS_plant_associated_subspecific_genetic_lineage,
		'GSC_MIxS_plant_associated_trophic_level': GSC_MIxS_plant_associated_trophic_level,
		'GSC_MIxS_plant_associated_relationship_to_oxygen': GSC_MIxS_plant_associated_relationship_to_oxygen,
		'GSC_MIxS_plant_associated_known_pathogenicity': GSC_MIxS_plant_associated_known_pathogenicity,
		'GSC_MIxS_plant_associated_encoded_traits': GSC_MIxS_plant_associated_encoded_traits,
		'GSC_MIxS_plant_associated_observed_biotic_relationship': GSC_MIxS_plant_associated_observed_biotic_relationship,
		'GSC_MIxS_plant_associated_air_temperature_regimen': GSC_MIxS_plant_associated_air_temperature_regimen,
		'GSC_MIxS_plant_associated_antibiotic_regimen': GSC_MIxS_plant_associated_antibiotic_regimen,
		'GSC_MIxS_plant_associated_chemical_mutagen': GSC_MIxS_plant_associated_chemical_mutagen,
		'GSC_MIxS_plant_associated_fertilizer_regimen': GSC_MIxS_plant_associated_fertilizer_regimen,
		'GSC_MIxS_plant_associated_fungicide_regimen': GSC_MIxS_plant_associated_fungicide_regimen,
		'GSC_MIxS_plant_associated_gravity': GSC_MIxS_plant_associated_gravity,
		'GSC_MIxS_plant_associated_growth_hormone_regimen': GSC_MIxS_plant_associated_growth_hormone_regimen,
		'GSC_MIxS_plant_associated_growth_media': GSC_MIxS_plant_associated_growth_media,
		'GSC_MIxS_plant_associated_herbicide_regimen': GSC_MIxS_plant_associated_herbicide_regimen,
		'GSC_MIxS_plant_associated_humidity_regimen': GSC_MIxS_plant_associated_humidity_regimen,
		'GSC_MIxS_plant_associated_mineral_nutrient_regimen': GSC_MIxS_plant_associated_mineral_nutrient_regimen,
		'GSC_MIxS_plant_associated_non_mineral_nutrient_regimen': GSC_MIxS_plant_associated_non_mineral_nutrient_regimen,
		'GSC_MIxS_plant_associated_pesticide_regimen': GSC_MIxS_plant_associated_pesticide_regimen,
		'GSC_MIxS_plant_associated_pH_regimen': GSC_MIxS_plant_associated_pH_regimen,
		'GSC_MIxS_plant_associated_radiation_regimen': GSC_MIxS_plant_associated_radiation_regimen,
		'GSC_MIxS_plant_associated_rainfall_regimen': GSC_MIxS_plant_associated_rainfall_regimen,
		'GSC_MIxS_plant_associated_salt_regimen': GSC_MIxS_plant_associated_salt_regimen,
		'GSC_MIxS_plant_associated_standing_water_regimen': GSC_MIxS_plant_associated_standing_water_regimen,
		'GSC_MIxS_plant_associated_tissue_culture_growth_media': GSC_MIxS_plant_associated_tissue_culture_growth_media,
		'GSC_MIxS_plant_associated_watering_regimen': GSC_MIxS_plant_associated_watering_regimen,
		'GSC_MIxS_plant_associated_water_temperature_regimen': GSC_MIxS_plant_associated_water_temperature_regimen,
		'GSC_MIxS_plant_associated_mechanical_damage': GSC_MIxS_plant_associated_mechanical_damage,
		'GSC_MIxS_plant_associated_chemical_administration': GSC_MIxS_plant_associated_chemical_administration,
		'GSC_MIxS_plant_associated_perturbation': GSC_MIxS_plant_associated_perturbation,
	}

class GSC_MIxS_plant_associated_unit(SelfDescribingModel):

	GSC_MIxS_plant_associated_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_plant_associated_altitude_units = [('m', 'm')]
	GSC_MIxS_plant_associated_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_plant_associated_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_plant_associated_depth_units = [('m', 'm')]
	GSC_MIxS_plant_associated_elevation_units = [('m', 'm')]
	GSC_MIxS_plant_associated_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_plant_associated_host_dry_mass_units = [('g', 'g'), ('kg', 'kg'), ('mg', 'mg')]
	GSC_MIxS_plant_associated_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_plant_associated_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_plant_associated_host_wet_mass_units = [('g', 'g'), ('kg', 'kg'), ('mg', 'mg')]
	GSC_MIxS_plant_associated_host_age_units = [('centuries', 'centuries'), ('days', 'days'), ('decades', 'decades'), ('hours', 'hours'), ('minutes', 'minutes'), ('months', 'months'), ('seconds', 'seconds'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_plant_associated_host_height_units = [('cm', 'cm'), ('m', 'm'), ('mm', 'mm')]
	GSC_MIxS_plant_associated_host_length_units = [('cm', 'cm'), ('m', 'm'), ('mm', 'mm')]
	GSC_MIxS_plant_associated_host_total_mass_units = [('g', 'g'), ('kg', 'kg')]
	GSC_MIxS_plant_associated_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_plant_associated_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]

	fields = {
		'GSC_MIxS_plant_associated_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_plant_associated_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_plant_associated_altitude_units': GSC_MIxS_plant_associated_altitude_units,
		'GSC_MIxS_plant_associated_geographic_location_latitude_units': GSC_MIxS_plant_associated_geographic_location_latitude_units,
		'GSC_MIxS_plant_associated_geographic_location_longitude_units': GSC_MIxS_plant_associated_geographic_location_longitude_units,
		'GSC_MIxS_plant_associated_depth_units': GSC_MIxS_plant_associated_depth_units,
		'GSC_MIxS_plant_associated_elevation_units': GSC_MIxS_plant_associated_elevation_units,
		'GSC_MIxS_plant_associated_amount_or_size_of_sample_collected_units': GSC_MIxS_plant_associated_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_plant_associated_host_dry_mass_units': GSC_MIxS_plant_associated_host_dry_mass_units,
		'GSC_MIxS_plant_associated_sample_storage_duration_units': GSC_MIxS_plant_associated_sample_storage_duration_units,
		'GSC_MIxS_plant_associated_sample_storage_temperature_units': GSC_MIxS_plant_associated_sample_storage_temperature_units,
		'GSC_MIxS_plant_associated_host_wet_mass_units': GSC_MIxS_plant_associated_host_wet_mass_units,
		'GSC_MIxS_plant_associated_host_age_units': GSC_MIxS_plant_associated_host_age_units,
		'GSC_MIxS_plant_associated_host_height_units': GSC_MIxS_plant_associated_host_height_units,
		'GSC_MIxS_plant_associated_host_length_units': GSC_MIxS_plant_associated_host_length_units,
		'GSC_MIxS_plant_associated_host_total_mass_units': GSC_MIxS_plant_associated_host_total_mass_units,
		'GSC_MIxS_plant_associated_temperature_units': GSC_MIxS_plant_associated_temperature_units,
		'GSC_MIxS_plant_associated_salinity_units': GSC_MIxS_plant_associated_salinity_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_plant_associated_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_plant_associated_altitude = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_altitude_units, blank=False)
	GSC_MIxS_plant_associated_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_geographic_location_latitude_units, blank=False)
	GSC_MIxS_plant_associated_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_geographic_location_longitude_units, blank=False)
	GSC_MIxS_plant_associated_depth = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_depth_units, blank=False)
	GSC_MIxS_plant_associated_elevation = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_elevation_units, blank=False)
	GSC_MIxS_plant_associated_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_plant_associated_host_dry_mass = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_host_dry_mass_units, blank=False)
	GSC_MIxS_plant_associated_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_sample_storage_duration_units, blank=False)
	GSC_MIxS_plant_associated_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_sample_storage_temperature_units, blank=False)
	GSC_MIxS_plant_associated_host_wet_mass = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_host_wet_mass_units, blank=False)
	GSC_MIxS_plant_associated_host_age = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_host_age_units, blank=False)
	GSC_MIxS_plant_associated_host_height = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_host_height_units, blank=False)
	GSC_MIxS_plant_associated_host_length = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_host_length_units, blank=False)
	GSC_MIxS_plant_associated_host_total_mass = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_host_total_mass_units, blank=False)
	GSC_MIxS_plant_associated_temperature = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_temperature_units, blank=False)
	GSC_MIxS_plant_associated_salinity = models.CharField(max_length=100, choices=GSC_MIxS_plant_associated_salinity_units, blank=False)

class GSC_MIxS_water(SelfDescribingModel):

	GSC_MIxS_water_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_water_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_water_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_water_tidal_stage_choice = [('high', 'high'), ('low', 'low')]
	GSC_MIxS_water_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_water_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_water_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_water_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_water_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_water_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_water_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_water_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_water_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_water_altitude_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_water_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_water_depth_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_elevation_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_density_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_alkalinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_conductivity_validator = "[1-9][0-9]*\.?[0-9]*([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_water_current_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_fluorescence_validator = "[1-9][0-9]*\.?[0-9]*([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_light_intensity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_mean_friction_velocity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_mean_peak_friction_velocity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_downward_PAR_validator = "[1-9][0-9]*\.?[0-9]*([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_photon_flux_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_pressure_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_pH_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_total_depth_of_water_column_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_alkyl_diethers_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_aminopeptidase_activity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_ammonium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_bacterial_carbon_production_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_bacterial_production_validator = "[1-9][0-9]*\.?[0-9]*([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_bacterial_respiration_validator = "[1-9][0-9]*\.?[0-9]*([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_bishomohopanol_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_bromide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_calcium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_carbon_nitrogen_ratio_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_chloride_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_chlorophyll_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_diether_lipids_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_dissolved_carbon_dioxide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_dissolved_hydrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_dissolved_inorganic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_dissolved_inorganic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_dissolved_inorganic_phosphorus_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_dissolved_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_dissolved_organic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_dissolved_oxygen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_glucosidase_activity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_magnesium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_n_alkanes_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_nitrate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_nitrite_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_organic_matter_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_organic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_particulate_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_particulate_organic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_petroleum_hydrocarbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_phaeopigments_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_phosphate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_phospholipid_fatty_acid_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_potassium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_primary_production_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_redox_potential_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_silicate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_sodium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_soluble_reactive_phosphorus_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_sulfate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_sulfide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_suspended_particulate_matter_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_total_dissolved_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_total_inorganic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_total_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_total_particulate_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_water_total_phosphorus_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_water_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_water_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_water_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_water_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_water_number_of_replicons_validator)])
	GSC_MIxS_water_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_water_extrachromosomal_elements_validator)])
	GSC_MIxS_water_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_water_estimated_size_validator)])
	GSC_MIxS_water_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_water_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_water_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_water_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_water_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_water_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_water_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_water_library_size_validator)])
	GSC_MIxS_water_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_water_library_reads_sequenced_validator)])
	GSC_MIxS_water_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_water_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_water_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_water_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_water_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_water_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_water_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_water_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_water_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_water_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_water_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_water_sequence_quality_check_choice)
	GSC_MIxS_water_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_water_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_water_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_water_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_water_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_water_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_water_collection_date_validator)])
	GSC_MIxS_water_altitude= models.CharField(max_length=100, blank=True,help_text="The altitu", validators=[RegexValidator(GSC_MIxS_water_altitude_validator)])
	GSC_MIxS_water_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_water_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_water_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_water_geographic_location_latitude_validator)])
	GSC_MIxS_water_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_water_geographic_location_longitude_validator)])
	GSC_MIxS_water_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_water_depth= models.CharField(max_length=100, blank=False,help_text="The vertic", validators=[RegexValidator(GSC_MIxS_water_depth_validator)])
	GSC_MIxS_water_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_water_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_water_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_water_elevation= models.CharField(max_length=100, blank=True,help_text="The elevat", validators=[RegexValidator(GSC_MIxS_water_elevation_validator)])
	GSC_MIxS_water_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_water_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_water_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_water_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_water_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_water_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_water_biomass= models.CharField(max_length=100, blank=True,help_text="amount of ")
	GSC_MIxS_water_density= models.CharField(max_length=100, blank=True,help_text="density of", validators=[RegexValidator(GSC_MIxS_water_density_validator)])
	GSC_MIxS_water_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_water_oxygenation_status_of_sample_choice)
	GSC_MIxS_water_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_water_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_water_sample_storage_duration_validator)])
	GSC_MIxS_water_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_water_sample_storage_temperature_validator)])
	GSC_MIxS_water_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_water_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_water_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_water_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_water_host_scientific_name= models.CharField(max_length=100, blank=True,help_text="Scientific")
	GSC_MIxS_water_alkalinity= models.CharField(max_length=100, blank=True,help_text="alkalinity", validators=[RegexValidator(GSC_MIxS_water_alkalinity_validator)])
	GSC_MIxS_water_atmospheric_data= models.CharField(max_length=100, blank=True,help_text="measuremen")
	GSC_MIxS_water_conductivity= models.CharField(max_length=100, blank=True,help_text="electrical", validators=[RegexValidator(GSC_MIxS_water_conductivity_validator)])
	GSC_MIxS_water_water_current= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_water_water_current_validator)])
	GSC_MIxS_water_fluorescence= models.CharField(max_length=100, blank=True,help_text="raw (volts", validators=[RegexValidator(GSC_MIxS_water_fluorescence_validator)])
	GSC_MIxS_water_light_intensity= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_water_light_intensity_validator)])
	GSC_MIxS_water_mean_friction_velocity= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_water_mean_friction_velocity_validator)])
	GSC_MIxS_water_mean_peak_friction_velocity= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_water_mean_peak_friction_velocity_validator)])
	GSC_MIxS_water_downward_PAR= models.CharField(max_length=100, blank=True,help_text="visible wa", validators=[RegexValidator(GSC_MIxS_water_downward_PAR_validator)])
	GSC_MIxS_water_photon_flux= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_water_photon_flux_validator)])
	GSC_MIxS_water_pressure= models.CharField(max_length=100, blank=True,help_text="pressure t", validators=[RegexValidator(GSC_MIxS_water_pressure_validator)])
	GSC_MIxS_water_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_water_temperature_validator)])
	GSC_MIxS_water_tidal_stage= models.CharField(max_length=100, blank=True,help_text="stage of t", choices=GSC_MIxS_water_tidal_stage_choice)
	GSC_MIxS_water_pH= models.CharField(max_length=100, blank=True,help_text="pH measure", validators=[RegexValidator(GSC_MIxS_water_pH_validator)])
	GSC_MIxS_water_total_depth_of_water_column= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_water_total_depth_of_water_column_validator)])
	GSC_MIxS_water_alkyl_diethers= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_alkyl_diethers_validator)])
	GSC_MIxS_water_aminopeptidase_activity= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_water_aminopeptidase_activity_validator)])
	GSC_MIxS_water_ammonium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_ammonium_validator)])
	GSC_MIxS_water_bacterial_carbon_production= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_water_bacterial_carbon_production_validator)])
	GSC_MIxS_water_bacterial_production= models.CharField(max_length=100, blank=True,help_text="bacterial ", validators=[RegexValidator(GSC_MIxS_water_bacterial_production_validator)])
	GSC_MIxS_water_bacterial_respiration= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_water_bacterial_respiration_validator)])
	GSC_MIxS_water_bishomohopanol= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_bishomohopanol_validator)])
	GSC_MIxS_water_bromide= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_bromide_validator)])
	GSC_MIxS_water_calcium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_calcium_validator)])
	GSC_MIxS_water_carbon_nitrogen_ratio= models.CharField(max_length=100, blank=True,help_text="ratio of a", validators=[RegexValidator(GSC_MIxS_water_carbon_nitrogen_ratio_validator)])
	GSC_MIxS_water_chloride= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_chloride_validator)])
	GSC_MIxS_water_chlorophyll= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_chlorophyll_validator)])
	GSC_MIxS_water_diether_lipids= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_diether_lipids_validator)])
	GSC_MIxS_water_dissolved_carbon_dioxide= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_dissolved_carbon_dioxide_validator)])
	GSC_MIxS_water_dissolved_hydrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_dissolved_hydrogen_validator)])
	GSC_MIxS_water_dissolved_inorganic_carbon= models.CharField(max_length=100, blank=True,help_text="dissolved ", validators=[RegexValidator(GSC_MIxS_water_dissolved_inorganic_carbon_validator)])
	GSC_MIxS_water_dissolved_inorganic_nitrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_dissolved_inorganic_nitrogen_validator)])
	GSC_MIxS_water_dissolved_inorganic_phosphorus= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_dissolved_inorganic_phosphorus_validator)])
	GSC_MIxS_water_dissolved_organic_carbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_dissolved_organic_carbon_validator)])
	GSC_MIxS_water_dissolved_organic_nitrogen= models.CharField(max_length=100, blank=True,help_text="dissolved ", validators=[RegexValidator(GSC_MIxS_water_dissolved_organic_nitrogen_validator)])
	GSC_MIxS_water_dissolved_oxygen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_dissolved_oxygen_validator)])
	GSC_MIxS_water_glucosidase_activity= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_water_glucosidase_activity_validator)])
	GSC_MIxS_water_magnesium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_magnesium_validator)])
	GSC_MIxS_water_n_alkanes= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_n_alkanes_validator)])
	GSC_MIxS_water_nitrate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_nitrate_validator)])
	GSC_MIxS_water_nitrite= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_nitrite_validator)])
	GSC_MIxS_water_nitrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_nitrogen_validator)])
	GSC_MIxS_water_organic_carbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_organic_carbon_validator)])
	GSC_MIxS_water_organic_matter= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_organic_matter_validator)])
	GSC_MIxS_water_organic_nitrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_organic_nitrogen_validator)])
	GSC_MIxS_water_particulate_organic_carbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_particulate_organic_carbon_validator)])
	GSC_MIxS_water_particulate_organic_nitrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_particulate_organic_nitrogen_validator)])
	GSC_MIxS_water_petroleum_hydrocarbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_petroleum_hydrocarbon_validator)])
	GSC_MIxS_water_phaeopigments= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_phaeopigments_validator)])
	GSC_MIxS_water_phosphate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_phosphate_validator)])
	GSC_MIxS_water_phospholipid_fatty_acid= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_phospholipid_fatty_acid_validator)])
	GSC_MIxS_water_potassium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_potassium_validator)])
	GSC_MIxS_water_primary_production= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_water_primary_production_validator)])
	GSC_MIxS_water_redox_potential= models.CharField(max_length=100, blank=True,help_text="redox pote", validators=[RegexValidator(GSC_MIxS_water_redox_potential_validator)])
	GSC_MIxS_water_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_water_salinity_validator)])
	GSC_MIxS_water_silicate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_silicate_validator)])
	GSC_MIxS_water_sodium= models.CharField(max_length=100, blank=True,help_text="sodium con", validators=[RegexValidator(GSC_MIxS_water_sodium_validator)])
	GSC_MIxS_water_soluble_reactive_phosphorus= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_soluble_reactive_phosphorus_validator)])
	GSC_MIxS_water_sulfate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_sulfate_validator)])
	GSC_MIxS_water_sulfide= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_sulfide_validator)])
	GSC_MIxS_water_suspended_particulate_matter= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_water_suspended_particulate_matter_validator)])
	GSC_MIxS_water_total_dissolved_nitrogen= models.CharField(max_length=100, blank=True,help_text="total diss", validators=[RegexValidator(GSC_MIxS_water_total_dissolved_nitrogen_validator)])
	GSC_MIxS_water_total_inorganic_nitrogen= models.CharField(max_length=100, blank=True,help_text="total inor", validators=[RegexValidator(GSC_MIxS_water_total_inorganic_nitrogen_validator)])
	GSC_MIxS_water_total_nitrogen= models.CharField(max_length=100, blank=True,help_text="total nitr", validators=[RegexValidator(GSC_MIxS_water_total_nitrogen_validator)])
	GSC_MIxS_water_total_particulate_carbon= models.CharField(max_length=100, blank=True,help_text="total part", validators=[RegexValidator(GSC_MIxS_water_total_particulate_carbon_validator)])
	GSC_MIxS_water_total_phosphorus= models.CharField(max_length=100, blank=True,help_text="total phos", validators=[RegexValidator(GSC_MIxS_water_total_phosphorus_validator)])
	GSC_MIxS_water_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_water_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_water_trophic_level_choice)
	GSC_MIxS_water_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_water_relationship_to_oxygen_choice)
	GSC_MIxS_water_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_water_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_water_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_water_observed_biotic_relationship_choice)
	GSC_MIxS_water_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_water_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_water_project_name': GSC_MIxS_water_project_name,
		'GSC_MIxS_water_experimental_factor': GSC_MIxS_water_experimental_factor,
		'GSC_MIxS_water_ploidy': GSC_MIxS_water_ploidy,
		'GSC_MIxS_water_number_of_replicons': GSC_MIxS_water_number_of_replicons,
		'GSC_MIxS_water_extrachromosomal_elements': GSC_MIxS_water_extrachromosomal_elements,
		'GSC_MIxS_water_estimated_size': GSC_MIxS_water_estimated_size,
		'GSC_MIxS_water_reference_for_biomaterial': GSC_MIxS_water_reference_for_biomaterial,
		'GSC_MIxS_water_annotation_source': GSC_MIxS_water_annotation_source,
		'GSC_MIxS_water_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_water_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_water_nucleic_acid_extraction': GSC_MIxS_water_nucleic_acid_extraction,
		'GSC_MIxS_water_nucleic_acid_amplification': GSC_MIxS_water_nucleic_acid_amplification,
		'GSC_MIxS_water_library_size': GSC_MIxS_water_library_size,
		'GSC_MIxS_water_library_reads_sequenced': GSC_MIxS_water_library_reads_sequenced,
		'GSC_MIxS_water_library_construction_method': GSC_MIxS_water_library_construction_method,
		'GSC_MIxS_water_library_vector': GSC_MIxS_water_library_vector,
		'GSC_MIxS_water_library_screening_strategy': GSC_MIxS_water_library_screening_strategy,
		'GSC_MIxS_water_target_gene': GSC_MIxS_water_target_gene,
		'GSC_MIxS_water_target_subfragment': GSC_MIxS_water_target_subfragment,
		'GSC_MIxS_water_pcr_primers': GSC_MIxS_water_pcr_primers,
		'GSC_MIxS_water_multiplex_identifiers': GSC_MIxS_water_multiplex_identifiers,
		'GSC_MIxS_water_adapters': GSC_MIxS_water_adapters,
		'GSC_MIxS_water_pcr_conditions': GSC_MIxS_water_pcr_conditions,
		'GSC_MIxS_water_sequencing_method': GSC_MIxS_water_sequencing_method,
		'GSC_MIxS_water_sequence_quality_check': GSC_MIxS_water_sequence_quality_check,
		'GSC_MIxS_water_chimera_check_software': GSC_MIxS_water_chimera_check_software,
		'GSC_MIxS_water_relevant_electronic_resources': GSC_MIxS_water_relevant_electronic_resources,
		'GSC_MIxS_water_relevant_standard_operating_procedures': GSC_MIxS_water_relevant_standard_operating_procedures,
		'GSC_MIxS_water_negative_control_type': GSC_MIxS_water_negative_control_type,
		'GSC_MIxS_water_positive_control_type': GSC_MIxS_water_positive_control_type,
		'GSC_MIxS_water_collection_date': GSC_MIxS_water_collection_date,
		'GSC_MIxS_water_altitude': GSC_MIxS_water_altitude,
		'GSC_MIxS_water_geographic_location_country_and_or_sea': GSC_MIxS_water_geographic_location_country_and_or_sea,
		'GSC_MIxS_water_geographic_location_latitude': GSC_MIxS_water_geographic_location_latitude,
		'GSC_MIxS_water_geographic_location_longitude': GSC_MIxS_water_geographic_location_longitude,
		'GSC_MIxS_water_geographic_location_region_and_locality': GSC_MIxS_water_geographic_location_region_and_locality,
		'GSC_MIxS_water_depth': GSC_MIxS_water_depth,
		'GSC_MIxS_water_broad_scale_environmental_context': GSC_MIxS_water_broad_scale_environmental_context,
		'GSC_MIxS_water_local_environmental_context': GSC_MIxS_water_local_environmental_context,
		'GSC_MIxS_water_environmental_medium': GSC_MIxS_water_environmental_medium,
		'GSC_MIxS_water_elevation': GSC_MIxS_water_elevation,
		'GSC_MIxS_water_source_material_identifiers': GSC_MIxS_water_source_material_identifiers,
		'GSC_MIxS_water_sample_material_processing': GSC_MIxS_water_sample_material_processing,
		'GSC_MIxS_water_isolation_and_growth_condition': GSC_MIxS_water_isolation_and_growth_condition,
		'GSC_MIxS_water_propagation': GSC_MIxS_water_propagation,
		'GSC_MIxS_water_amount_or_size_of_sample_collected': GSC_MIxS_water_amount_or_size_of_sample_collected,
		'GSC_MIxS_water_biomass': GSC_MIxS_water_biomass,
		'GSC_MIxS_water_density': GSC_MIxS_water_density,
		'GSC_MIxS_water_oxygenation_status_of_sample': GSC_MIxS_water_oxygenation_status_of_sample,
		'GSC_MIxS_water_organism_count': GSC_MIxS_water_organism_count,
		'GSC_MIxS_water_sample_storage_duration': GSC_MIxS_water_sample_storage_duration,
		'GSC_MIxS_water_sample_storage_temperature': GSC_MIxS_water_sample_storage_temperature,
		'GSC_MIxS_water_sample_storage_location': GSC_MIxS_water_sample_storage_location,
		'GSC_MIxS_water_sample_collection_device': GSC_MIxS_water_sample_collection_device,
		'GSC_MIxS_water_sample_collection_method': GSC_MIxS_water_sample_collection_method,
		'GSC_MIxS_water_host_disease_status': GSC_MIxS_water_host_disease_status,
		'GSC_MIxS_water_host_scientific_name': GSC_MIxS_water_host_scientific_name,
		'GSC_MIxS_water_alkalinity': GSC_MIxS_water_alkalinity,
		'GSC_MIxS_water_atmospheric_data': GSC_MIxS_water_atmospheric_data,
		'GSC_MIxS_water_conductivity': GSC_MIxS_water_conductivity,
		'GSC_MIxS_water_water_current': GSC_MIxS_water_water_current,
		'GSC_MIxS_water_fluorescence': GSC_MIxS_water_fluorescence,
		'GSC_MIxS_water_light_intensity': GSC_MIxS_water_light_intensity,
		'GSC_MIxS_water_mean_friction_velocity': GSC_MIxS_water_mean_friction_velocity,
		'GSC_MIxS_water_mean_peak_friction_velocity': GSC_MIxS_water_mean_peak_friction_velocity,
		'GSC_MIxS_water_downward_PAR': GSC_MIxS_water_downward_PAR,
		'GSC_MIxS_water_photon_flux': GSC_MIxS_water_photon_flux,
		'GSC_MIxS_water_pressure': GSC_MIxS_water_pressure,
		'GSC_MIxS_water_temperature': GSC_MIxS_water_temperature,
		'GSC_MIxS_water_tidal_stage': GSC_MIxS_water_tidal_stage,
		'GSC_MIxS_water_pH': GSC_MIxS_water_pH,
		'GSC_MIxS_water_total_depth_of_water_column': GSC_MIxS_water_total_depth_of_water_column,
		'GSC_MIxS_water_alkyl_diethers': GSC_MIxS_water_alkyl_diethers,
		'GSC_MIxS_water_aminopeptidase_activity': GSC_MIxS_water_aminopeptidase_activity,
		'GSC_MIxS_water_ammonium': GSC_MIxS_water_ammonium,
		'GSC_MIxS_water_bacterial_carbon_production': GSC_MIxS_water_bacterial_carbon_production,
		'GSC_MIxS_water_bacterial_production': GSC_MIxS_water_bacterial_production,
		'GSC_MIxS_water_bacterial_respiration': GSC_MIxS_water_bacterial_respiration,
		'GSC_MIxS_water_bishomohopanol': GSC_MIxS_water_bishomohopanol,
		'GSC_MIxS_water_bromide': GSC_MIxS_water_bromide,
		'GSC_MIxS_water_calcium': GSC_MIxS_water_calcium,
		'GSC_MIxS_water_carbon_nitrogen_ratio': GSC_MIxS_water_carbon_nitrogen_ratio,
		'GSC_MIxS_water_chloride': GSC_MIxS_water_chloride,
		'GSC_MIxS_water_chlorophyll': GSC_MIxS_water_chlorophyll,
		'GSC_MIxS_water_diether_lipids': GSC_MIxS_water_diether_lipids,
		'GSC_MIxS_water_dissolved_carbon_dioxide': GSC_MIxS_water_dissolved_carbon_dioxide,
		'GSC_MIxS_water_dissolved_hydrogen': GSC_MIxS_water_dissolved_hydrogen,
		'GSC_MIxS_water_dissolved_inorganic_carbon': GSC_MIxS_water_dissolved_inorganic_carbon,
		'GSC_MIxS_water_dissolved_inorganic_nitrogen': GSC_MIxS_water_dissolved_inorganic_nitrogen,
		'GSC_MIxS_water_dissolved_inorganic_phosphorus': GSC_MIxS_water_dissolved_inorganic_phosphorus,
		'GSC_MIxS_water_dissolved_organic_carbon': GSC_MIxS_water_dissolved_organic_carbon,
		'GSC_MIxS_water_dissolved_organic_nitrogen': GSC_MIxS_water_dissolved_organic_nitrogen,
		'GSC_MIxS_water_dissolved_oxygen': GSC_MIxS_water_dissolved_oxygen,
		'GSC_MIxS_water_glucosidase_activity': GSC_MIxS_water_glucosidase_activity,
		'GSC_MIxS_water_magnesium': GSC_MIxS_water_magnesium,
		'GSC_MIxS_water_n_alkanes': GSC_MIxS_water_n_alkanes,
		'GSC_MIxS_water_nitrate': GSC_MIxS_water_nitrate,
		'GSC_MIxS_water_nitrite': GSC_MIxS_water_nitrite,
		'GSC_MIxS_water_nitrogen': GSC_MIxS_water_nitrogen,
		'GSC_MIxS_water_organic_carbon': GSC_MIxS_water_organic_carbon,
		'GSC_MIxS_water_organic_matter': GSC_MIxS_water_organic_matter,
		'GSC_MIxS_water_organic_nitrogen': GSC_MIxS_water_organic_nitrogen,
		'GSC_MIxS_water_particulate_organic_carbon': GSC_MIxS_water_particulate_organic_carbon,
		'GSC_MIxS_water_particulate_organic_nitrogen': GSC_MIxS_water_particulate_organic_nitrogen,
		'GSC_MIxS_water_petroleum_hydrocarbon': GSC_MIxS_water_petroleum_hydrocarbon,
		'GSC_MIxS_water_phaeopigments': GSC_MIxS_water_phaeopigments,
		'GSC_MIxS_water_phosphate': GSC_MIxS_water_phosphate,
		'GSC_MIxS_water_phospholipid_fatty_acid': GSC_MIxS_water_phospholipid_fatty_acid,
		'GSC_MIxS_water_potassium': GSC_MIxS_water_potassium,
		'GSC_MIxS_water_primary_production': GSC_MIxS_water_primary_production,
		'GSC_MIxS_water_redox_potential': GSC_MIxS_water_redox_potential,
		'GSC_MIxS_water_salinity': GSC_MIxS_water_salinity,
		'GSC_MIxS_water_silicate': GSC_MIxS_water_silicate,
		'GSC_MIxS_water_sodium': GSC_MIxS_water_sodium,
		'GSC_MIxS_water_soluble_reactive_phosphorus': GSC_MIxS_water_soluble_reactive_phosphorus,
		'GSC_MIxS_water_sulfate': GSC_MIxS_water_sulfate,
		'GSC_MIxS_water_sulfide': GSC_MIxS_water_sulfide,
		'GSC_MIxS_water_suspended_particulate_matter': GSC_MIxS_water_suspended_particulate_matter,
		'GSC_MIxS_water_total_dissolved_nitrogen': GSC_MIxS_water_total_dissolved_nitrogen,
		'GSC_MIxS_water_total_inorganic_nitrogen': GSC_MIxS_water_total_inorganic_nitrogen,
		'GSC_MIxS_water_total_nitrogen': GSC_MIxS_water_total_nitrogen,
		'GSC_MIxS_water_total_particulate_carbon': GSC_MIxS_water_total_particulate_carbon,
		'GSC_MIxS_water_total_phosphorus': GSC_MIxS_water_total_phosphorus,
		'GSC_MIxS_water_subspecific_genetic_lineage': GSC_MIxS_water_subspecific_genetic_lineage,
		'GSC_MIxS_water_trophic_level': GSC_MIxS_water_trophic_level,
		'GSC_MIxS_water_relationship_to_oxygen': GSC_MIxS_water_relationship_to_oxygen,
		'GSC_MIxS_water_known_pathogenicity': GSC_MIxS_water_known_pathogenicity,
		'GSC_MIxS_water_encoded_traits': GSC_MIxS_water_encoded_traits,
		'GSC_MIxS_water_observed_biotic_relationship': GSC_MIxS_water_observed_biotic_relationship,
		'GSC_MIxS_water_chemical_administration': GSC_MIxS_water_chemical_administration,
		'GSC_MIxS_water_perturbation': GSC_MIxS_water_perturbation,
	}

class GSC_MIxS_water_unit(SelfDescribingModel):

	GSC_MIxS_water_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_water_altitude_units = [('m', 'm')]
	GSC_MIxS_water_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_water_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_water_depth_units = [('m', 'm')]
	GSC_MIxS_water_elevation_units = [('m', 'm')]
	GSC_MIxS_water_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_water_biomass_units = [('g', 'g'), ('kg', 'kg'), ('t', 't')]
	GSC_MIxS_water_density_units = [('g', 'g'), ('/', '/'), ('m', 'm'), ('3', '3')]
	GSC_MIxS_water_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_water_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_water_alkalinity_units = [('m', 'm'), ('E', 'E'), ('q', 'q'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_conductivity_units = [('m', 'm'), ('S', 'S'), ('/', '/'), ('c', 'c'), ('m', 'm')]
	GSC_MIxS_water_water_current_units = [('knot', 'knot'), ('m3/s', 'm3/s')]
	GSC_MIxS_water_fluorescence_units = [('V', 'V'), ('mg Chla/m3', 'mg Chla/m3')]
	GSC_MIxS_water_light_intensity_units = [('l', 'l'), ('u', 'u'), ('x', 'x')]
	GSC_MIxS_water_mean_friction_velocity_units = [('m', 'm'), ('/', '/'), ('s', 's')]
	GSC_MIxS_water_mean_peak_friction_velocity_units = [('m', 'm'), ('/', '/'), ('s', 's')]
	GSC_MIxS_water_downward_PAR_units = [('µ', 'µ'), ('E', 'E'), ('/', '/'), ('m', 'm'), ('2', '2'), ('/', '/'), ('s', 's')]
	GSC_MIxS_water_photon_flux_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('m', 'm'), ('2', '2'), ('/', '/'), ('s', 's')]
	GSC_MIxS_water_pressure_units = [('atm', 'atm'), ('bar', 'bar')]
	GSC_MIxS_water_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_water_total_depth_of_water_column_units = [('m', 'm')]
	GSC_MIxS_water_alkyl_diethers_units = [('M/L', 'M/L'), ('µg/L', 'µg/L')]
	GSC_MIxS_water_aminopeptidase_activity_units = [('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L'), ('/', '/'), ('h', 'h')]
	GSC_MIxS_water_ammonium_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_bacterial_carbon_production_units = [('n', 'n'), ('g', 'g'), ('/', '/'), ('h', 'h')]
	GSC_MIxS_water_bacterial_production_units = [('m', 'm'), ('g', 'g'), ('/', '/'), ('m', 'm'), ('3', '3'), ('/', '/'), ('d', 'd')]
	GSC_MIxS_water_bacterial_respiration_units = [('m', 'm'), ('g', 'g'), ('/', '/'), ('m', 'm'), ('3', '3'), ('/', '/'), ('d', 'd')]
	GSC_MIxS_water_bishomohopanol_units = [('µg/L', 'µg/L'), ('µg/g', 'µg/g')]
	GSC_MIxS_water_bromide_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_water_calcium_units = [('mg/L', 'mg/L'), ('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_water_chloride_units = [('m', 'm'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_chlorophyll_units = [('mg/m3', 'mg/m3'), ('µg/L', 'µg/L')]
	GSC_MIxS_water_diether_lipids_units = [('n', 'n'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_dissolved_carbon_dioxide_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_dissolved_hydrogen_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_dissolved_inorganic_carbon_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_dissolved_inorganic_nitrogen_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_dissolved_inorganic_phosphorus_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_dissolved_organic_carbon_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_dissolved_organic_nitrogen_units = [('mg/L', 'mg/L'), ('µg/L', 'µg/L')]
	GSC_MIxS_water_dissolved_oxygen_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('k', 'k'), ('g', 'g')]
	GSC_MIxS_water_glucosidase_activity_units = [('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L'), ('/', '/'), ('h', 'h')]
	GSC_MIxS_water_magnesium_units = [('mg/L', 'mg/L'), ('mol/L', 'mol/L'), ('parts/million', 'parts/million')]
	GSC_MIxS_water_n_alkanes_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_nitrate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_nitrite_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_nitrogen_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_organic_carbon_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_organic_matter_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_organic_nitrogen_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_particulate_organic_carbon_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_particulate_organic_nitrogen_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_petroleum_hydrocarbon_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_phaeopigments_units = [('mg/m3', 'mg/m3'), ('µg/L', 'µg/L')]
	GSC_MIxS_water_phosphate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_phospholipid_fatty_acid_units = [('mol/L', 'mol/L'), ('mol/g', 'mol/g')]
	GSC_MIxS_water_potassium_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_water_primary_production_units = [('g/m2/day', 'g/m2/day'), ('mg/m3/day', 'mg/m3/day')]
	GSC_MIxS_water_redox_potential_units = [('m', 'm'), ('V', 'V')]
	GSC_MIxS_water_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]
	GSC_MIxS_water_silicate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_sodium_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_water_soluble_reactive_phosphorus_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_sulfate_units = [('mg/L', 'mg/L'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_water_sulfide_units = [('mg/L', 'mg/L'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_water_suspended_particulate_matter_units = [('m', 'm'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_total_dissolved_nitrogen_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_total_inorganic_nitrogen_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_water_total_nitrogen_units = [('µg/L', 'µg/L'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_water_total_particulate_carbon_units = [('µg/L', 'µg/L'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_water_total_phosphorus_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]

	fields = {
		'GSC_MIxS_water_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_water_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_water_altitude_units': GSC_MIxS_water_altitude_units,
		'GSC_MIxS_water_geographic_location_latitude_units': GSC_MIxS_water_geographic_location_latitude_units,
		'GSC_MIxS_water_geographic_location_longitude_units': GSC_MIxS_water_geographic_location_longitude_units,
		'GSC_MIxS_water_depth_units': GSC_MIxS_water_depth_units,
		'GSC_MIxS_water_elevation_units': GSC_MIxS_water_elevation_units,
		'GSC_MIxS_water_amount_or_size_of_sample_collected_units': GSC_MIxS_water_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_water_biomass_units': GSC_MIxS_water_biomass_units,
		'GSC_MIxS_water_density_units': GSC_MIxS_water_density_units,
		'GSC_MIxS_water_sample_storage_duration_units': GSC_MIxS_water_sample_storage_duration_units,
		'GSC_MIxS_water_sample_storage_temperature_units': GSC_MIxS_water_sample_storage_temperature_units,
		'GSC_MIxS_water_alkalinity_units': GSC_MIxS_water_alkalinity_units,
		'GSC_MIxS_water_conductivity_units': GSC_MIxS_water_conductivity_units,
		'GSC_MIxS_water_water_current_units': GSC_MIxS_water_water_current_units,
		'GSC_MIxS_water_fluorescence_units': GSC_MIxS_water_fluorescence_units,
		'GSC_MIxS_water_light_intensity_units': GSC_MIxS_water_light_intensity_units,
		'GSC_MIxS_water_mean_friction_velocity_units': GSC_MIxS_water_mean_friction_velocity_units,
		'GSC_MIxS_water_mean_peak_friction_velocity_units': GSC_MIxS_water_mean_peak_friction_velocity_units,
		'GSC_MIxS_water_downward_PAR_units': GSC_MIxS_water_downward_PAR_units,
		'GSC_MIxS_water_photon_flux_units': GSC_MIxS_water_photon_flux_units,
		'GSC_MIxS_water_pressure_units': GSC_MIxS_water_pressure_units,
		'GSC_MIxS_water_temperature_units': GSC_MIxS_water_temperature_units,
		'GSC_MIxS_water_total_depth_of_water_column_units': GSC_MIxS_water_total_depth_of_water_column_units,
		'GSC_MIxS_water_alkyl_diethers_units': GSC_MIxS_water_alkyl_diethers_units,
		'GSC_MIxS_water_aminopeptidase_activity_units': GSC_MIxS_water_aminopeptidase_activity_units,
		'GSC_MIxS_water_ammonium_units': GSC_MIxS_water_ammonium_units,
		'GSC_MIxS_water_bacterial_carbon_production_units': GSC_MIxS_water_bacterial_carbon_production_units,
		'GSC_MIxS_water_bacterial_production_units': GSC_MIxS_water_bacterial_production_units,
		'GSC_MIxS_water_bacterial_respiration_units': GSC_MIxS_water_bacterial_respiration_units,
		'GSC_MIxS_water_bishomohopanol_units': GSC_MIxS_water_bishomohopanol_units,
		'GSC_MIxS_water_bromide_units': GSC_MIxS_water_bromide_units,
		'GSC_MIxS_water_calcium_units': GSC_MIxS_water_calcium_units,
		'GSC_MIxS_water_chloride_units': GSC_MIxS_water_chloride_units,
		'GSC_MIxS_water_chlorophyll_units': GSC_MIxS_water_chlorophyll_units,
		'GSC_MIxS_water_diether_lipids_units': GSC_MIxS_water_diether_lipids_units,
		'GSC_MIxS_water_dissolved_carbon_dioxide_units': GSC_MIxS_water_dissolved_carbon_dioxide_units,
		'GSC_MIxS_water_dissolved_hydrogen_units': GSC_MIxS_water_dissolved_hydrogen_units,
		'GSC_MIxS_water_dissolved_inorganic_carbon_units': GSC_MIxS_water_dissolved_inorganic_carbon_units,
		'GSC_MIxS_water_dissolved_inorganic_nitrogen_units': GSC_MIxS_water_dissolved_inorganic_nitrogen_units,
		'GSC_MIxS_water_dissolved_inorganic_phosphorus_units': GSC_MIxS_water_dissolved_inorganic_phosphorus_units,
		'GSC_MIxS_water_dissolved_organic_carbon_units': GSC_MIxS_water_dissolved_organic_carbon_units,
		'GSC_MIxS_water_dissolved_organic_nitrogen_units': GSC_MIxS_water_dissolved_organic_nitrogen_units,
		'GSC_MIxS_water_dissolved_oxygen_units': GSC_MIxS_water_dissolved_oxygen_units,
		'GSC_MIxS_water_glucosidase_activity_units': GSC_MIxS_water_glucosidase_activity_units,
		'GSC_MIxS_water_magnesium_units': GSC_MIxS_water_magnesium_units,
		'GSC_MIxS_water_n_alkanes_units': GSC_MIxS_water_n_alkanes_units,
		'GSC_MIxS_water_nitrate_units': GSC_MIxS_water_nitrate_units,
		'GSC_MIxS_water_nitrite_units': GSC_MIxS_water_nitrite_units,
		'GSC_MIxS_water_nitrogen_units': GSC_MIxS_water_nitrogen_units,
		'GSC_MIxS_water_organic_carbon_units': GSC_MIxS_water_organic_carbon_units,
		'GSC_MIxS_water_organic_matter_units': GSC_MIxS_water_organic_matter_units,
		'GSC_MIxS_water_organic_nitrogen_units': GSC_MIxS_water_organic_nitrogen_units,
		'GSC_MIxS_water_particulate_organic_carbon_units': GSC_MIxS_water_particulate_organic_carbon_units,
		'GSC_MIxS_water_particulate_organic_nitrogen_units': GSC_MIxS_water_particulate_organic_nitrogen_units,
		'GSC_MIxS_water_petroleum_hydrocarbon_units': GSC_MIxS_water_petroleum_hydrocarbon_units,
		'GSC_MIxS_water_phaeopigments_units': GSC_MIxS_water_phaeopigments_units,
		'GSC_MIxS_water_phosphate_units': GSC_MIxS_water_phosphate_units,
		'GSC_MIxS_water_phospholipid_fatty_acid_units': GSC_MIxS_water_phospholipid_fatty_acid_units,
		'GSC_MIxS_water_potassium_units': GSC_MIxS_water_potassium_units,
		'GSC_MIxS_water_primary_production_units': GSC_MIxS_water_primary_production_units,
		'GSC_MIxS_water_redox_potential_units': GSC_MIxS_water_redox_potential_units,
		'GSC_MIxS_water_salinity_units': GSC_MIxS_water_salinity_units,
		'GSC_MIxS_water_silicate_units': GSC_MIxS_water_silicate_units,
		'GSC_MIxS_water_sodium_units': GSC_MIxS_water_sodium_units,
		'GSC_MIxS_water_soluble_reactive_phosphorus_units': GSC_MIxS_water_soluble_reactive_phosphorus_units,
		'GSC_MIxS_water_sulfate_units': GSC_MIxS_water_sulfate_units,
		'GSC_MIxS_water_sulfide_units': GSC_MIxS_water_sulfide_units,
		'GSC_MIxS_water_suspended_particulate_matter_units': GSC_MIxS_water_suspended_particulate_matter_units,
		'GSC_MIxS_water_total_dissolved_nitrogen_units': GSC_MIxS_water_total_dissolved_nitrogen_units,
		'GSC_MIxS_water_total_inorganic_nitrogen_units': GSC_MIxS_water_total_inorganic_nitrogen_units,
		'GSC_MIxS_water_total_nitrogen_units': GSC_MIxS_water_total_nitrogen_units,
		'GSC_MIxS_water_total_particulate_carbon_units': GSC_MIxS_water_total_particulate_carbon_units,
		'GSC_MIxS_water_total_phosphorus_units': GSC_MIxS_water_total_phosphorus_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_water_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_water_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_water_altitude = models.CharField(max_length=100, choices=GSC_MIxS_water_altitude_units, blank=False)
	GSC_MIxS_water_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_water_geographic_location_latitude_units, blank=False)
	GSC_MIxS_water_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_water_geographic_location_longitude_units, blank=False)
	GSC_MIxS_water_depth = models.CharField(max_length=100, choices=GSC_MIxS_water_depth_units, blank=False)
	GSC_MIxS_water_elevation = models.CharField(max_length=100, choices=GSC_MIxS_water_elevation_units, blank=False)
	GSC_MIxS_water_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_water_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_water_biomass = models.CharField(max_length=100, choices=GSC_MIxS_water_biomass_units, blank=False)
	GSC_MIxS_water_density = models.CharField(max_length=100, choices=GSC_MIxS_water_density_units, blank=False)
	GSC_MIxS_water_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_water_sample_storage_duration_units, blank=False)
	GSC_MIxS_water_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_water_sample_storage_temperature_units, blank=False)
	GSC_MIxS_water_alkalinity = models.CharField(max_length=100, choices=GSC_MIxS_water_alkalinity_units, blank=False)
	GSC_MIxS_water_conductivity = models.CharField(max_length=100, choices=GSC_MIxS_water_conductivity_units, blank=False)
	GSC_MIxS_water_water_current = models.CharField(max_length=100, choices=GSC_MIxS_water_water_current_units, blank=False)
	GSC_MIxS_water_fluorescence = models.CharField(max_length=100, choices=GSC_MIxS_water_fluorescence_units, blank=False)
	GSC_MIxS_water_light_intensity = models.CharField(max_length=100, choices=GSC_MIxS_water_light_intensity_units, blank=False)
	GSC_MIxS_water_mean_friction_velocity = models.CharField(max_length=100, choices=GSC_MIxS_water_mean_friction_velocity_units, blank=False)
	GSC_MIxS_water_mean_peak_friction_velocity = models.CharField(max_length=100, choices=GSC_MIxS_water_mean_peak_friction_velocity_units, blank=False)
	GSC_MIxS_water_downward_PAR = models.CharField(max_length=100, choices=GSC_MIxS_water_downward_PAR_units, blank=False)
	GSC_MIxS_water_photon_flux = models.CharField(max_length=100, choices=GSC_MIxS_water_photon_flux_units, blank=False)
	GSC_MIxS_water_pressure = models.CharField(max_length=100, choices=GSC_MIxS_water_pressure_units, blank=False)
	GSC_MIxS_water_temperature = models.CharField(max_length=100, choices=GSC_MIxS_water_temperature_units, blank=False)
	GSC_MIxS_water_total_depth_of_water_column = models.CharField(max_length=100, choices=GSC_MIxS_water_total_depth_of_water_column_units, blank=False)
	GSC_MIxS_water_alkyl_diethers = models.CharField(max_length=100, choices=GSC_MIxS_water_alkyl_diethers_units, blank=False)
	GSC_MIxS_water_aminopeptidase_activity = models.CharField(max_length=100, choices=GSC_MIxS_water_aminopeptidase_activity_units, blank=False)
	GSC_MIxS_water_ammonium = models.CharField(max_length=100, choices=GSC_MIxS_water_ammonium_units, blank=False)
	GSC_MIxS_water_bacterial_carbon_production = models.CharField(max_length=100, choices=GSC_MIxS_water_bacterial_carbon_production_units, blank=False)
	GSC_MIxS_water_bacterial_production = models.CharField(max_length=100, choices=GSC_MIxS_water_bacterial_production_units, blank=False)
	GSC_MIxS_water_bacterial_respiration = models.CharField(max_length=100, choices=GSC_MIxS_water_bacterial_respiration_units, blank=False)
	GSC_MIxS_water_bishomohopanol = models.CharField(max_length=100, choices=GSC_MIxS_water_bishomohopanol_units, blank=False)
	GSC_MIxS_water_bromide = models.CharField(max_length=100, choices=GSC_MIxS_water_bromide_units, blank=False)
	GSC_MIxS_water_calcium = models.CharField(max_length=100, choices=GSC_MIxS_water_calcium_units, blank=False)
	GSC_MIxS_water_chloride = models.CharField(max_length=100, choices=GSC_MIxS_water_chloride_units, blank=False)
	GSC_MIxS_water_chlorophyll = models.CharField(max_length=100, choices=GSC_MIxS_water_chlorophyll_units, blank=False)
	GSC_MIxS_water_diether_lipids = models.CharField(max_length=100, choices=GSC_MIxS_water_diether_lipids_units, blank=False)
	GSC_MIxS_water_dissolved_carbon_dioxide = models.CharField(max_length=100, choices=GSC_MIxS_water_dissolved_carbon_dioxide_units, blank=False)
	GSC_MIxS_water_dissolved_hydrogen = models.CharField(max_length=100, choices=GSC_MIxS_water_dissolved_hydrogen_units, blank=False)
	GSC_MIxS_water_dissolved_inorganic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_water_dissolved_inorganic_carbon_units, blank=False)
	GSC_MIxS_water_dissolved_inorganic_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_water_dissolved_inorganic_nitrogen_units, blank=False)
	GSC_MIxS_water_dissolved_inorganic_phosphorus = models.CharField(max_length=100, choices=GSC_MIxS_water_dissolved_inorganic_phosphorus_units, blank=False)
	GSC_MIxS_water_dissolved_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_water_dissolved_organic_carbon_units, blank=False)
	GSC_MIxS_water_dissolved_organic_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_water_dissolved_organic_nitrogen_units, blank=False)
	GSC_MIxS_water_dissolved_oxygen = models.CharField(max_length=100, choices=GSC_MIxS_water_dissolved_oxygen_units, blank=False)
	GSC_MIxS_water_glucosidase_activity = models.CharField(max_length=100, choices=GSC_MIxS_water_glucosidase_activity_units, blank=False)
	GSC_MIxS_water_magnesium = models.CharField(max_length=100, choices=GSC_MIxS_water_magnesium_units, blank=False)
	GSC_MIxS_water_n_alkanes = models.CharField(max_length=100, choices=GSC_MIxS_water_n_alkanes_units, blank=False)
	GSC_MIxS_water_nitrate = models.CharField(max_length=100, choices=GSC_MIxS_water_nitrate_units, blank=False)
	GSC_MIxS_water_nitrite = models.CharField(max_length=100, choices=GSC_MIxS_water_nitrite_units, blank=False)
	GSC_MIxS_water_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_water_nitrogen_units, blank=False)
	GSC_MIxS_water_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_water_organic_carbon_units, blank=False)
	GSC_MIxS_water_organic_matter = models.CharField(max_length=100, choices=GSC_MIxS_water_organic_matter_units, blank=False)
	GSC_MIxS_water_organic_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_water_organic_nitrogen_units, blank=False)
	GSC_MIxS_water_particulate_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_water_particulate_organic_carbon_units, blank=False)
	GSC_MIxS_water_particulate_organic_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_water_particulate_organic_nitrogen_units, blank=False)
	GSC_MIxS_water_petroleum_hydrocarbon = models.CharField(max_length=100, choices=GSC_MIxS_water_petroleum_hydrocarbon_units, blank=False)
	GSC_MIxS_water_phaeopigments = models.CharField(max_length=100, choices=GSC_MIxS_water_phaeopigments_units, blank=False)
	GSC_MIxS_water_phosphate = models.CharField(max_length=100, choices=GSC_MIxS_water_phosphate_units, blank=False)
	GSC_MIxS_water_phospholipid_fatty_acid = models.CharField(max_length=100, choices=GSC_MIxS_water_phospholipid_fatty_acid_units, blank=False)
	GSC_MIxS_water_potassium = models.CharField(max_length=100, choices=GSC_MIxS_water_potassium_units, blank=False)
	GSC_MIxS_water_primary_production = models.CharField(max_length=100, choices=GSC_MIxS_water_primary_production_units, blank=False)
	GSC_MIxS_water_redox_potential = models.CharField(max_length=100, choices=GSC_MIxS_water_redox_potential_units, blank=False)
	GSC_MIxS_water_salinity = models.CharField(max_length=100, choices=GSC_MIxS_water_salinity_units, blank=False)
	GSC_MIxS_water_silicate = models.CharField(max_length=100, choices=GSC_MIxS_water_silicate_units, blank=False)
	GSC_MIxS_water_sodium = models.CharField(max_length=100, choices=GSC_MIxS_water_sodium_units, blank=False)
	GSC_MIxS_water_soluble_reactive_phosphorus = models.CharField(max_length=100, choices=GSC_MIxS_water_soluble_reactive_phosphorus_units, blank=False)
	GSC_MIxS_water_sulfate = models.CharField(max_length=100, choices=GSC_MIxS_water_sulfate_units, blank=False)
	GSC_MIxS_water_sulfide = models.CharField(max_length=100, choices=GSC_MIxS_water_sulfide_units, blank=False)
	GSC_MIxS_water_suspended_particulate_matter = models.CharField(max_length=100, choices=GSC_MIxS_water_suspended_particulate_matter_units, blank=False)
	GSC_MIxS_water_total_dissolved_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_water_total_dissolved_nitrogen_units, blank=False)
	GSC_MIxS_water_total_inorganic_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_water_total_inorganic_nitrogen_units, blank=False)
	GSC_MIxS_water_total_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_water_total_nitrogen_units, blank=False)
	GSC_MIxS_water_total_particulate_carbon = models.CharField(max_length=100, choices=GSC_MIxS_water_total_particulate_carbon_units, blank=False)
	GSC_MIxS_water_total_phosphorus = models.CharField(max_length=100, choices=GSC_MIxS_water_total_phosphorus_units, blank=False)

class GSC_MIxS_soil(SelfDescribingModel):

	GSC_MIxS_soil_profile_position_choice = [('backslope', 'backslope'), ('footslope', 'footslope'), ('shoulder', 'shoulder'), ('summit', 'summit'), ('toeslope', 'toeslope')]
	GSC_MIxS_soil_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_soil_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_soil_soil_horizon_choice = [('A horizon', 'A horizon'), ('B horizon', 'B horizon'), ('C horizon', 'C horizon'), ('E horizon', 'E horizon'), ('O horizon', 'O horizon'), ('Permafrost', 'Permafrost'), ('R layer', 'R layer')]
	GSC_MIxS_soil_soil_type_choice = [('Acrisol', 'Acrisol'), ('Albeluvisol', 'Albeluvisol'), ('Alisol', 'Alisol'), ('Andosol', 'Andosol'), ('Anthrosol', 'Anthrosol'), ('Arenosol', 'Arenosol'), ('Calcisol', 'Calcisol'), ('Cambisol', 'Cambisol'), ('Chernozem', 'Chernozem'), ('Cryosol', 'Cryosol'), ('Durisol', 'Durisol'), ('Ferralsol', 'Ferralsol'), ('Fluvisol', 'Fluvisol'), ('Gleysol', 'Gleysol'), ('Gypsisol', 'Gypsisol'), ('Histosol', 'Histosol'), ('Kastanozem', 'Kastanozem'), ('Leptosol', 'Leptosol'), ('Lixisol', 'Lixisol'), ('Luvisol', 'Luvisol'), ('Nitisol', 'Nitisol'), ('Phaeozem', 'Phaeozem'), ('Planosol', 'Planosol'), ('Plinthosol', 'Plinthosol'), ('Podzol', 'Podzol'), ('Regosol', 'Regosol'), ('Solonchak', 'Solonchak'), ('Solonetz', 'Solonetz'), ('Stagnosol', 'Stagnosol'), ('Technosol', 'Technosol'), ('Umbrisol', 'Umbrisol'), ('Vertisol', 'Vertisol')]
	GSC_MIxS_soil_drainage_classification_choice = [('excessively drained', 'excessively drained'), ('moderately well', 'moderately well'), ('poorly', 'poorly'), ('somewhat poorly', 'somewhat poorly'), ('very poorly', 'very poorly'), ('well', 'well')]
	GSC_MIxS_soil_history_tillage_choice = [('chisel', 'chisel'), ('cutting disc', 'cutting disc'), ('disc plough', 'disc plough'), ('drill', 'drill'), ('mouldboard', 'mouldboard'), ('ridge till', 'ridge till'), ('strip tillage', 'strip tillage'), ('tined', 'tined'), ('zonal tillage', 'zonal tillage')]
	GSC_MIxS_soil_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_soil_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_soil_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_soil_slope_gradient_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_soil_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_soil_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_soil_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_soil_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_soil_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_soil_altitude_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_soil_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_soil_depth_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_elevation_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_sample_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_microbial_biomass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_extreme_unusual_properties_Al_saturation_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_mean_annual_and_seasonal_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_mean_annual_and_seasonal_precipitation_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_pH_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_organic_matter_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_total_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_water_content_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_soil_total_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_soil_slope_gradient= models.CharField(max_length=100, blank=True,help_text="commonly c", validators=[RegexValidator(GSC_MIxS_soil_slope_gradient_validator)])
	GSC_MIxS_soil_slope_aspect= models.CharField(max_length=100, blank=True,help_text="the direct")
	GSC_MIxS_soil_profile_position= models.CharField(max_length=100, blank=True,help_text="cross-sect", choices=GSC_MIxS_soil_profile_position_choice)
	GSC_MIxS_soil_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_soil_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_soil_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_soil_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_soil_number_of_replicons_validator)])
	GSC_MIxS_soil_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_soil_extrachromosomal_elements_validator)])
	GSC_MIxS_soil_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_soil_estimated_size_validator)])
	GSC_MIxS_soil_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_soil_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_soil_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_soil_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_soil_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_soil_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_soil_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_soil_library_size_validator)])
	GSC_MIxS_soil_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_soil_library_reads_sequenced_validator)])
	GSC_MIxS_soil_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_soil_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_soil_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_soil_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_soil_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_soil_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_soil_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_soil_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_soil_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_soil_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_soil_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_soil_sequence_quality_check_choice)
	GSC_MIxS_soil_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_soil_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_soil_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_soil_pooling_of_DNA_extracts_if_done= models.CharField(max_length=100, blank=True,help_text="were multi")
	GSC_MIxS_soil_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_soil_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_soil_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_soil_collection_date_validator)])
	GSC_MIxS_soil_altitude= models.CharField(max_length=100, blank=True,help_text="The altitu", validators=[RegexValidator(GSC_MIxS_soil_altitude_validator)])
	GSC_MIxS_soil_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_soil_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_soil_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_soil_geographic_location_latitude_validator)])
	GSC_MIxS_soil_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_soil_geographic_location_longitude_validator)])
	GSC_MIxS_soil_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_soil_depth= models.CharField(max_length=100, blank=False,help_text="The vertic", validators=[RegexValidator(GSC_MIxS_soil_depth_validator)])
	GSC_MIxS_soil_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_soil_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_soil_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_soil_elevation= models.CharField(max_length=100, blank=False,help_text="The elevat", validators=[RegexValidator(GSC_MIxS_soil_elevation_validator)])
	GSC_MIxS_soil_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_soil_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_soil_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_soil_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_soil_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_soil_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_soil_composite_design_sieving_if_any= models.CharField(max_length=100, blank=True,help_text="collection")
	GSC_MIxS_soil_sample_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="weight (g)", validators=[RegexValidator(GSC_MIxS_soil_sample_weight_for_DNA_extraction_validator)])
	GSC_MIxS_soil_storage_conditions_fresh_frozen_other= models.CharField(max_length=100, blank=True,help_text="explain ho")
	GSC_MIxS_soil_microbial_biomass= models.CharField(max_length=100, blank=True,help_text="the part o", validators=[RegexValidator(GSC_MIxS_soil_microbial_biomass_validator)])
	GSC_MIxS_soil_microbial_biomass_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_soil_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_soil_salinity_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_extreme_unusual_properties_heavy_metals= models.CharField(max_length=100, blank=True,help_text="heavy meta")
	GSC_MIxS_soil_extreme_unusual_properties_heavy_metals_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_extreme_unusual_properties_Al_saturation= models.CharField(max_length=100, blank=True,help_text="aluminum s", validators=[RegexValidator(GSC_MIxS_soil_extreme_unusual_properties_Al_saturation_validator)])
	GSC_MIxS_soil_extreme_unusual_properties_Al_saturation_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_soil_host_scientific_name= models.CharField(max_length=100, blank=True,help_text="Scientific")
	GSC_MIxS_soil_link_to_climate_information= models.CharField(max_length=100, blank=True,help_text="link to cl")
	GSC_MIxS_soil_link_to_classification_information= models.CharField(max_length=100, blank=True,help_text="link to di")
	GSC_MIxS_soil_links_to_additional_analysis= models.CharField(max_length=100, blank=True,help_text="link to ad")
	GSC_MIxS_soil_current_land_use= models.CharField(max_length=100, blank=True,help_text="present st")
	GSC_MIxS_soil_current_vegetation= models.CharField(max_length=100, blank=True,help_text="vegetation")
	GSC_MIxS_soil_current_vegetation_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_soil_horizon= models.CharField(max_length=100, blank=True,help_text="specific l", choices=GSC_MIxS_soil_soil_horizon_choice)
	GSC_MIxS_soil_soil_horizon_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_mean_annual_and_seasonal_temperature= models.CharField(max_length=100, blank=True,help_text="mean annua", validators=[RegexValidator(GSC_MIxS_soil_mean_annual_and_seasonal_temperature_validator)])
	GSC_MIxS_soil_mean_annual_and_seasonal_precipitation= models.CharField(max_length=100, blank=True,help_text="mean annua", validators=[RegexValidator(GSC_MIxS_soil_mean_annual_and_seasonal_precipitation_validator)])
	GSC_MIxS_soil_soil_taxonomic_FAO_classification= models.CharField(max_length=100, blank=True,help_text="soil class")
	GSC_MIxS_soil_soil_taxonomic_local_classification= models.CharField(max_length=100, blank=True,help_text="soil class")
	GSC_MIxS_soil_soil_taxonomic_local_classification_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_soil_type= models.CharField(max_length=100, blank=True,help_text="Descriptio", choices=GSC_MIxS_soil_soil_type_choice)
	GSC_MIxS_soil_soil_type_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_drainage_classification= models.CharField(max_length=100, blank=True,help_text="drainage c", choices=GSC_MIxS_soil_drainage_classification_choice)
	GSC_MIxS_soil_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_soil_temperature_validator)])
	GSC_MIxS_soil_soil_texture_measurement= models.CharField(max_length=100, blank=True,help_text="the relati")
	GSC_MIxS_soil_soil_texture_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_pH= models.CharField(max_length=100, blank=True,help_text="pH measure", validators=[RegexValidator(GSC_MIxS_soil_pH_validator)])
	GSC_MIxS_soil_pH_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_water_content_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_total_organic_C_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_total_nitrogen_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_organic_matter= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_soil_organic_matter_validator)])
	GSC_MIxS_soil_total_organic_carbon= models.CharField(max_length=100, blank=True,help_text="Definition", validators=[RegexValidator(GSC_MIxS_soil_total_organic_carbon_validator)])
	GSC_MIxS_soil_water_content= models.CharField(max_length=100, blank=True,help_text="water cont", validators=[RegexValidator(GSC_MIxS_soil_water_content_validator)])
	GSC_MIxS_soil_total_nitrogen= models.CharField(max_length=100, blank=True,help_text="total nitr", validators=[RegexValidator(GSC_MIxS_soil_total_nitrogen_validator)])
	GSC_MIxS_soil_history_previous_land_use= models.CharField(max_length=100, blank=True,help_text="previous l")
	GSC_MIxS_soil_history_previous_land_use_method= models.CharField(max_length=100, blank=True,help_text="reference ")
	GSC_MIxS_soil_history_crop_rotation= models.CharField(max_length=100, blank=True,help_text="whether or")
	GSC_MIxS_soil_history_agrochemical_additions= models.CharField(max_length=100, blank=True,help_text="addition o")
	GSC_MIxS_soil_history_tillage= models.CharField(max_length=100, blank=True,help_text="note metho", choices=GSC_MIxS_soil_history_tillage_choice)
	GSC_MIxS_soil_history_fire= models.CharField(max_length=100, blank=True,help_text="historical")
	GSC_MIxS_soil_history_flooding= models.CharField(max_length=100, blank=True,help_text="historical")
	GSC_MIxS_soil_history_extreme_events= models.CharField(max_length=100, blank=True,help_text="unusual ph")
	GSC_MIxS_soil_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_soil_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_soil_trophic_level_choice)
	GSC_MIxS_soil_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_soil_relationship_to_oxygen_choice)
	GSC_MIxS_soil_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_soil_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_soil_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_soil_observed_biotic_relationship_choice)
	GSC_MIxS_soil_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_soil_slope_gradient': GSC_MIxS_soil_slope_gradient,
		'GSC_MIxS_soil_slope_aspect': GSC_MIxS_soil_slope_aspect,
		'GSC_MIxS_soil_profile_position': GSC_MIxS_soil_profile_position,
		'GSC_MIxS_soil_project_name': GSC_MIxS_soil_project_name,
		'GSC_MIxS_soil_experimental_factor': GSC_MIxS_soil_experimental_factor,
		'GSC_MIxS_soil_ploidy': GSC_MIxS_soil_ploidy,
		'GSC_MIxS_soil_number_of_replicons': GSC_MIxS_soil_number_of_replicons,
		'GSC_MIxS_soil_extrachromosomal_elements': GSC_MIxS_soil_extrachromosomal_elements,
		'GSC_MIxS_soil_estimated_size': GSC_MIxS_soil_estimated_size,
		'GSC_MIxS_soil_reference_for_biomaterial': GSC_MIxS_soil_reference_for_biomaterial,
		'GSC_MIxS_soil_annotation_source': GSC_MIxS_soil_annotation_source,
		'GSC_MIxS_soil_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_soil_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_soil_nucleic_acid_extraction': GSC_MIxS_soil_nucleic_acid_extraction,
		'GSC_MIxS_soil_nucleic_acid_amplification': GSC_MIxS_soil_nucleic_acid_amplification,
		'GSC_MIxS_soil_library_size': GSC_MIxS_soil_library_size,
		'GSC_MIxS_soil_library_reads_sequenced': GSC_MIxS_soil_library_reads_sequenced,
		'GSC_MIxS_soil_library_construction_method': GSC_MIxS_soil_library_construction_method,
		'GSC_MIxS_soil_library_vector': GSC_MIxS_soil_library_vector,
		'GSC_MIxS_soil_library_screening_strategy': GSC_MIxS_soil_library_screening_strategy,
		'GSC_MIxS_soil_target_gene': GSC_MIxS_soil_target_gene,
		'GSC_MIxS_soil_target_subfragment': GSC_MIxS_soil_target_subfragment,
		'GSC_MIxS_soil_pcr_primers': GSC_MIxS_soil_pcr_primers,
		'GSC_MIxS_soil_multiplex_identifiers': GSC_MIxS_soil_multiplex_identifiers,
		'GSC_MIxS_soil_adapters': GSC_MIxS_soil_adapters,
		'GSC_MIxS_soil_pcr_conditions': GSC_MIxS_soil_pcr_conditions,
		'GSC_MIxS_soil_sequencing_method': GSC_MIxS_soil_sequencing_method,
		'GSC_MIxS_soil_sequence_quality_check': GSC_MIxS_soil_sequence_quality_check,
		'GSC_MIxS_soil_chimera_check_software': GSC_MIxS_soil_chimera_check_software,
		'GSC_MIxS_soil_relevant_electronic_resources': GSC_MIxS_soil_relevant_electronic_resources,
		'GSC_MIxS_soil_relevant_standard_operating_procedures': GSC_MIxS_soil_relevant_standard_operating_procedures,
		'GSC_MIxS_soil_pooling_of_DNA_extracts_if_done': GSC_MIxS_soil_pooling_of_DNA_extracts_if_done,
		'GSC_MIxS_soil_negative_control_type': GSC_MIxS_soil_negative_control_type,
		'GSC_MIxS_soil_positive_control_type': GSC_MIxS_soil_positive_control_type,
		'GSC_MIxS_soil_collection_date': GSC_MIxS_soil_collection_date,
		'GSC_MIxS_soil_altitude': GSC_MIxS_soil_altitude,
		'GSC_MIxS_soil_geographic_location_country_and_or_sea': GSC_MIxS_soil_geographic_location_country_and_or_sea,
		'GSC_MIxS_soil_geographic_location_latitude': GSC_MIxS_soil_geographic_location_latitude,
		'GSC_MIxS_soil_geographic_location_longitude': GSC_MIxS_soil_geographic_location_longitude,
		'GSC_MIxS_soil_geographic_location_region_and_locality': GSC_MIxS_soil_geographic_location_region_and_locality,
		'GSC_MIxS_soil_depth': GSC_MIxS_soil_depth,
		'GSC_MIxS_soil_broad_scale_environmental_context': GSC_MIxS_soil_broad_scale_environmental_context,
		'GSC_MIxS_soil_local_environmental_context': GSC_MIxS_soil_local_environmental_context,
		'GSC_MIxS_soil_environmental_medium': GSC_MIxS_soil_environmental_medium,
		'GSC_MIxS_soil_elevation': GSC_MIxS_soil_elevation,
		'GSC_MIxS_soil_source_material_identifiers': GSC_MIxS_soil_source_material_identifiers,
		'GSC_MIxS_soil_sample_material_processing': GSC_MIxS_soil_sample_material_processing,
		'GSC_MIxS_soil_isolation_and_growth_condition': GSC_MIxS_soil_isolation_and_growth_condition,
		'GSC_MIxS_soil_propagation': GSC_MIxS_soil_propagation,
		'GSC_MIxS_soil_amount_or_size_of_sample_collected': GSC_MIxS_soil_amount_or_size_of_sample_collected,
		'GSC_MIxS_soil_composite_design_sieving_if_any': GSC_MIxS_soil_composite_design_sieving_if_any,
		'GSC_MIxS_soil_sample_weight_for_DNA_extraction': GSC_MIxS_soil_sample_weight_for_DNA_extraction,
		'GSC_MIxS_soil_storage_conditions_fresh_frozen_other': GSC_MIxS_soil_storage_conditions_fresh_frozen_other,
		'GSC_MIxS_soil_microbial_biomass': GSC_MIxS_soil_microbial_biomass,
		'GSC_MIxS_soil_microbial_biomass_method': GSC_MIxS_soil_microbial_biomass_method,
		'GSC_MIxS_soil_sample_collection_device': GSC_MIxS_soil_sample_collection_device,
		'GSC_MIxS_soil_sample_collection_method': GSC_MIxS_soil_sample_collection_method,
		'GSC_MIxS_soil_salinity_method': GSC_MIxS_soil_salinity_method,
		'GSC_MIxS_soil_extreme_unusual_properties_heavy_metals': GSC_MIxS_soil_extreme_unusual_properties_heavy_metals,
		'GSC_MIxS_soil_extreme_unusual_properties_heavy_metals_method': GSC_MIxS_soil_extreme_unusual_properties_heavy_metals_method,
		'GSC_MIxS_soil_extreme_unusual_properties_Al_saturation': GSC_MIxS_soil_extreme_unusual_properties_Al_saturation,
		'GSC_MIxS_soil_extreme_unusual_properties_Al_saturation_method': GSC_MIxS_soil_extreme_unusual_properties_Al_saturation_method,
		'GSC_MIxS_soil_host_disease_status': GSC_MIxS_soil_host_disease_status,
		'GSC_MIxS_soil_host_scientific_name': GSC_MIxS_soil_host_scientific_name,
		'GSC_MIxS_soil_link_to_climate_information': GSC_MIxS_soil_link_to_climate_information,
		'GSC_MIxS_soil_link_to_classification_information': GSC_MIxS_soil_link_to_classification_information,
		'GSC_MIxS_soil_links_to_additional_analysis': GSC_MIxS_soil_links_to_additional_analysis,
		'GSC_MIxS_soil_current_land_use': GSC_MIxS_soil_current_land_use,
		'GSC_MIxS_soil_current_vegetation': GSC_MIxS_soil_current_vegetation,
		'GSC_MIxS_soil_current_vegetation_method': GSC_MIxS_soil_current_vegetation_method,
		'GSC_MIxS_soil_soil_horizon': GSC_MIxS_soil_soil_horizon,
		'GSC_MIxS_soil_soil_horizon_method': GSC_MIxS_soil_soil_horizon_method,
		'GSC_MIxS_soil_mean_annual_and_seasonal_temperature': GSC_MIxS_soil_mean_annual_and_seasonal_temperature,
		'GSC_MIxS_soil_mean_annual_and_seasonal_precipitation': GSC_MIxS_soil_mean_annual_and_seasonal_precipitation,
		'GSC_MIxS_soil_soil_taxonomic_FAO_classification': GSC_MIxS_soil_soil_taxonomic_FAO_classification,
		'GSC_MIxS_soil_soil_taxonomic_local_classification': GSC_MIxS_soil_soil_taxonomic_local_classification,
		'GSC_MIxS_soil_soil_taxonomic_local_classification_method': GSC_MIxS_soil_soil_taxonomic_local_classification_method,
		'GSC_MIxS_soil_soil_type': GSC_MIxS_soil_soil_type,
		'GSC_MIxS_soil_soil_type_method': GSC_MIxS_soil_soil_type_method,
		'GSC_MIxS_soil_drainage_classification': GSC_MIxS_soil_drainage_classification,
		'GSC_MIxS_soil_temperature': GSC_MIxS_soil_temperature,
		'GSC_MIxS_soil_soil_texture_measurement': GSC_MIxS_soil_soil_texture_measurement,
		'GSC_MIxS_soil_soil_texture_method': GSC_MIxS_soil_soil_texture_method,
		'GSC_MIxS_soil_pH': GSC_MIxS_soil_pH,
		'GSC_MIxS_soil_pH_method': GSC_MIxS_soil_pH_method,
		'GSC_MIxS_soil_water_content_method': GSC_MIxS_soil_water_content_method,
		'GSC_MIxS_soil_total_organic_C_method': GSC_MIxS_soil_total_organic_C_method,
		'GSC_MIxS_soil_total_nitrogen_method': GSC_MIxS_soil_total_nitrogen_method,
		'GSC_MIxS_soil_organic_matter': GSC_MIxS_soil_organic_matter,
		'GSC_MIxS_soil_total_organic_carbon': GSC_MIxS_soil_total_organic_carbon,
		'GSC_MIxS_soil_water_content': GSC_MIxS_soil_water_content,
		'GSC_MIxS_soil_total_nitrogen': GSC_MIxS_soil_total_nitrogen,
		'GSC_MIxS_soil_history_previous_land_use': GSC_MIxS_soil_history_previous_land_use,
		'GSC_MIxS_soil_history_previous_land_use_method': GSC_MIxS_soil_history_previous_land_use_method,
		'GSC_MIxS_soil_history_crop_rotation': GSC_MIxS_soil_history_crop_rotation,
		'GSC_MIxS_soil_history_agrochemical_additions': GSC_MIxS_soil_history_agrochemical_additions,
		'GSC_MIxS_soil_history_tillage': GSC_MIxS_soil_history_tillage,
		'GSC_MIxS_soil_history_fire': GSC_MIxS_soil_history_fire,
		'GSC_MIxS_soil_history_flooding': GSC_MIxS_soil_history_flooding,
		'GSC_MIxS_soil_history_extreme_events': GSC_MIxS_soil_history_extreme_events,
		'GSC_MIxS_soil_subspecific_genetic_lineage': GSC_MIxS_soil_subspecific_genetic_lineage,
		'GSC_MIxS_soil_trophic_level': GSC_MIxS_soil_trophic_level,
		'GSC_MIxS_soil_relationship_to_oxygen': GSC_MIxS_soil_relationship_to_oxygen,
		'GSC_MIxS_soil_known_pathogenicity': GSC_MIxS_soil_known_pathogenicity,
		'GSC_MIxS_soil_encoded_traits': GSC_MIxS_soil_encoded_traits,
		'GSC_MIxS_soil_observed_biotic_relationship': GSC_MIxS_soil_observed_biotic_relationship,
		'GSC_MIxS_soil_perturbation': GSC_MIxS_soil_perturbation,
	}

class GSC_MIxS_soil_unit(SelfDescribingModel):

	GSC_MIxS_soil_slope_gradient_units = [('%', '%')]
	GSC_MIxS_soil_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_soil_altitude_units = [('m', 'm')]
	GSC_MIxS_soil_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_soil_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_soil_depth_units = [('m', 'm')]
	GSC_MIxS_soil_elevation_units = [('m', 'm')]
	GSC_MIxS_soil_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_soil_sample_weight_for_DNA_extraction_units = [('g', 'g')]
	GSC_MIxS_soil_microbial_biomass_units = [('g', 'g'), ('/', '/'), ('k', 'k'), ('g', 'g')]
	GSC_MIxS_soil_extreme_unusual_properties_Al_saturation_units = [('%', '%')]
	GSC_MIxS_soil_mean_annual_and_seasonal_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_soil_mean_annual_and_seasonal_precipitation_units = [('m', 'm'), ('m', 'm')]
	GSC_MIxS_soil_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_soil_soil_texture_measurement_units = [('%', '%'), (' ', ' '), ('s', 's'), ('a', 'a'), ('n', 'n'), ('d', 'd'), ('/', '/'), ('s', 's'), ('i', 'i'), ('l', 'l'), ('t', 't'), ('/', '/'), ('c', 'c'), ('l', 'l'), ('a', 'a'), ('y', 'y')]
	GSC_MIxS_soil_organic_matter_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_soil_total_organic_carbon_units = [('g', 'g'), ('/', '/'), ('k', 'k'), ('g', 'g')]
	GSC_MIxS_soil_water_content_units = [('cm3/cm3', 'cm3/cm3'), ('g/g', 'g/g')]
	GSC_MIxS_soil_total_nitrogen_units = [('µg/L', 'µg/L'), ('µmol/L', 'µmol/L')]

	fields = {
		'GSC_MIxS_soil_slope_gradient_units': GSC_MIxS_soil_slope_gradient_units,
		'GSC_MIxS_soil_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_soil_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_soil_altitude_units': GSC_MIxS_soil_altitude_units,
		'GSC_MIxS_soil_geographic_location_latitude_units': GSC_MIxS_soil_geographic_location_latitude_units,
		'GSC_MIxS_soil_geographic_location_longitude_units': GSC_MIxS_soil_geographic_location_longitude_units,
		'GSC_MIxS_soil_depth_units': GSC_MIxS_soil_depth_units,
		'GSC_MIxS_soil_elevation_units': GSC_MIxS_soil_elevation_units,
		'GSC_MIxS_soil_amount_or_size_of_sample_collected_units': GSC_MIxS_soil_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_soil_sample_weight_for_DNA_extraction_units': GSC_MIxS_soil_sample_weight_for_DNA_extraction_units,
		'GSC_MIxS_soil_microbial_biomass_units': GSC_MIxS_soil_microbial_biomass_units,
		'GSC_MIxS_soil_extreme_unusual_properties_Al_saturation_units': GSC_MIxS_soil_extreme_unusual_properties_Al_saturation_units,
		'GSC_MIxS_soil_mean_annual_and_seasonal_temperature_units': GSC_MIxS_soil_mean_annual_and_seasonal_temperature_units,
		'GSC_MIxS_soil_mean_annual_and_seasonal_precipitation_units': GSC_MIxS_soil_mean_annual_and_seasonal_precipitation_units,
		'GSC_MIxS_soil_temperature_units': GSC_MIxS_soil_temperature_units,
		'GSC_MIxS_soil_soil_texture_measurement_units': GSC_MIxS_soil_soil_texture_measurement_units,
		'GSC_MIxS_soil_organic_matter_units': GSC_MIxS_soil_organic_matter_units,
		'GSC_MIxS_soil_total_organic_carbon_units': GSC_MIxS_soil_total_organic_carbon_units,
		'GSC_MIxS_soil_water_content_units': GSC_MIxS_soil_water_content_units,
		'GSC_MIxS_soil_total_nitrogen_units': GSC_MIxS_soil_total_nitrogen_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_soil_slope_gradient = models.CharField(max_length=100, choices=GSC_MIxS_soil_slope_gradient_units, blank=False)
	GSC_MIxS_soil_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_soil_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_soil_altitude = models.CharField(max_length=100, choices=GSC_MIxS_soil_altitude_units, blank=False)
	GSC_MIxS_soil_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_soil_geographic_location_latitude_units, blank=False)
	GSC_MIxS_soil_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_soil_geographic_location_longitude_units, blank=False)
	GSC_MIxS_soil_depth = models.CharField(max_length=100, choices=GSC_MIxS_soil_depth_units, blank=False)
	GSC_MIxS_soil_elevation = models.CharField(max_length=100, choices=GSC_MIxS_soil_elevation_units, blank=False)
	GSC_MIxS_soil_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_soil_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_soil_sample_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_soil_sample_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_soil_microbial_biomass = models.CharField(max_length=100, choices=GSC_MIxS_soil_microbial_biomass_units, blank=False)
	GSC_MIxS_soil_extreme_unusual_properties_Al_saturation = models.CharField(max_length=100, choices=GSC_MIxS_soil_extreme_unusual_properties_Al_saturation_units, blank=False)
	GSC_MIxS_soil_mean_annual_and_seasonal_temperature = models.CharField(max_length=100, choices=GSC_MIxS_soil_mean_annual_and_seasonal_temperature_units, blank=False)
	GSC_MIxS_soil_mean_annual_and_seasonal_precipitation = models.CharField(max_length=100, choices=GSC_MIxS_soil_mean_annual_and_seasonal_precipitation_units, blank=False)
	GSC_MIxS_soil_temperature = models.CharField(max_length=100, choices=GSC_MIxS_soil_temperature_units, blank=False)
	GSC_MIxS_soil_soil_texture_measurement = models.CharField(max_length=100, choices=GSC_MIxS_soil_soil_texture_measurement_units, blank=False)
	GSC_MIxS_soil_organic_matter = models.CharField(max_length=100, choices=GSC_MIxS_soil_organic_matter_units, blank=False)
	GSC_MIxS_soil_total_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_soil_total_organic_carbon_units, blank=False)
	GSC_MIxS_soil_water_content = models.CharField(max_length=100, choices=GSC_MIxS_soil_water_content_units, blank=False)
	GSC_MIxS_soil_total_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_soil_total_nitrogen_units, blank=False)

class GSC_MIxS_human_gut(SelfDescribingModel):

	GSC_MIxS_human_gut_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_human_gut_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_human_gut_medical_history_performed_choice = [('No', 'No'), ('Yes', 'Yes')]
	GSC_MIxS_human_gut_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_human_gut_IHMC_medication_code_choice = [('01=1=Analgesics/NSAIDS', '01=1=Analgesics/NSAIDS'), ('02=2=Anesthetics', '02=2=Anesthetics'), ('03=3=Antacids/H2 antagonists', '03=3=Antacids/H2 antagonists'), ('04=4=Anti-acne', '04=4=Anti-acne'), ('05=5=Anti-asthma/bronchodilators', '05=5=Anti-asthma/bronchodilators'), ('06=6=Anti-cholesterol/Anti-hyperlipidemic', '06=6=Anti-cholesterol/Anti-hyperlipidemic'), ('07=7=Anti-coagulants', '07=7=Anti-coagulants'), ('08=8=Antibiotics/(anti)-infectives, parasitics, microbials', '08=8=Antibiotics/(anti)-infectives, parasitics, microbials'), ('09=9=Antidepressants/mood-altering drugs', '09=9=Antidepressants/mood-altering drugs'), ('10=10=Antihistamines/ Decongestants', '10=10=Antihistamines/ Decongestants'), ('11=11=Antihypertensives', '11=11=Antihypertensives'), ('12=12=Cardiovascular, other than hyperlipidemic/HTN', '12=12=Cardiovascular, other than hyperlipidemic/HTN'), ('13=13=Contraceptives (oral, implant, injectable)', '13=13=Contraceptives (oral, implant, injectable)'), ('14=14=Emergency/support medications', '14=14=Emergency/support medications'), ('15=15=Endocrine/Metabolic agents', '15=15=Endocrine/Metabolic agents'), ('16=16=GI meds (anti-diarrheal, emetic, spasmodics)', '16=16=GI meds (anti-diarrheal, emetic, spasmodics)'), ('17=17=Herbal/homeopathic products', '17=17=Herbal/homeopathic products'), ('18=18=Hormones/steroids', '18=18=Hormones/steroids'), ('19=19=OTC cold & flu', '19=19=OTC cold & flu'), ('20=20=Vaccine prophylaxis', '20=20=Vaccine prophylaxis'), ('21=21=Vitamins, minerals, food supplements', '21=21=Vitamins, minerals, food supplements'), ('99=99=Other', '99=99=Other')]
	GSC_MIxS_human_gut_host_occupation_choice = [('01=01 Accounting/Finance', '01=01 Accounting/Finance'), ('02=02 Advertising/Public Relations', '02=02 Advertising/Public Relations'), ('03=03 Arts/Entertainment/Publishing', '03=03 Arts/Entertainment/Publishing'), ('04=04 Automotive', '04=04 Automotive'), ('05=05 Banking/ Mortgage', '05=05 Banking/ Mortgage'), ('06=06 Biotech', '06=06 Biotech'), ('07=07 Broadcast/Journalism', '07=07 Broadcast/Journalism'), ('08=08 Business Development', '08=08 Business Development'), ('09=09 Clerical/Administrative', '09=09 Clerical/Administrative'), ('10=10 Construction/Trades', '10=10 Construction/Trades'), ('11=11 Consultant', '11=11 Consultant'), ('12=12 Customer Services', '12=12 Customer Services'), ('13=13 Design', '13=13 Design'), ('14=14 Education', '14=14 Education'), ('15=15 Engineering', '15=15 Engineering'), ('16=16 Entry Level', '16=16 Entry Level'), ('17=17 Executive', '17=17 Executive'), ('18=18 Food Service', '18=18 Food Service'), ('19=19 Government', '19=19 Government'), ('20=20 Grocery', '20=20 Grocery'), ('21=21 Healthcare', '21=21 Healthcare'), ('22=22 Hospitality', '22=22 Hospitality'), ('23=23 Human Resources', '23=23 Human Resources'), ('24=24 Information Technology', '24=24 Information Technology'), ('25=25 Insurance', '25=25 Insurance'), ('26=26 Law/Legal', '26=26 Law/Legal'), ('27=27 Management', '27=27 Management'), ('28=28 Manufacturing', '28=28 Manufacturing'), ('29=29 Marketing', '29=29 Marketing'), ('30=30 Pharmaceutical', '30=30 Pharmaceutical'), ('31=31 Professional Services', '31=31 Professional Services'), ('32=32 Purchasing', '32=32 Purchasing'), ('33=33 Quality Assurance (QA)', '33=33 Quality Assurance (QA)'), ('34=34 Research', '34=34 Research'), ('35=35 Restaurant', '35=35 Restaurant'), ('36=36 Retail', '36=36 Retail'), ('37=37 Sales', '37=37 Sales'), ('38=38 Science', '38=38 Science'), ('39=39 Security/Law Enforcement', '39=39 Security/Law Enforcement'), ('40=40 Shipping/Distribution', '40=40 Shipping/Distribution'), ('41=41 Strategy', '41=41 Strategy'), ('42=42 Student', '42=42 Student'), ('43=43 Telecommunications', '43=43 Telecommunications'), ('44=44 Training', '44=44 Training'), ('45=45 Transportation', '45=45 Transportation'), ('46=46 Warehouse', '46=46 Warehouse'), ('47=47 Other', '47=47 Other'), ('99=99 Unknown/Refused', '99=99 Unknown/Refused')]
	GSC_MIxS_human_gut_host_sex_choice = [('female', 'female'), ('hermaphrodite', 'hermaphrodite'), ('male', 'male'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('neuter', 'neuter'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('other', 'other'), ('restricted access', 'restricted access')]
	GSC_MIxS_human_gut_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_human_gut_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_human_gut_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_human_gut_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_gut_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_gut_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_gut_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_gut_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_gut_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_gut_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_gut_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_gut_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_gut_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_gut_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_gut_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_gut_host_age_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_gut_host_height_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_gut_host_body_mass_index_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_gut_host_total_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_gut_host_body_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_gut_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_gut_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_gut_host_pulse_validator = "[+-]?[0-9]+"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_human_gut_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_human_gut_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_human_gut_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_human_gut_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_human_gut_number_of_replicons_validator)])
	GSC_MIxS_human_gut_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_human_gut_extrachromosomal_elements_validator)])
	GSC_MIxS_human_gut_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_human_gut_estimated_size_validator)])
	GSC_MIxS_human_gut_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_human_gut_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_human_gut_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_human_gut_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_human_gut_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_human_gut_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_human_gut_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_human_gut_library_size_validator)])
	GSC_MIxS_human_gut_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_human_gut_library_reads_sequenced_validator)])
	GSC_MIxS_human_gut_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_human_gut_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_human_gut_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_human_gut_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_human_gut_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_human_gut_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_human_gut_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_human_gut_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_human_gut_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_human_gut_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_human_gut_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_human_gut_sequence_quality_check_choice)
	GSC_MIxS_human_gut_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_human_gut_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_human_gut_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_human_gut_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_human_gut_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_human_gut_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_human_gut_collection_date_validator)])
	GSC_MIxS_human_gut_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_human_gut_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_human_gut_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_human_gut_geographic_location_latitude_validator)])
	GSC_MIxS_human_gut_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_human_gut_geographic_location_longitude_validator)])
	GSC_MIxS_human_gut_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_human_gut_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_gut_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_gut_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_gut_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_human_gut_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_human_gut_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_human_gut_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_human_gut_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_human_gut_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_human_gut_host_body_product= models.CharField(max_length=100, blank=True,help_text="substance ")
	GSC_MIxS_human_gut_medical_history_performed= models.CharField(max_length=100, blank=True,help_text="whether fu", choices=GSC_MIxS_human_gut_medical_history_performed_choice)
	GSC_MIxS_human_gut_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_human_gut_oxygenation_status_of_sample_choice)
	GSC_MIxS_human_gut_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_human_gut_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_human_gut_sample_storage_duration_validator)])
	GSC_MIxS_human_gut_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_human_gut_sample_storage_temperature_validator)])
	GSC_MIxS_human_gut_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_human_gut_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_human_gut_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_human_gut_gastrointestinal_tract_disorder= models.CharField(max_length=100, blank=True,help_text="History of")
	GSC_MIxS_human_gut_liver_disorder= models.CharField(max_length=100, blank=True,help_text="History of")
	GSC_MIxS_human_gut_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_human_gut_host_subject_id= models.CharField(max_length=100, blank=True,help_text="a unique i")
	GSC_MIxS_human_gut_IHMC_medication_code= models.CharField(max_length=100, blank=True,help_text="can includ", choices=GSC_MIxS_human_gut_IHMC_medication_code_choice)
	GSC_MIxS_human_gut_host_age= models.CharField(max_length=100, blank=True,help_text="age of hos", validators=[RegexValidator(GSC_MIxS_human_gut_host_age_validator)])
	GSC_MIxS_human_gut_host_body_site= models.CharField(max_length=100, blank=True,help_text="name of bo")
	GSC_MIxS_human_gut_host_height= models.CharField(max_length=100, blank=True,help_text="the height", validators=[RegexValidator(GSC_MIxS_human_gut_host_height_validator)])
	GSC_MIxS_human_gut_host_body_mass_index= models.CharField(max_length=100, blank=True,help_text="body mass ", validators=[RegexValidator(GSC_MIxS_human_gut_host_body_mass_index_validator)])
	GSC_MIxS_human_gut_ethnicity= models.CharField(max_length=100, blank=True,help_text="A category")
	GSC_MIxS_human_gut_host_occupation= models.CharField(max_length=100, blank=True,help_text="most frequ", choices=GSC_MIxS_human_gut_host_occupation_choice)
	GSC_MIxS_human_gut_host_total_mass= models.CharField(max_length=100, blank=True,help_text="total mass", validators=[RegexValidator(GSC_MIxS_human_gut_host_total_mass_validator)])
	GSC_MIxS_human_gut_host_phenotype= models.CharField(max_length=100, blank=True,help_text="phenotype ")
	GSC_MIxS_human_gut_host_body_temperature= models.CharField(max_length=100, blank=True,help_text="core body ", validators=[RegexValidator(GSC_MIxS_human_gut_host_body_temperature_validator)])
	GSC_MIxS_human_gut_host_sex= models.CharField(max_length=100, blank=True,help_text="Gender or ", choices=GSC_MIxS_human_gut_host_sex_choice)
	GSC_MIxS_human_gut_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_human_gut_temperature_validator)])
	GSC_MIxS_human_gut_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_human_gut_salinity_validator)])
	GSC_MIxS_human_gut_special_diet= models.CharField(max_length=100, blank=True,help_text="specificat")
	GSC_MIxS_human_gut_host_diet= models.CharField(max_length=100, blank=True,help_text="type of di")
	GSC_MIxS_human_gut_host_last_meal= models.CharField(max_length=100, blank=True,help_text="content of")
	GSC_MIxS_human_gut_host_family_relationship= models.CharField(max_length=100, blank=True,help_text="relationsh")
	GSC_MIxS_human_gut_host_genotype= models.CharField(max_length=100, blank=True,help_text="observed g")
	GSC_MIxS_human_gut_host_pulse= models.CharField(max_length=100, blank=True,help_text="resting pu", validators=[RegexValidator(GSC_MIxS_human_gut_host_pulse_validator)])
	GSC_MIxS_human_gut_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_human_gut_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_human_gut_trophic_level_choice)
	GSC_MIxS_human_gut_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_human_gut_relationship_to_oxygen_choice)
	GSC_MIxS_human_gut_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_human_gut_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_human_gut_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_human_gut_observed_biotic_relationship_choice)
	GSC_MIxS_human_gut_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_human_gut_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_human_gut_project_name': GSC_MIxS_human_gut_project_name,
		'GSC_MIxS_human_gut_experimental_factor': GSC_MIxS_human_gut_experimental_factor,
		'GSC_MIxS_human_gut_ploidy': GSC_MIxS_human_gut_ploidy,
		'GSC_MIxS_human_gut_number_of_replicons': GSC_MIxS_human_gut_number_of_replicons,
		'GSC_MIxS_human_gut_extrachromosomal_elements': GSC_MIxS_human_gut_extrachromosomal_elements,
		'GSC_MIxS_human_gut_estimated_size': GSC_MIxS_human_gut_estimated_size,
		'GSC_MIxS_human_gut_reference_for_biomaterial': GSC_MIxS_human_gut_reference_for_biomaterial,
		'GSC_MIxS_human_gut_annotation_source': GSC_MIxS_human_gut_annotation_source,
		'GSC_MIxS_human_gut_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_human_gut_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_human_gut_nucleic_acid_extraction': GSC_MIxS_human_gut_nucleic_acid_extraction,
		'GSC_MIxS_human_gut_nucleic_acid_amplification': GSC_MIxS_human_gut_nucleic_acid_amplification,
		'GSC_MIxS_human_gut_library_size': GSC_MIxS_human_gut_library_size,
		'GSC_MIxS_human_gut_library_reads_sequenced': GSC_MIxS_human_gut_library_reads_sequenced,
		'GSC_MIxS_human_gut_library_construction_method': GSC_MIxS_human_gut_library_construction_method,
		'GSC_MIxS_human_gut_library_vector': GSC_MIxS_human_gut_library_vector,
		'GSC_MIxS_human_gut_library_screening_strategy': GSC_MIxS_human_gut_library_screening_strategy,
		'GSC_MIxS_human_gut_target_gene': GSC_MIxS_human_gut_target_gene,
		'GSC_MIxS_human_gut_target_subfragment': GSC_MIxS_human_gut_target_subfragment,
		'GSC_MIxS_human_gut_pcr_primers': GSC_MIxS_human_gut_pcr_primers,
		'GSC_MIxS_human_gut_multiplex_identifiers': GSC_MIxS_human_gut_multiplex_identifiers,
		'GSC_MIxS_human_gut_adapters': GSC_MIxS_human_gut_adapters,
		'GSC_MIxS_human_gut_pcr_conditions': GSC_MIxS_human_gut_pcr_conditions,
		'GSC_MIxS_human_gut_sequencing_method': GSC_MIxS_human_gut_sequencing_method,
		'GSC_MIxS_human_gut_sequence_quality_check': GSC_MIxS_human_gut_sequence_quality_check,
		'GSC_MIxS_human_gut_chimera_check_software': GSC_MIxS_human_gut_chimera_check_software,
		'GSC_MIxS_human_gut_relevant_electronic_resources': GSC_MIxS_human_gut_relevant_electronic_resources,
		'GSC_MIxS_human_gut_relevant_standard_operating_procedures': GSC_MIxS_human_gut_relevant_standard_operating_procedures,
		'GSC_MIxS_human_gut_negative_control_type': GSC_MIxS_human_gut_negative_control_type,
		'GSC_MIxS_human_gut_positive_control_type': GSC_MIxS_human_gut_positive_control_type,
		'GSC_MIxS_human_gut_collection_date': GSC_MIxS_human_gut_collection_date,
		'GSC_MIxS_human_gut_geographic_location_country_and_or_sea': GSC_MIxS_human_gut_geographic_location_country_and_or_sea,
		'GSC_MIxS_human_gut_geographic_location_latitude': GSC_MIxS_human_gut_geographic_location_latitude,
		'GSC_MIxS_human_gut_geographic_location_longitude': GSC_MIxS_human_gut_geographic_location_longitude,
		'GSC_MIxS_human_gut_geographic_location_region_and_locality': GSC_MIxS_human_gut_geographic_location_region_and_locality,
		'GSC_MIxS_human_gut_broad_scale_environmental_context': GSC_MIxS_human_gut_broad_scale_environmental_context,
		'GSC_MIxS_human_gut_local_environmental_context': GSC_MIxS_human_gut_local_environmental_context,
		'GSC_MIxS_human_gut_environmental_medium': GSC_MIxS_human_gut_environmental_medium,
		'GSC_MIxS_human_gut_source_material_identifiers': GSC_MIxS_human_gut_source_material_identifiers,
		'GSC_MIxS_human_gut_sample_material_processing': GSC_MIxS_human_gut_sample_material_processing,
		'GSC_MIxS_human_gut_isolation_and_growth_condition': GSC_MIxS_human_gut_isolation_and_growth_condition,
		'GSC_MIxS_human_gut_propagation': GSC_MIxS_human_gut_propagation,
		'GSC_MIxS_human_gut_amount_or_size_of_sample_collected': GSC_MIxS_human_gut_amount_or_size_of_sample_collected,
		'GSC_MIxS_human_gut_host_body_product': GSC_MIxS_human_gut_host_body_product,
		'GSC_MIxS_human_gut_medical_history_performed': GSC_MIxS_human_gut_medical_history_performed,
		'GSC_MIxS_human_gut_oxygenation_status_of_sample': GSC_MIxS_human_gut_oxygenation_status_of_sample,
		'GSC_MIxS_human_gut_organism_count': GSC_MIxS_human_gut_organism_count,
		'GSC_MIxS_human_gut_sample_storage_duration': GSC_MIxS_human_gut_sample_storage_duration,
		'GSC_MIxS_human_gut_sample_storage_temperature': GSC_MIxS_human_gut_sample_storage_temperature,
		'GSC_MIxS_human_gut_sample_storage_location': GSC_MIxS_human_gut_sample_storage_location,
		'GSC_MIxS_human_gut_sample_collection_device': GSC_MIxS_human_gut_sample_collection_device,
		'GSC_MIxS_human_gut_sample_collection_method': GSC_MIxS_human_gut_sample_collection_method,
		'GSC_MIxS_human_gut_gastrointestinal_tract_disorder': GSC_MIxS_human_gut_gastrointestinal_tract_disorder,
		'GSC_MIxS_human_gut_liver_disorder': GSC_MIxS_human_gut_liver_disorder,
		'GSC_MIxS_human_gut_host_disease_status': GSC_MIxS_human_gut_host_disease_status,
		'GSC_MIxS_human_gut_host_subject_id': GSC_MIxS_human_gut_host_subject_id,
		'GSC_MIxS_human_gut_IHMC_medication_code': GSC_MIxS_human_gut_IHMC_medication_code,
		'GSC_MIxS_human_gut_host_age': GSC_MIxS_human_gut_host_age,
		'GSC_MIxS_human_gut_host_body_site': GSC_MIxS_human_gut_host_body_site,
		'GSC_MIxS_human_gut_host_height': GSC_MIxS_human_gut_host_height,
		'GSC_MIxS_human_gut_host_body_mass_index': GSC_MIxS_human_gut_host_body_mass_index,
		'GSC_MIxS_human_gut_ethnicity': GSC_MIxS_human_gut_ethnicity,
		'GSC_MIxS_human_gut_host_occupation': GSC_MIxS_human_gut_host_occupation,
		'GSC_MIxS_human_gut_host_total_mass': GSC_MIxS_human_gut_host_total_mass,
		'GSC_MIxS_human_gut_host_phenotype': GSC_MIxS_human_gut_host_phenotype,
		'GSC_MIxS_human_gut_host_body_temperature': GSC_MIxS_human_gut_host_body_temperature,
		'GSC_MIxS_human_gut_host_sex': GSC_MIxS_human_gut_host_sex,
		'GSC_MIxS_human_gut_temperature': GSC_MIxS_human_gut_temperature,
		'GSC_MIxS_human_gut_salinity': GSC_MIxS_human_gut_salinity,
		'GSC_MIxS_human_gut_special_diet': GSC_MIxS_human_gut_special_diet,
		'GSC_MIxS_human_gut_host_diet': GSC_MIxS_human_gut_host_diet,
		'GSC_MIxS_human_gut_host_last_meal': GSC_MIxS_human_gut_host_last_meal,
		'GSC_MIxS_human_gut_host_family_relationship': GSC_MIxS_human_gut_host_family_relationship,
		'GSC_MIxS_human_gut_host_genotype': GSC_MIxS_human_gut_host_genotype,
		'GSC_MIxS_human_gut_host_pulse': GSC_MIxS_human_gut_host_pulse,
		'GSC_MIxS_human_gut_subspecific_genetic_lineage': GSC_MIxS_human_gut_subspecific_genetic_lineage,
		'GSC_MIxS_human_gut_trophic_level': GSC_MIxS_human_gut_trophic_level,
		'GSC_MIxS_human_gut_relationship_to_oxygen': GSC_MIxS_human_gut_relationship_to_oxygen,
		'GSC_MIxS_human_gut_known_pathogenicity': GSC_MIxS_human_gut_known_pathogenicity,
		'GSC_MIxS_human_gut_encoded_traits': GSC_MIxS_human_gut_encoded_traits,
		'GSC_MIxS_human_gut_observed_biotic_relationship': GSC_MIxS_human_gut_observed_biotic_relationship,
		'GSC_MIxS_human_gut_chemical_administration': GSC_MIxS_human_gut_chemical_administration,
		'GSC_MIxS_human_gut_perturbation': GSC_MIxS_human_gut_perturbation,
	}

class GSC_MIxS_human_gut_unit(SelfDescribingModel):

	GSC_MIxS_human_gut_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_human_gut_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_human_gut_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_human_gut_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_human_gut_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_human_gut_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_human_gut_host_age_units = [('centuries', 'centuries'), ('days', 'days'), ('decades', 'decades'), ('hours', 'hours'), ('minutes', 'minutes'), ('months', 'months'), ('seconds', 'seconds'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_human_gut_host_height_units = [('cm', 'cm'), ('m', 'm'), ('mm', 'mm')]
	GSC_MIxS_human_gut_host_body_mass_index_units = [('k', 'k'), ('g', 'g'), ('/', '/'), ('m', 'm'), ('2', '2')]
	GSC_MIxS_human_gut_host_total_mass_units = [('g', 'g'), ('kg', 'kg')]
	GSC_MIxS_human_gut_host_body_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_human_gut_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_human_gut_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]
	GSC_MIxS_human_gut_host_pulse_units = [('b', 'b'), ('p', 'p'), ('m', 'm')]

	fields = {
		'GSC_MIxS_human_gut_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_human_gut_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_human_gut_geographic_location_latitude_units': GSC_MIxS_human_gut_geographic_location_latitude_units,
		'GSC_MIxS_human_gut_geographic_location_longitude_units': GSC_MIxS_human_gut_geographic_location_longitude_units,
		'GSC_MIxS_human_gut_amount_or_size_of_sample_collected_units': GSC_MIxS_human_gut_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_human_gut_sample_storage_duration_units': GSC_MIxS_human_gut_sample_storage_duration_units,
		'GSC_MIxS_human_gut_sample_storage_temperature_units': GSC_MIxS_human_gut_sample_storage_temperature_units,
		'GSC_MIxS_human_gut_host_age_units': GSC_MIxS_human_gut_host_age_units,
		'GSC_MIxS_human_gut_host_height_units': GSC_MIxS_human_gut_host_height_units,
		'GSC_MIxS_human_gut_host_body_mass_index_units': GSC_MIxS_human_gut_host_body_mass_index_units,
		'GSC_MIxS_human_gut_host_total_mass_units': GSC_MIxS_human_gut_host_total_mass_units,
		'GSC_MIxS_human_gut_host_body_temperature_units': GSC_MIxS_human_gut_host_body_temperature_units,
		'GSC_MIxS_human_gut_temperature_units': GSC_MIxS_human_gut_temperature_units,
		'GSC_MIxS_human_gut_salinity_units': GSC_MIxS_human_gut_salinity_units,
		'GSC_MIxS_human_gut_host_pulse_units': GSC_MIxS_human_gut_host_pulse_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_human_gut_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_human_gut_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_geographic_location_latitude_units, blank=False)
	GSC_MIxS_human_gut_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_geographic_location_longitude_units, blank=False)
	GSC_MIxS_human_gut_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_human_gut_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_sample_storage_duration_units, blank=False)
	GSC_MIxS_human_gut_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_sample_storage_temperature_units, blank=False)
	GSC_MIxS_human_gut_host_age = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_host_age_units, blank=False)
	GSC_MIxS_human_gut_host_height = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_host_height_units, blank=False)
	GSC_MIxS_human_gut_host_body_mass_index = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_host_body_mass_index_units, blank=False)
	GSC_MIxS_human_gut_host_total_mass = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_host_total_mass_units, blank=False)
	GSC_MIxS_human_gut_host_body_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_host_body_temperature_units, blank=False)
	GSC_MIxS_human_gut_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_temperature_units, blank=False)
	GSC_MIxS_human_gut_salinity = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_salinity_units, blank=False)
	GSC_MIxS_human_gut_host_pulse = models.CharField(max_length=100, choices=GSC_MIxS_human_gut_host_pulse_units, blank=False)

class GSC_MIxS_host_associated(SelfDescribingModel):

	GSC_MIxS_host_associated_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_host_associated_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_host_associated_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_host_associated_host_sex_choice = [('female', 'female'), ('hermaphrodite', 'hermaphrodite'), ('male', 'male'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('neuter', 'neuter'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('other', 'other'), ('restricted access', 'restricted access')]
	GSC_MIxS_host_associated_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_host_associated_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_host_associated_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_host_associated_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_host_associated_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_host_associated_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_host_associated_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_host_associated_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_host_associated_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_host_associated_altitude_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_host_associated_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_host_associated_depth_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_elevation_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_host_dry_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_host_age_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_host_taxid_validator = "[+-]?[0-9]+"
	GSC_MIxS_host_associated_host_height_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_host_length_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_host_total_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_host_body_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_host_blood_pressure_diastolic_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_host_associated_host_blood_pressure_systolic_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_host_associated_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_host_associated_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_host_associated_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_host_associated_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_host_associated_number_of_replicons_validator)])
	GSC_MIxS_host_associated_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_host_associated_extrachromosomal_elements_validator)])
	GSC_MIxS_host_associated_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_host_associated_estimated_size_validator)])
	GSC_MIxS_host_associated_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_host_associated_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_host_associated_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_host_associated_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_host_associated_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_host_associated_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_host_associated_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_host_associated_library_size_validator)])
	GSC_MIxS_host_associated_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_host_associated_library_reads_sequenced_validator)])
	GSC_MIxS_host_associated_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_host_associated_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_host_associated_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_host_associated_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_host_associated_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_host_associated_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_host_associated_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_host_associated_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_host_associated_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_host_associated_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_host_associated_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_host_associated_sequence_quality_check_choice)
	GSC_MIxS_host_associated_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_host_associated_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_host_associated_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_host_associated_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_host_associated_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_host_associated_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_host_associated_collection_date_validator)])
	GSC_MIxS_host_associated_altitude= models.CharField(max_length=100, blank=True,help_text="The altitu", validators=[RegexValidator(GSC_MIxS_host_associated_altitude_validator)])
	GSC_MIxS_host_associated_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_host_associated_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_host_associated_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_host_associated_geographic_location_latitude_validator)])
	GSC_MIxS_host_associated_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_host_associated_geographic_location_longitude_validator)])
	GSC_MIxS_host_associated_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_host_associated_depth= models.CharField(max_length=100, blank=True,help_text="The vertic", validators=[RegexValidator(GSC_MIxS_host_associated_depth_validator)])
	GSC_MIxS_host_associated_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_host_associated_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_host_associated_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_host_associated_elevation= models.CharField(max_length=100, blank=True,help_text="The elevat", validators=[RegexValidator(GSC_MIxS_host_associated_elevation_validator)])
	GSC_MIxS_host_associated_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_host_associated_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_host_associated_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_host_associated_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_host_associated_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_host_associated_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_host_associated_host_body_product= models.CharField(max_length=100, blank=True,help_text="substance ")
	GSC_MIxS_host_associated_host_dry_mass= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_host_associated_host_dry_mass_validator)])
	GSC_MIxS_host_associated_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_host_associated_oxygenation_status_of_sample_choice)
	GSC_MIxS_host_associated_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_host_associated_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_host_associated_sample_storage_duration_validator)])
	GSC_MIxS_host_associated_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_host_associated_sample_storage_temperature_validator)])
	GSC_MIxS_host_associated_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_host_associated_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_host_associated_host_common_name= models.CharField(max_length=100, blank=True,help_text="common nam")
	GSC_MIxS_host_associated_host_subject_id= models.CharField(max_length=100, blank=True,help_text="a unique i")
	GSC_MIxS_host_associated_host_age= models.CharField(max_length=100, blank=True,help_text="age of hos", validators=[RegexValidator(GSC_MIxS_host_associated_host_age_validator)])
	GSC_MIxS_host_associated_host_taxid= models.CharField(max_length=100, blank=True,help_text="NCBI taxon", validators=[RegexValidator(GSC_MIxS_host_associated_host_taxid_validator)])
	GSC_MIxS_host_associated_host_body_habitat= models.CharField(max_length=100, blank=True,help_text="original b")
	GSC_MIxS_host_associated_host_body_site= models.CharField(max_length=100, blank=True,help_text="name of bo")
	GSC_MIxS_host_associated_host_life_stage= models.CharField(max_length=100, blank=True,help_text="descriptio")
	GSC_MIxS_host_associated_host_height= models.CharField(max_length=100, blank=True,help_text="the height", validators=[RegexValidator(GSC_MIxS_host_associated_host_height_validator)])
	GSC_MIxS_host_associated_host_length= models.CharField(max_length=100, blank=True,help_text="the length", validators=[RegexValidator(GSC_MIxS_host_associated_host_length_validator)])
	GSC_MIxS_host_associated_host_growth_conditions= models.CharField(max_length=100, blank=True,help_text="literature")
	GSC_MIxS_host_associated_host_substrate= models.CharField(max_length=100, blank=True,help_text="the growth")
	GSC_MIxS_host_associated_host_total_mass= models.CharField(max_length=100, blank=True,help_text="total mass", validators=[RegexValidator(GSC_MIxS_host_associated_host_total_mass_validator)])
	GSC_MIxS_host_associated_host_phenotype= models.CharField(max_length=100, blank=True,help_text="phenotype ")
	GSC_MIxS_host_associated_host_body_temperature= models.CharField(max_length=100, blank=True,help_text="core body ", validators=[RegexValidator(GSC_MIxS_host_associated_host_body_temperature_validator)])
	GSC_MIxS_host_associated_host_color= models.CharField(max_length=100, blank=True,help_text="the color ")
	GSC_MIxS_host_associated_host_shape= models.CharField(max_length=100, blank=True,help_text="morphologi")
	GSC_MIxS_host_associated_host_sex= models.CharField(max_length=100, blank=True,help_text="Gender or ", choices=GSC_MIxS_host_associated_host_sex_choice)
	GSC_MIxS_host_associated_host_scientific_name= models.CharField(max_length=100, blank=True,help_text="Scientific")
	GSC_MIxS_host_associated_host_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_host_associated_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_host_associated_temperature_validator)])
	GSC_MIxS_host_associated_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_host_associated_salinity_validator)])
	GSC_MIxS_host_associated_host_blood_pressure_diastolic= models.CharField(max_length=100, blank=True,help_text="resting di", validators=[RegexValidator(GSC_MIxS_host_associated_host_blood_pressure_diastolic_validator)])
	GSC_MIxS_host_associated_host_blood_pressure_systolic= models.CharField(max_length=100, blank=True,help_text="resting sy", validators=[RegexValidator(GSC_MIxS_host_associated_host_blood_pressure_systolic_validator)])
	GSC_MIxS_host_associated_host_diet= models.CharField(max_length=100, blank=True,help_text="type of di")
	GSC_MIxS_host_associated_host_last_meal= models.CharField(max_length=100, blank=True,help_text="content of")
	GSC_MIxS_host_associated_host_family_relationship= models.CharField(max_length=100, blank=True,help_text="relationsh")
	GSC_MIxS_host_associated_host_genotype= models.CharField(max_length=100, blank=True,help_text="observed g")
	GSC_MIxS_host_associated_gravidity= models.CharField(max_length=100, blank=True,help_text="Whether or")
	GSC_MIxS_host_associated_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_host_associated_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_host_associated_trophic_level_choice)
	GSC_MIxS_host_associated_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_host_associated_relationship_to_oxygen_choice)
	GSC_MIxS_host_associated_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_host_associated_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_host_associated_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_host_associated_observed_biotic_relationship_choice)
	GSC_MIxS_host_associated_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_host_associated_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_host_associated_project_name': GSC_MIxS_host_associated_project_name,
		'GSC_MIxS_host_associated_experimental_factor': GSC_MIxS_host_associated_experimental_factor,
		'GSC_MIxS_host_associated_ploidy': GSC_MIxS_host_associated_ploidy,
		'GSC_MIxS_host_associated_number_of_replicons': GSC_MIxS_host_associated_number_of_replicons,
		'GSC_MIxS_host_associated_extrachromosomal_elements': GSC_MIxS_host_associated_extrachromosomal_elements,
		'GSC_MIxS_host_associated_estimated_size': GSC_MIxS_host_associated_estimated_size,
		'GSC_MIxS_host_associated_reference_for_biomaterial': GSC_MIxS_host_associated_reference_for_biomaterial,
		'GSC_MIxS_host_associated_annotation_source': GSC_MIxS_host_associated_annotation_source,
		'GSC_MIxS_host_associated_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_host_associated_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_host_associated_nucleic_acid_extraction': GSC_MIxS_host_associated_nucleic_acid_extraction,
		'GSC_MIxS_host_associated_nucleic_acid_amplification': GSC_MIxS_host_associated_nucleic_acid_amplification,
		'GSC_MIxS_host_associated_library_size': GSC_MIxS_host_associated_library_size,
		'GSC_MIxS_host_associated_library_reads_sequenced': GSC_MIxS_host_associated_library_reads_sequenced,
		'GSC_MIxS_host_associated_library_construction_method': GSC_MIxS_host_associated_library_construction_method,
		'GSC_MIxS_host_associated_library_vector': GSC_MIxS_host_associated_library_vector,
		'GSC_MIxS_host_associated_library_screening_strategy': GSC_MIxS_host_associated_library_screening_strategy,
		'GSC_MIxS_host_associated_target_gene': GSC_MIxS_host_associated_target_gene,
		'GSC_MIxS_host_associated_target_subfragment': GSC_MIxS_host_associated_target_subfragment,
		'GSC_MIxS_host_associated_pcr_primers': GSC_MIxS_host_associated_pcr_primers,
		'GSC_MIxS_host_associated_multiplex_identifiers': GSC_MIxS_host_associated_multiplex_identifiers,
		'GSC_MIxS_host_associated_adapters': GSC_MIxS_host_associated_adapters,
		'GSC_MIxS_host_associated_pcr_conditions': GSC_MIxS_host_associated_pcr_conditions,
		'GSC_MIxS_host_associated_sequencing_method': GSC_MIxS_host_associated_sequencing_method,
		'GSC_MIxS_host_associated_sequence_quality_check': GSC_MIxS_host_associated_sequence_quality_check,
		'GSC_MIxS_host_associated_chimera_check_software': GSC_MIxS_host_associated_chimera_check_software,
		'GSC_MIxS_host_associated_relevant_electronic_resources': GSC_MIxS_host_associated_relevant_electronic_resources,
		'GSC_MIxS_host_associated_relevant_standard_operating_procedures': GSC_MIxS_host_associated_relevant_standard_operating_procedures,
		'GSC_MIxS_host_associated_negative_control_type': GSC_MIxS_host_associated_negative_control_type,
		'GSC_MIxS_host_associated_positive_control_type': GSC_MIxS_host_associated_positive_control_type,
		'GSC_MIxS_host_associated_collection_date': GSC_MIxS_host_associated_collection_date,
		'GSC_MIxS_host_associated_altitude': GSC_MIxS_host_associated_altitude,
		'GSC_MIxS_host_associated_geographic_location_country_and_or_sea': GSC_MIxS_host_associated_geographic_location_country_and_or_sea,
		'GSC_MIxS_host_associated_geographic_location_latitude': GSC_MIxS_host_associated_geographic_location_latitude,
		'GSC_MIxS_host_associated_geographic_location_longitude': GSC_MIxS_host_associated_geographic_location_longitude,
		'GSC_MIxS_host_associated_geographic_location_region_and_locality': GSC_MIxS_host_associated_geographic_location_region_and_locality,
		'GSC_MIxS_host_associated_depth': GSC_MIxS_host_associated_depth,
		'GSC_MIxS_host_associated_broad_scale_environmental_context': GSC_MIxS_host_associated_broad_scale_environmental_context,
		'GSC_MIxS_host_associated_local_environmental_context': GSC_MIxS_host_associated_local_environmental_context,
		'GSC_MIxS_host_associated_environmental_medium': GSC_MIxS_host_associated_environmental_medium,
		'GSC_MIxS_host_associated_elevation': GSC_MIxS_host_associated_elevation,
		'GSC_MIxS_host_associated_source_material_identifiers': GSC_MIxS_host_associated_source_material_identifiers,
		'GSC_MIxS_host_associated_sample_material_processing': GSC_MIxS_host_associated_sample_material_processing,
		'GSC_MIxS_host_associated_isolation_and_growth_condition': GSC_MIxS_host_associated_isolation_and_growth_condition,
		'GSC_MIxS_host_associated_propagation': GSC_MIxS_host_associated_propagation,
		'GSC_MIxS_host_associated_amount_or_size_of_sample_collected': GSC_MIxS_host_associated_amount_or_size_of_sample_collected,
		'GSC_MIxS_host_associated_host_body_product': GSC_MIxS_host_associated_host_body_product,
		'GSC_MIxS_host_associated_host_dry_mass': GSC_MIxS_host_associated_host_dry_mass,
		'GSC_MIxS_host_associated_oxygenation_status_of_sample': GSC_MIxS_host_associated_oxygenation_status_of_sample,
		'GSC_MIxS_host_associated_organism_count': GSC_MIxS_host_associated_organism_count,
		'GSC_MIxS_host_associated_sample_storage_duration': GSC_MIxS_host_associated_sample_storage_duration,
		'GSC_MIxS_host_associated_sample_storage_temperature': GSC_MIxS_host_associated_sample_storage_temperature,
		'GSC_MIxS_host_associated_sample_storage_location': GSC_MIxS_host_associated_sample_storage_location,
		'GSC_MIxS_host_associated_host_disease_status': GSC_MIxS_host_associated_host_disease_status,
		'GSC_MIxS_host_associated_host_common_name': GSC_MIxS_host_associated_host_common_name,
		'GSC_MIxS_host_associated_host_subject_id': GSC_MIxS_host_associated_host_subject_id,
		'GSC_MIxS_host_associated_host_age': GSC_MIxS_host_associated_host_age,
		'GSC_MIxS_host_associated_host_taxid': GSC_MIxS_host_associated_host_taxid,
		'GSC_MIxS_host_associated_host_body_habitat': GSC_MIxS_host_associated_host_body_habitat,
		'GSC_MIxS_host_associated_host_body_site': GSC_MIxS_host_associated_host_body_site,
		'GSC_MIxS_host_associated_host_life_stage': GSC_MIxS_host_associated_host_life_stage,
		'GSC_MIxS_host_associated_host_height': GSC_MIxS_host_associated_host_height,
		'GSC_MIxS_host_associated_host_length': GSC_MIxS_host_associated_host_length,
		'GSC_MIxS_host_associated_host_growth_conditions': GSC_MIxS_host_associated_host_growth_conditions,
		'GSC_MIxS_host_associated_host_substrate': GSC_MIxS_host_associated_host_substrate,
		'GSC_MIxS_host_associated_host_total_mass': GSC_MIxS_host_associated_host_total_mass,
		'GSC_MIxS_host_associated_host_phenotype': GSC_MIxS_host_associated_host_phenotype,
		'GSC_MIxS_host_associated_host_body_temperature': GSC_MIxS_host_associated_host_body_temperature,
		'GSC_MIxS_host_associated_host_color': GSC_MIxS_host_associated_host_color,
		'GSC_MIxS_host_associated_host_shape': GSC_MIxS_host_associated_host_shape,
		'GSC_MIxS_host_associated_host_sex': GSC_MIxS_host_associated_host_sex,
		'GSC_MIxS_host_associated_host_scientific_name': GSC_MIxS_host_associated_host_scientific_name,
		'GSC_MIxS_host_associated_host_subspecific_genetic_lineage': GSC_MIxS_host_associated_host_subspecific_genetic_lineage,
		'GSC_MIxS_host_associated_temperature': GSC_MIxS_host_associated_temperature,
		'GSC_MIxS_host_associated_salinity': GSC_MIxS_host_associated_salinity,
		'GSC_MIxS_host_associated_host_blood_pressure_diastolic': GSC_MIxS_host_associated_host_blood_pressure_diastolic,
		'GSC_MIxS_host_associated_host_blood_pressure_systolic': GSC_MIxS_host_associated_host_blood_pressure_systolic,
		'GSC_MIxS_host_associated_host_diet': GSC_MIxS_host_associated_host_diet,
		'GSC_MIxS_host_associated_host_last_meal': GSC_MIxS_host_associated_host_last_meal,
		'GSC_MIxS_host_associated_host_family_relationship': GSC_MIxS_host_associated_host_family_relationship,
		'GSC_MIxS_host_associated_host_genotype': GSC_MIxS_host_associated_host_genotype,
		'GSC_MIxS_host_associated_gravidity': GSC_MIxS_host_associated_gravidity,
		'GSC_MIxS_host_associated_subspecific_genetic_lineage': GSC_MIxS_host_associated_subspecific_genetic_lineage,
		'GSC_MIxS_host_associated_trophic_level': GSC_MIxS_host_associated_trophic_level,
		'GSC_MIxS_host_associated_relationship_to_oxygen': GSC_MIxS_host_associated_relationship_to_oxygen,
		'GSC_MIxS_host_associated_known_pathogenicity': GSC_MIxS_host_associated_known_pathogenicity,
		'GSC_MIxS_host_associated_encoded_traits': GSC_MIxS_host_associated_encoded_traits,
		'GSC_MIxS_host_associated_observed_biotic_relationship': GSC_MIxS_host_associated_observed_biotic_relationship,
		'GSC_MIxS_host_associated_chemical_administration': GSC_MIxS_host_associated_chemical_administration,
		'GSC_MIxS_host_associated_perturbation': GSC_MIxS_host_associated_perturbation,
	}

class GSC_MIxS_host_associated_unit(SelfDescribingModel):

	GSC_MIxS_host_associated_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_host_associated_altitude_units = [('m', 'm')]
	GSC_MIxS_host_associated_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_host_associated_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_host_associated_depth_units = [('m', 'm')]
	GSC_MIxS_host_associated_elevation_units = [('m', 'm')]
	GSC_MIxS_host_associated_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_host_associated_host_dry_mass_units = [('g', 'g'), ('kg', 'kg'), ('mg', 'mg')]
	GSC_MIxS_host_associated_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_host_associated_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_host_associated_host_age_units = [('centuries', 'centuries'), ('days', 'days'), ('decades', 'decades'), ('hours', 'hours'), ('minutes', 'minutes'), ('months', 'months'), ('seconds', 'seconds'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_host_associated_host_height_units = [('cm', 'cm'), ('m', 'm'), ('mm', 'mm')]
	GSC_MIxS_host_associated_host_length_units = [('cm', 'cm'), ('m', 'm'), ('mm', 'mm')]
	GSC_MIxS_host_associated_host_total_mass_units = [('g', 'g'), ('kg', 'kg')]
	GSC_MIxS_host_associated_host_body_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_host_associated_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_host_associated_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]
	GSC_MIxS_host_associated_host_blood_pressure_diastolic_units = [('m', 'm'), ('m', 'm'), (' ', ' '), ('H', 'H'), ('g', 'g')]
	GSC_MIxS_host_associated_host_blood_pressure_systolic_units = [('m', 'm'), ('m', 'm'), (' ', ' '), ('H', 'H'), ('g', 'g')]

	fields = {
		'GSC_MIxS_host_associated_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_host_associated_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_host_associated_altitude_units': GSC_MIxS_host_associated_altitude_units,
		'GSC_MIxS_host_associated_geographic_location_latitude_units': GSC_MIxS_host_associated_geographic_location_latitude_units,
		'GSC_MIxS_host_associated_geographic_location_longitude_units': GSC_MIxS_host_associated_geographic_location_longitude_units,
		'GSC_MIxS_host_associated_depth_units': GSC_MIxS_host_associated_depth_units,
		'GSC_MIxS_host_associated_elevation_units': GSC_MIxS_host_associated_elevation_units,
		'GSC_MIxS_host_associated_amount_or_size_of_sample_collected_units': GSC_MIxS_host_associated_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_host_associated_host_dry_mass_units': GSC_MIxS_host_associated_host_dry_mass_units,
		'GSC_MIxS_host_associated_sample_storage_duration_units': GSC_MIxS_host_associated_sample_storage_duration_units,
		'GSC_MIxS_host_associated_sample_storage_temperature_units': GSC_MIxS_host_associated_sample_storage_temperature_units,
		'GSC_MIxS_host_associated_host_age_units': GSC_MIxS_host_associated_host_age_units,
		'GSC_MIxS_host_associated_host_height_units': GSC_MIxS_host_associated_host_height_units,
		'GSC_MIxS_host_associated_host_length_units': GSC_MIxS_host_associated_host_length_units,
		'GSC_MIxS_host_associated_host_total_mass_units': GSC_MIxS_host_associated_host_total_mass_units,
		'GSC_MIxS_host_associated_host_body_temperature_units': GSC_MIxS_host_associated_host_body_temperature_units,
		'GSC_MIxS_host_associated_temperature_units': GSC_MIxS_host_associated_temperature_units,
		'GSC_MIxS_host_associated_salinity_units': GSC_MIxS_host_associated_salinity_units,
		'GSC_MIxS_host_associated_host_blood_pressure_diastolic_units': GSC_MIxS_host_associated_host_blood_pressure_diastolic_units,
		'GSC_MIxS_host_associated_host_blood_pressure_systolic_units': GSC_MIxS_host_associated_host_blood_pressure_systolic_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_host_associated_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_host_associated_altitude = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_altitude_units, blank=False)
	GSC_MIxS_host_associated_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_geographic_location_latitude_units, blank=False)
	GSC_MIxS_host_associated_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_geographic_location_longitude_units, blank=False)
	GSC_MIxS_host_associated_depth = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_depth_units, blank=False)
	GSC_MIxS_host_associated_elevation = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_elevation_units, blank=False)
	GSC_MIxS_host_associated_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_host_associated_host_dry_mass = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_host_dry_mass_units, blank=False)
	GSC_MIxS_host_associated_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_sample_storage_duration_units, blank=False)
	GSC_MIxS_host_associated_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_sample_storage_temperature_units, blank=False)
	GSC_MIxS_host_associated_host_age = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_host_age_units, blank=False)
	GSC_MIxS_host_associated_host_height = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_host_height_units, blank=False)
	GSC_MIxS_host_associated_host_length = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_host_length_units, blank=False)
	GSC_MIxS_host_associated_host_total_mass = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_host_total_mass_units, blank=False)
	GSC_MIxS_host_associated_host_body_temperature = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_host_body_temperature_units, blank=False)
	GSC_MIxS_host_associated_temperature = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_temperature_units, blank=False)
	GSC_MIxS_host_associated_salinity = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_salinity_units, blank=False)
	GSC_MIxS_host_associated_host_blood_pressure_diastolic = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_host_blood_pressure_diastolic_units, blank=False)
	GSC_MIxS_host_associated_host_blood_pressure_systolic = models.CharField(max_length=100, choices=GSC_MIxS_host_associated_host_blood_pressure_systolic_units, blank=False)

class GSC_MIxS_human_vaginal(SelfDescribingModel):

	GSC_MIxS_human_vaginal_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_human_vaginal_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_human_vaginal_medical_history_performed_choice = [('No', 'No'), ('Yes', 'Yes')]
	GSC_MIxS_human_vaginal_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_human_vaginal_IHMC_medication_code_choice = [('01=1=Analgesics/NSAIDS', '01=1=Analgesics/NSAIDS'), ('02=2=Anesthetics', '02=2=Anesthetics'), ('03=3=Antacids/H2 antagonists', '03=3=Antacids/H2 antagonists'), ('04=4=Anti-acne', '04=4=Anti-acne'), ('05=5=Anti-asthma/bronchodilators', '05=5=Anti-asthma/bronchodilators'), ('06=6=Anti-cholesterol/Anti-hyperlipidemic', '06=6=Anti-cholesterol/Anti-hyperlipidemic'), ('07=7=Anti-coagulants', '07=7=Anti-coagulants'), ('08=8=Antibiotics/(anti)-infectives, parasitics, microbials', '08=8=Antibiotics/(anti)-infectives, parasitics, microbials'), ('09=9=Antidepressants/mood-altering drugs', '09=9=Antidepressants/mood-altering drugs'), ('10=10=Antihistamines/ Decongestants', '10=10=Antihistamines/ Decongestants'), ('11=11=Antihypertensives', '11=11=Antihypertensives'), ('12=12=Cardiovascular, other than hyperlipidemic/HTN', '12=12=Cardiovascular, other than hyperlipidemic/HTN'), ('13=13=Contraceptives (oral, implant, injectable)', '13=13=Contraceptives (oral, implant, injectable)'), ('14=14=Emergency/support medications', '14=14=Emergency/support medications'), ('15=15=Endocrine/Metabolic agents', '15=15=Endocrine/Metabolic agents'), ('16=16=GI meds (anti-diarrheal, emetic, spasmodics)', '16=16=GI meds (anti-diarrheal, emetic, spasmodics)'), ('17=17=Herbal/homeopathic products', '17=17=Herbal/homeopathic products'), ('18=18=Hormones/steroids', '18=18=Hormones/steroids'), ('19=19=OTC cold & flu', '19=19=OTC cold & flu'), ('20=20=Vaccine prophylaxis', '20=20=Vaccine prophylaxis'), ('21=21=Vitamins, minerals, food supplements', '21=21=Vitamins, minerals, food supplements'), ('99=99=Other', '99=99=Other')]
	GSC_MIxS_human_vaginal_host_occupation_choice = [('01=01 Accounting/Finance', '01=01 Accounting/Finance'), ('02=02 Advertising/Public Relations', '02=02 Advertising/Public Relations'), ('03=03 Arts/Entertainment/Publishing', '03=03 Arts/Entertainment/Publishing'), ('04=04 Automotive', '04=04 Automotive'), ('05=05 Banking/ Mortgage', '05=05 Banking/ Mortgage'), ('06=06 Biotech', '06=06 Biotech'), ('07=07 Broadcast/Journalism', '07=07 Broadcast/Journalism'), ('08=08 Business Development', '08=08 Business Development'), ('09=09 Clerical/Administrative', '09=09 Clerical/Administrative'), ('10=10 Construction/Trades', '10=10 Construction/Trades'), ('11=11 Consultant', '11=11 Consultant'), ('12=12 Customer Services', '12=12 Customer Services'), ('13=13 Design', '13=13 Design'), ('14=14 Education', '14=14 Education'), ('15=15 Engineering', '15=15 Engineering'), ('16=16 Entry Level', '16=16 Entry Level'), ('17=17 Executive', '17=17 Executive'), ('18=18 Food Service', '18=18 Food Service'), ('19=19 Government', '19=19 Government'), ('20=20 Grocery', '20=20 Grocery'), ('21=21 Healthcare', '21=21 Healthcare'), ('22=22 Hospitality', '22=22 Hospitality'), ('23=23 Human Resources', '23=23 Human Resources'), ('24=24 Information Technology', '24=24 Information Technology'), ('25=25 Insurance', '25=25 Insurance'), ('26=26 Law/Legal', '26=26 Law/Legal'), ('27=27 Management', '27=27 Management'), ('28=28 Manufacturing', '28=28 Manufacturing'), ('29=29 Marketing', '29=29 Marketing'), ('30=30 Pharmaceutical', '30=30 Pharmaceutical'), ('31=31 Professional Services', '31=31 Professional Services'), ('32=32 Purchasing', '32=32 Purchasing'), ('33=33 Quality Assurance (QA)', '33=33 Quality Assurance (QA)'), ('34=34 Research', '34=34 Research'), ('35=35 Restaurant', '35=35 Restaurant'), ('36=36 Retail', '36=36 Retail'), ('37=37 Sales', '37=37 Sales'), ('38=38 Science', '38=38 Science'), ('39=39 Security/Law Enforcement', '39=39 Security/Law Enforcement'), ('40=40 Shipping/Distribution', '40=40 Shipping/Distribution'), ('41=41 Strategy', '41=41 Strategy'), ('42=42 Student', '42=42 Student'), ('43=43 Telecommunications', '43=43 Telecommunications'), ('44=44 Training', '44=44 Training'), ('45=45 Transportation', '45=45 Transportation'), ('46=46 Warehouse', '46=46 Warehouse'), ('47=47 Other', '47=47 Other'), ('99=99 Unknown/Refused', '99=99 Unknown/Refused')]
	GSC_MIxS_human_vaginal_host_sex_choice = [('female', 'female'), ('hermaphrodite', 'hermaphrodite'), ('male', 'male'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('neuter', 'neuter'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('other', 'other'), ('restricted access', 'restricted access')]
	GSC_MIxS_human_vaginal_hysterectomy_choice = [('No', 'No'), ('Yes', 'Yes')]
	GSC_MIxS_human_vaginal_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_human_vaginal_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_human_vaginal_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_human_vaginal_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_vaginal_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_vaginal_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_vaginal_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_vaginal_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_vaginal_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_vaginal_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_vaginal_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_vaginal_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_vaginal_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_vaginal_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_vaginal_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_vaginal_host_age_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_vaginal_host_height_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_vaginal_host_body_mass_index_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_vaginal_host_total_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_vaginal_host_body_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_vaginal_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_vaginal_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_vaginal_host_pulse_validator = "[+-]?[0-9]+"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_human_vaginal_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_human_vaginal_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_human_vaginal_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_human_vaginal_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_human_vaginal_number_of_replicons_validator)])
	GSC_MIxS_human_vaginal_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_human_vaginal_extrachromosomal_elements_validator)])
	GSC_MIxS_human_vaginal_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_human_vaginal_estimated_size_validator)])
	GSC_MIxS_human_vaginal_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_human_vaginal_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_human_vaginal_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_human_vaginal_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_human_vaginal_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_human_vaginal_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_human_vaginal_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_human_vaginal_library_size_validator)])
	GSC_MIxS_human_vaginal_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_human_vaginal_library_reads_sequenced_validator)])
	GSC_MIxS_human_vaginal_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_human_vaginal_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_human_vaginal_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_human_vaginal_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_human_vaginal_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_human_vaginal_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_human_vaginal_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_human_vaginal_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_human_vaginal_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_human_vaginal_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_human_vaginal_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_human_vaginal_sequence_quality_check_choice)
	GSC_MIxS_human_vaginal_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_human_vaginal_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_human_vaginal_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_human_vaginal_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_human_vaginal_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_human_vaginal_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_human_vaginal_collection_date_validator)])
	GSC_MIxS_human_vaginal_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_human_vaginal_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_human_vaginal_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_human_vaginal_geographic_location_latitude_validator)])
	GSC_MIxS_human_vaginal_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_human_vaginal_geographic_location_longitude_validator)])
	GSC_MIxS_human_vaginal_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_human_vaginal_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_vaginal_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_vaginal_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_vaginal_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_human_vaginal_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_human_vaginal_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_human_vaginal_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_human_vaginal_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_human_vaginal_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_human_vaginal_host_body_product= models.CharField(max_length=100, blank=True,help_text="substance ")
	GSC_MIxS_human_vaginal_medical_history_performed= models.CharField(max_length=100, blank=True,help_text="whether fu", choices=GSC_MIxS_human_vaginal_medical_history_performed_choice)
	GSC_MIxS_human_vaginal_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_human_vaginal_oxygenation_status_of_sample_choice)
	GSC_MIxS_human_vaginal_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_human_vaginal_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_human_vaginal_sample_storage_duration_validator)])
	GSC_MIxS_human_vaginal_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_human_vaginal_sample_storage_temperature_validator)])
	GSC_MIxS_human_vaginal_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_human_vaginal_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_human_vaginal_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_human_vaginal_gynecological_disorder= models.CharField(max_length=100, blank=True,help_text="History of")
	GSC_MIxS_human_vaginal_urogenital_disorder= models.CharField(max_length=100, blank=True,help_text="History of")
	GSC_MIxS_human_vaginal_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_human_vaginal_host_subject_id= models.CharField(max_length=100, blank=True,help_text="a unique i")
	GSC_MIxS_human_vaginal_IHMC_medication_code= models.CharField(max_length=100, blank=True,help_text="can includ", choices=GSC_MIxS_human_vaginal_IHMC_medication_code_choice)
	GSC_MIxS_human_vaginal_host_age= models.CharField(max_length=100, blank=True,help_text="age of hos", validators=[RegexValidator(GSC_MIxS_human_vaginal_host_age_validator)])
	GSC_MIxS_human_vaginal_host_body_site= models.CharField(max_length=100, blank=True,help_text="name of bo")
	GSC_MIxS_human_vaginal_host_height= models.CharField(max_length=100, blank=True,help_text="the height", validators=[RegexValidator(GSC_MIxS_human_vaginal_host_height_validator)])
	GSC_MIxS_human_vaginal_host_body_mass_index= models.CharField(max_length=100, blank=True,help_text="body mass ", validators=[RegexValidator(GSC_MIxS_human_vaginal_host_body_mass_index_validator)])
	GSC_MIxS_human_vaginal_ethnicity= models.CharField(max_length=100, blank=True,help_text="A category")
	GSC_MIxS_human_vaginal_host_occupation= models.CharField(max_length=100, blank=True,help_text="most frequ", choices=GSC_MIxS_human_vaginal_host_occupation_choice)
	GSC_MIxS_human_vaginal_host_total_mass= models.CharField(max_length=100, blank=True,help_text="total mass", validators=[RegexValidator(GSC_MIxS_human_vaginal_host_total_mass_validator)])
	GSC_MIxS_human_vaginal_host_phenotype= models.CharField(max_length=100, blank=True,help_text="phenotype ")
	GSC_MIxS_human_vaginal_host_body_temperature= models.CharField(max_length=100, blank=True,help_text="core body ", validators=[RegexValidator(GSC_MIxS_human_vaginal_host_body_temperature_validator)])
	GSC_MIxS_human_vaginal_host_sex= models.CharField(max_length=100, blank=True,help_text="Gender or ", choices=GSC_MIxS_human_vaginal_host_sex_choice)
	GSC_MIxS_human_vaginal_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_human_vaginal_temperature_validator)])
	GSC_MIxS_human_vaginal_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_human_vaginal_salinity_validator)])
	GSC_MIxS_human_vaginal_menarche= models.CharField(max_length=100, blank=True,help_text="date of mo")
	GSC_MIxS_human_vaginal_sexual_activity= models.CharField(max_length=100, blank=True,help_text="current se")
	GSC_MIxS_human_vaginal_pregnancy= models.CharField(max_length=100, blank=True,help_text="date due o")
	GSC_MIxS_human_vaginal_douche= models.CharField(max_length=100, blank=True,help_text="date of mo")
	GSC_MIxS_human_vaginal_birth_control= models.CharField(max_length=100, blank=True,help_text="specificat")
	GSC_MIxS_human_vaginal_menopause= models.CharField(max_length=100, blank=True,help_text="date of on")
	GSC_MIxS_human_vaginal_HRT= models.CharField(max_length=100, blank=True,help_text="whether su")
	GSC_MIxS_human_vaginal_hysterectomy= models.CharField(max_length=100, blank=True,help_text="specificat", choices=GSC_MIxS_human_vaginal_hysterectomy_choice)
	GSC_MIxS_human_vaginal_host_diet= models.CharField(max_length=100, blank=True,help_text="type of di")
	GSC_MIxS_human_vaginal_host_last_meal= models.CharField(max_length=100, blank=True,help_text="content of")
	GSC_MIxS_human_vaginal_host_family_relationship= models.CharField(max_length=100, blank=True,help_text="relationsh")
	GSC_MIxS_human_vaginal_host_genotype= models.CharField(max_length=100, blank=True,help_text="observed g")
	GSC_MIxS_human_vaginal_host_pulse= models.CharField(max_length=100, blank=True,help_text="resting pu", validators=[RegexValidator(GSC_MIxS_human_vaginal_host_pulse_validator)])
	GSC_MIxS_human_vaginal_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_human_vaginal_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_human_vaginal_trophic_level_choice)
	GSC_MIxS_human_vaginal_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_human_vaginal_relationship_to_oxygen_choice)
	GSC_MIxS_human_vaginal_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_human_vaginal_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_human_vaginal_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_human_vaginal_observed_biotic_relationship_choice)
	GSC_MIxS_human_vaginal_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_human_vaginal_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_human_vaginal_project_name': GSC_MIxS_human_vaginal_project_name,
		'GSC_MIxS_human_vaginal_experimental_factor': GSC_MIxS_human_vaginal_experimental_factor,
		'GSC_MIxS_human_vaginal_ploidy': GSC_MIxS_human_vaginal_ploidy,
		'GSC_MIxS_human_vaginal_number_of_replicons': GSC_MIxS_human_vaginal_number_of_replicons,
		'GSC_MIxS_human_vaginal_extrachromosomal_elements': GSC_MIxS_human_vaginal_extrachromosomal_elements,
		'GSC_MIxS_human_vaginal_estimated_size': GSC_MIxS_human_vaginal_estimated_size,
		'GSC_MIxS_human_vaginal_reference_for_biomaterial': GSC_MIxS_human_vaginal_reference_for_biomaterial,
		'GSC_MIxS_human_vaginal_annotation_source': GSC_MIxS_human_vaginal_annotation_source,
		'GSC_MIxS_human_vaginal_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_human_vaginal_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_human_vaginal_nucleic_acid_extraction': GSC_MIxS_human_vaginal_nucleic_acid_extraction,
		'GSC_MIxS_human_vaginal_nucleic_acid_amplification': GSC_MIxS_human_vaginal_nucleic_acid_amplification,
		'GSC_MIxS_human_vaginal_library_size': GSC_MIxS_human_vaginal_library_size,
		'GSC_MIxS_human_vaginal_library_reads_sequenced': GSC_MIxS_human_vaginal_library_reads_sequenced,
		'GSC_MIxS_human_vaginal_library_construction_method': GSC_MIxS_human_vaginal_library_construction_method,
		'GSC_MIxS_human_vaginal_library_vector': GSC_MIxS_human_vaginal_library_vector,
		'GSC_MIxS_human_vaginal_library_screening_strategy': GSC_MIxS_human_vaginal_library_screening_strategy,
		'GSC_MIxS_human_vaginal_target_gene': GSC_MIxS_human_vaginal_target_gene,
		'GSC_MIxS_human_vaginal_target_subfragment': GSC_MIxS_human_vaginal_target_subfragment,
		'GSC_MIxS_human_vaginal_pcr_primers': GSC_MIxS_human_vaginal_pcr_primers,
		'GSC_MIxS_human_vaginal_multiplex_identifiers': GSC_MIxS_human_vaginal_multiplex_identifiers,
		'GSC_MIxS_human_vaginal_adapters': GSC_MIxS_human_vaginal_adapters,
		'GSC_MIxS_human_vaginal_pcr_conditions': GSC_MIxS_human_vaginal_pcr_conditions,
		'GSC_MIxS_human_vaginal_sequencing_method': GSC_MIxS_human_vaginal_sequencing_method,
		'GSC_MIxS_human_vaginal_sequence_quality_check': GSC_MIxS_human_vaginal_sequence_quality_check,
		'GSC_MIxS_human_vaginal_chimera_check_software': GSC_MIxS_human_vaginal_chimera_check_software,
		'GSC_MIxS_human_vaginal_relevant_electronic_resources': GSC_MIxS_human_vaginal_relevant_electronic_resources,
		'GSC_MIxS_human_vaginal_relevant_standard_operating_procedures': GSC_MIxS_human_vaginal_relevant_standard_operating_procedures,
		'GSC_MIxS_human_vaginal_negative_control_type': GSC_MIxS_human_vaginal_negative_control_type,
		'GSC_MIxS_human_vaginal_positive_control_type': GSC_MIxS_human_vaginal_positive_control_type,
		'GSC_MIxS_human_vaginal_collection_date': GSC_MIxS_human_vaginal_collection_date,
		'GSC_MIxS_human_vaginal_geographic_location_country_and_or_sea': GSC_MIxS_human_vaginal_geographic_location_country_and_or_sea,
		'GSC_MIxS_human_vaginal_geographic_location_latitude': GSC_MIxS_human_vaginal_geographic_location_latitude,
		'GSC_MIxS_human_vaginal_geographic_location_longitude': GSC_MIxS_human_vaginal_geographic_location_longitude,
		'GSC_MIxS_human_vaginal_geographic_location_region_and_locality': GSC_MIxS_human_vaginal_geographic_location_region_and_locality,
		'GSC_MIxS_human_vaginal_broad_scale_environmental_context': GSC_MIxS_human_vaginal_broad_scale_environmental_context,
		'GSC_MIxS_human_vaginal_local_environmental_context': GSC_MIxS_human_vaginal_local_environmental_context,
		'GSC_MIxS_human_vaginal_environmental_medium': GSC_MIxS_human_vaginal_environmental_medium,
		'GSC_MIxS_human_vaginal_source_material_identifiers': GSC_MIxS_human_vaginal_source_material_identifiers,
		'GSC_MIxS_human_vaginal_sample_material_processing': GSC_MIxS_human_vaginal_sample_material_processing,
		'GSC_MIxS_human_vaginal_isolation_and_growth_condition': GSC_MIxS_human_vaginal_isolation_and_growth_condition,
		'GSC_MIxS_human_vaginal_propagation': GSC_MIxS_human_vaginal_propagation,
		'GSC_MIxS_human_vaginal_amount_or_size_of_sample_collected': GSC_MIxS_human_vaginal_amount_or_size_of_sample_collected,
		'GSC_MIxS_human_vaginal_host_body_product': GSC_MIxS_human_vaginal_host_body_product,
		'GSC_MIxS_human_vaginal_medical_history_performed': GSC_MIxS_human_vaginal_medical_history_performed,
		'GSC_MIxS_human_vaginal_oxygenation_status_of_sample': GSC_MIxS_human_vaginal_oxygenation_status_of_sample,
		'GSC_MIxS_human_vaginal_organism_count': GSC_MIxS_human_vaginal_organism_count,
		'GSC_MIxS_human_vaginal_sample_storage_duration': GSC_MIxS_human_vaginal_sample_storage_duration,
		'GSC_MIxS_human_vaginal_sample_storage_temperature': GSC_MIxS_human_vaginal_sample_storage_temperature,
		'GSC_MIxS_human_vaginal_sample_storage_location': GSC_MIxS_human_vaginal_sample_storage_location,
		'GSC_MIxS_human_vaginal_sample_collection_device': GSC_MIxS_human_vaginal_sample_collection_device,
		'GSC_MIxS_human_vaginal_sample_collection_method': GSC_MIxS_human_vaginal_sample_collection_method,
		'GSC_MIxS_human_vaginal_gynecological_disorder': GSC_MIxS_human_vaginal_gynecological_disorder,
		'GSC_MIxS_human_vaginal_urogenital_disorder': GSC_MIxS_human_vaginal_urogenital_disorder,
		'GSC_MIxS_human_vaginal_host_disease_status': GSC_MIxS_human_vaginal_host_disease_status,
		'GSC_MIxS_human_vaginal_host_subject_id': GSC_MIxS_human_vaginal_host_subject_id,
		'GSC_MIxS_human_vaginal_IHMC_medication_code': GSC_MIxS_human_vaginal_IHMC_medication_code,
		'GSC_MIxS_human_vaginal_host_age': GSC_MIxS_human_vaginal_host_age,
		'GSC_MIxS_human_vaginal_host_body_site': GSC_MIxS_human_vaginal_host_body_site,
		'GSC_MIxS_human_vaginal_host_height': GSC_MIxS_human_vaginal_host_height,
		'GSC_MIxS_human_vaginal_host_body_mass_index': GSC_MIxS_human_vaginal_host_body_mass_index,
		'GSC_MIxS_human_vaginal_ethnicity': GSC_MIxS_human_vaginal_ethnicity,
		'GSC_MIxS_human_vaginal_host_occupation': GSC_MIxS_human_vaginal_host_occupation,
		'GSC_MIxS_human_vaginal_host_total_mass': GSC_MIxS_human_vaginal_host_total_mass,
		'GSC_MIxS_human_vaginal_host_phenotype': GSC_MIxS_human_vaginal_host_phenotype,
		'GSC_MIxS_human_vaginal_host_body_temperature': GSC_MIxS_human_vaginal_host_body_temperature,
		'GSC_MIxS_human_vaginal_host_sex': GSC_MIxS_human_vaginal_host_sex,
		'GSC_MIxS_human_vaginal_temperature': GSC_MIxS_human_vaginal_temperature,
		'GSC_MIxS_human_vaginal_salinity': GSC_MIxS_human_vaginal_salinity,
		'GSC_MIxS_human_vaginal_menarche': GSC_MIxS_human_vaginal_menarche,
		'GSC_MIxS_human_vaginal_sexual_activity': GSC_MIxS_human_vaginal_sexual_activity,
		'GSC_MIxS_human_vaginal_pregnancy': GSC_MIxS_human_vaginal_pregnancy,
		'GSC_MIxS_human_vaginal_douche': GSC_MIxS_human_vaginal_douche,
		'GSC_MIxS_human_vaginal_birth_control': GSC_MIxS_human_vaginal_birth_control,
		'GSC_MIxS_human_vaginal_menopause': GSC_MIxS_human_vaginal_menopause,
		'GSC_MIxS_human_vaginal_HRT': GSC_MIxS_human_vaginal_HRT,
		'GSC_MIxS_human_vaginal_hysterectomy': GSC_MIxS_human_vaginal_hysterectomy,
		'GSC_MIxS_human_vaginal_host_diet': GSC_MIxS_human_vaginal_host_diet,
		'GSC_MIxS_human_vaginal_host_last_meal': GSC_MIxS_human_vaginal_host_last_meal,
		'GSC_MIxS_human_vaginal_host_family_relationship': GSC_MIxS_human_vaginal_host_family_relationship,
		'GSC_MIxS_human_vaginal_host_genotype': GSC_MIxS_human_vaginal_host_genotype,
		'GSC_MIxS_human_vaginal_host_pulse': GSC_MIxS_human_vaginal_host_pulse,
		'GSC_MIxS_human_vaginal_subspecific_genetic_lineage': GSC_MIxS_human_vaginal_subspecific_genetic_lineage,
		'GSC_MIxS_human_vaginal_trophic_level': GSC_MIxS_human_vaginal_trophic_level,
		'GSC_MIxS_human_vaginal_relationship_to_oxygen': GSC_MIxS_human_vaginal_relationship_to_oxygen,
		'GSC_MIxS_human_vaginal_known_pathogenicity': GSC_MIxS_human_vaginal_known_pathogenicity,
		'GSC_MIxS_human_vaginal_encoded_traits': GSC_MIxS_human_vaginal_encoded_traits,
		'GSC_MIxS_human_vaginal_observed_biotic_relationship': GSC_MIxS_human_vaginal_observed_biotic_relationship,
		'GSC_MIxS_human_vaginal_chemical_administration': GSC_MIxS_human_vaginal_chemical_administration,
		'GSC_MIxS_human_vaginal_perturbation': GSC_MIxS_human_vaginal_perturbation,
	}

class GSC_MIxS_human_vaginal_unit(SelfDescribingModel):

	GSC_MIxS_human_vaginal_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_human_vaginal_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_human_vaginal_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_human_vaginal_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_human_vaginal_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_human_vaginal_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_human_vaginal_host_age_units = [('centuries', 'centuries'), ('days', 'days'), ('decades', 'decades'), ('hours', 'hours'), ('minutes', 'minutes'), ('months', 'months'), ('seconds', 'seconds'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_human_vaginal_host_height_units = [('cm', 'cm'), ('m', 'm'), ('mm', 'mm')]
	GSC_MIxS_human_vaginal_host_body_mass_index_units = [('k', 'k'), ('g', 'g'), ('/', '/'), ('m', 'm'), ('2', '2')]
	GSC_MIxS_human_vaginal_host_total_mass_units = [('g', 'g'), ('kg', 'kg')]
	GSC_MIxS_human_vaginal_host_body_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_human_vaginal_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_human_vaginal_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]
	GSC_MIxS_human_vaginal_host_pulse_units = [('b', 'b'), ('p', 'p'), ('m', 'm')]

	fields = {
		'GSC_MIxS_human_vaginal_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_human_vaginal_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_human_vaginal_geographic_location_latitude_units': GSC_MIxS_human_vaginal_geographic_location_latitude_units,
		'GSC_MIxS_human_vaginal_geographic_location_longitude_units': GSC_MIxS_human_vaginal_geographic_location_longitude_units,
		'GSC_MIxS_human_vaginal_amount_or_size_of_sample_collected_units': GSC_MIxS_human_vaginal_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_human_vaginal_sample_storage_duration_units': GSC_MIxS_human_vaginal_sample_storage_duration_units,
		'GSC_MIxS_human_vaginal_sample_storage_temperature_units': GSC_MIxS_human_vaginal_sample_storage_temperature_units,
		'GSC_MIxS_human_vaginal_host_age_units': GSC_MIxS_human_vaginal_host_age_units,
		'GSC_MIxS_human_vaginal_host_height_units': GSC_MIxS_human_vaginal_host_height_units,
		'GSC_MIxS_human_vaginal_host_body_mass_index_units': GSC_MIxS_human_vaginal_host_body_mass_index_units,
		'GSC_MIxS_human_vaginal_host_total_mass_units': GSC_MIxS_human_vaginal_host_total_mass_units,
		'GSC_MIxS_human_vaginal_host_body_temperature_units': GSC_MIxS_human_vaginal_host_body_temperature_units,
		'GSC_MIxS_human_vaginal_temperature_units': GSC_MIxS_human_vaginal_temperature_units,
		'GSC_MIxS_human_vaginal_salinity_units': GSC_MIxS_human_vaginal_salinity_units,
		'GSC_MIxS_human_vaginal_host_pulse_units': GSC_MIxS_human_vaginal_host_pulse_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_human_vaginal_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_human_vaginal_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_geographic_location_latitude_units, blank=False)
	GSC_MIxS_human_vaginal_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_geographic_location_longitude_units, blank=False)
	GSC_MIxS_human_vaginal_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_human_vaginal_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_sample_storage_duration_units, blank=False)
	GSC_MIxS_human_vaginal_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_sample_storage_temperature_units, blank=False)
	GSC_MIxS_human_vaginal_host_age = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_host_age_units, blank=False)
	GSC_MIxS_human_vaginal_host_height = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_host_height_units, blank=False)
	GSC_MIxS_human_vaginal_host_body_mass_index = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_host_body_mass_index_units, blank=False)
	GSC_MIxS_human_vaginal_host_total_mass = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_host_total_mass_units, blank=False)
	GSC_MIxS_human_vaginal_host_body_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_host_body_temperature_units, blank=False)
	GSC_MIxS_human_vaginal_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_temperature_units, blank=False)
	GSC_MIxS_human_vaginal_salinity = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_salinity_units, blank=False)
	GSC_MIxS_human_vaginal_host_pulse = models.CharField(max_length=100, choices=GSC_MIxS_human_vaginal_host_pulse_units, blank=False)

class GSC_MIxS_human_oral(SelfDescribingModel):

	GSC_MIxS_human_oral_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_human_oral_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_human_oral_medical_history_performed_choice = [('No', 'No'), ('Yes', 'Yes')]
	GSC_MIxS_human_oral_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_human_oral_IHMC_medication_code_choice = [('01=1=Analgesics/NSAIDS', '01=1=Analgesics/NSAIDS'), ('02=2=Anesthetics', '02=2=Anesthetics'), ('03=3=Antacids/H2 antagonists', '03=3=Antacids/H2 antagonists'), ('04=4=Anti-acne', '04=4=Anti-acne'), ('05=5=Anti-asthma/bronchodilators', '05=5=Anti-asthma/bronchodilators'), ('06=6=Anti-cholesterol/Anti-hyperlipidemic', '06=6=Anti-cholesterol/Anti-hyperlipidemic'), ('07=7=Anti-coagulants', '07=7=Anti-coagulants'), ('08=8=Antibiotics/(anti)-infectives, parasitics, microbials', '08=8=Antibiotics/(anti)-infectives, parasitics, microbials'), ('09=9=Antidepressants/mood-altering drugs', '09=9=Antidepressants/mood-altering drugs'), ('10=10=Antihistamines/ Decongestants', '10=10=Antihistamines/ Decongestants'), ('11=11=Antihypertensives', '11=11=Antihypertensives'), ('12=12=Cardiovascular, other than hyperlipidemic/HTN', '12=12=Cardiovascular, other than hyperlipidemic/HTN'), ('13=13=Contraceptives (oral, implant, injectable)', '13=13=Contraceptives (oral, implant, injectable)'), ('14=14=Emergency/support medications', '14=14=Emergency/support medications'), ('15=15=Endocrine/Metabolic agents', '15=15=Endocrine/Metabolic agents'), ('16=16=GI meds (anti-diarrheal, emetic, spasmodics)', '16=16=GI meds (anti-diarrheal, emetic, spasmodics)'), ('17=17=Herbal/homeopathic products', '17=17=Herbal/homeopathic products'), ('18=18=Hormones/steroids', '18=18=Hormones/steroids'), ('19=19=OTC cold & flu', '19=19=OTC cold & flu'), ('20=20=Vaccine prophylaxis', '20=20=Vaccine prophylaxis'), ('21=21=Vitamins, minerals, food supplements', '21=21=Vitamins, minerals, food supplements'), ('99=99=Other', '99=99=Other')]
	GSC_MIxS_human_oral_host_occupation_choice = [('01=01 Accounting/Finance', '01=01 Accounting/Finance'), ('02=02 Advertising/Public Relations', '02=02 Advertising/Public Relations'), ('03=03 Arts/Entertainment/Publishing', '03=03 Arts/Entertainment/Publishing'), ('04=04 Automotive', '04=04 Automotive'), ('05=05 Banking/ Mortgage', '05=05 Banking/ Mortgage'), ('06=06 Biotech', '06=06 Biotech'), ('07=07 Broadcast/Journalism', '07=07 Broadcast/Journalism'), ('08=08 Business Development', '08=08 Business Development'), ('09=09 Clerical/Administrative', '09=09 Clerical/Administrative'), ('10=10 Construction/Trades', '10=10 Construction/Trades'), ('11=11 Consultant', '11=11 Consultant'), ('12=12 Customer Services', '12=12 Customer Services'), ('13=13 Design', '13=13 Design'), ('14=14 Education', '14=14 Education'), ('15=15 Engineering', '15=15 Engineering'), ('16=16 Entry Level', '16=16 Entry Level'), ('17=17 Executive', '17=17 Executive'), ('18=18 Food Service', '18=18 Food Service'), ('19=19 Government', '19=19 Government'), ('20=20 Grocery', '20=20 Grocery'), ('21=21 Healthcare', '21=21 Healthcare'), ('22=22 Hospitality', '22=22 Hospitality'), ('23=23 Human Resources', '23=23 Human Resources'), ('24=24 Information Technology', '24=24 Information Technology'), ('25=25 Insurance', '25=25 Insurance'), ('26=26 Law/Legal', '26=26 Law/Legal'), ('27=27 Management', '27=27 Management'), ('28=28 Manufacturing', '28=28 Manufacturing'), ('29=29 Marketing', '29=29 Marketing'), ('30=30 Pharmaceutical', '30=30 Pharmaceutical'), ('31=31 Professional Services', '31=31 Professional Services'), ('32=32 Purchasing', '32=32 Purchasing'), ('33=33 Quality Assurance (QA)', '33=33 Quality Assurance (QA)'), ('34=34 Research', '34=34 Research'), ('35=35 Restaurant', '35=35 Restaurant'), ('36=36 Retail', '36=36 Retail'), ('37=37 Sales', '37=37 Sales'), ('38=38 Science', '38=38 Science'), ('39=39 Security/Law Enforcement', '39=39 Security/Law Enforcement'), ('40=40 Shipping/Distribution', '40=40 Shipping/Distribution'), ('41=41 Strategy', '41=41 Strategy'), ('42=42 Student', '42=42 Student'), ('43=43 Telecommunications', '43=43 Telecommunications'), ('44=44 Training', '44=44 Training'), ('45=45 Transportation', '45=45 Transportation'), ('46=46 Warehouse', '46=46 Warehouse'), ('47=47 Other', '47=47 Other'), ('99=99 Unknown/Refused', '99=99 Unknown/Refused')]
	GSC_MIxS_human_oral_host_sex_choice = [('female', 'female'), ('hermaphrodite', 'hermaphrodite'), ('male', 'male'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('neuter', 'neuter'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('other', 'other'), ('restricted access', 'restricted access')]
	GSC_MIxS_human_oral_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_human_oral_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_human_oral_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_human_oral_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_oral_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_oral_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_oral_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_oral_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_oral_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_oral_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_oral_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_oral_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_oral_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_oral_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_oral_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_oral_host_age_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_oral_host_height_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_oral_host_body_mass_index_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_oral_host_total_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_oral_host_body_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_oral_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_oral_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_oral_time_since_last_toothbrushing_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_oral_host_pulse_validator = "[+-]?[0-9]+"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_human_oral_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_human_oral_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_human_oral_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_human_oral_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_human_oral_number_of_replicons_validator)])
	GSC_MIxS_human_oral_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_human_oral_extrachromosomal_elements_validator)])
	GSC_MIxS_human_oral_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_human_oral_estimated_size_validator)])
	GSC_MIxS_human_oral_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_human_oral_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_human_oral_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_human_oral_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_human_oral_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_human_oral_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_human_oral_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_human_oral_library_size_validator)])
	GSC_MIxS_human_oral_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_human_oral_library_reads_sequenced_validator)])
	GSC_MIxS_human_oral_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_human_oral_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_human_oral_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_human_oral_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_human_oral_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_human_oral_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_human_oral_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_human_oral_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_human_oral_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_human_oral_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_human_oral_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_human_oral_sequence_quality_check_choice)
	GSC_MIxS_human_oral_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_human_oral_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_human_oral_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_human_oral_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_human_oral_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_human_oral_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_human_oral_collection_date_validator)])
	GSC_MIxS_human_oral_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_human_oral_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_human_oral_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_human_oral_geographic_location_latitude_validator)])
	GSC_MIxS_human_oral_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_human_oral_geographic_location_longitude_validator)])
	GSC_MIxS_human_oral_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_human_oral_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_oral_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_oral_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_oral_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_human_oral_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_human_oral_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_human_oral_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_human_oral_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_human_oral_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_human_oral_host_body_product= models.CharField(max_length=100, blank=True,help_text="substance ")
	GSC_MIxS_human_oral_medical_history_performed= models.CharField(max_length=100, blank=True,help_text="whether fu", choices=GSC_MIxS_human_oral_medical_history_performed_choice)
	GSC_MIxS_human_oral_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_human_oral_oxygenation_status_of_sample_choice)
	GSC_MIxS_human_oral_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_human_oral_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_human_oral_sample_storage_duration_validator)])
	GSC_MIxS_human_oral_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_human_oral_sample_storage_temperature_validator)])
	GSC_MIxS_human_oral_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_human_oral_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_human_oral_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_human_oral_nose_mouth_teeth_throat_disorder= models.CharField(max_length=100, blank=True,help_text="History of")
	GSC_MIxS_human_oral_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_human_oral_host_subject_id= models.CharField(max_length=100, blank=True,help_text="a unique i")
	GSC_MIxS_human_oral_IHMC_medication_code= models.CharField(max_length=100, blank=True,help_text="can includ", choices=GSC_MIxS_human_oral_IHMC_medication_code_choice)
	GSC_MIxS_human_oral_host_age= models.CharField(max_length=100, blank=True,help_text="age of hos", validators=[RegexValidator(GSC_MIxS_human_oral_host_age_validator)])
	GSC_MIxS_human_oral_host_body_site= models.CharField(max_length=100, blank=True,help_text="name of bo")
	GSC_MIxS_human_oral_host_height= models.CharField(max_length=100, blank=True,help_text="the height", validators=[RegexValidator(GSC_MIxS_human_oral_host_height_validator)])
	GSC_MIxS_human_oral_host_body_mass_index= models.CharField(max_length=100, blank=True,help_text="body mass ", validators=[RegexValidator(GSC_MIxS_human_oral_host_body_mass_index_validator)])
	GSC_MIxS_human_oral_ethnicity= models.CharField(max_length=100, blank=True,help_text="A category")
	GSC_MIxS_human_oral_host_occupation= models.CharField(max_length=100, blank=True,help_text="most frequ", choices=GSC_MIxS_human_oral_host_occupation_choice)
	GSC_MIxS_human_oral_host_total_mass= models.CharField(max_length=100, blank=True,help_text="total mass", validators=[RegexValidator(GSC_MIxS_human_oral_host_total_mass_validator)])
	GSC_MIxS_human_oral_host_phenotype= models.CharField(max_length=100, blank=True,help_text="phenotype ")
	GSC_MIxS_human_oral_host_body_temperature= models.CharField(max_length=100, blank=True,help_text="core body ", validators=[RegexValidator(GSC_MIxS_human_oral_host_body_temperature_validator)])
	GSC_MIxS_human_oral_host_sex= models.CharField(max_length=100, blank=True,help_text="Gender or ", choices=GSC_MIxS_human_oral_host_sex_choice)
	GSC_MIxS_human_oral_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_human_oral_temperature_validator)])
	GSC_MIxS_human_oral_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_human_oral_salinity_validator)])
	GSC_MIxS_human_oral_time_since_last_toothbrushing= models.CharField(max_length=100, blank=True,help_text="specificat", validators=[RegexValidator(GSC_MIxS_human_oral_time_since_last_toothbrushing_validator)])
	GSC_MIxS_human_oral_host_diet= models.CharField(max_length=100, blank=True,help_text="type of di")
	GSC_MIxS_human_oral_host_last_meal= models.CharField(max_length=100, blank=True,help_text="content of")
	GSC_MIxS_human_oral_host_family_relationship= models.CharField(max_length=100, blank=True,help_text="relationsh")
	GSC_MIxS_human_oral_host_genotype= models.CharField(max_length=100, blank=True,help_text="observed g")
	GSC_MIxS_human_oral_host_pulse= models.CharField(max_length=100, blank=True,help_text="resting pu", validators=[RegexValidator(GSC_MIxS_human_oral_host_pulse_validator)])
	GSC_MIxS_human_oral_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_human_oral_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_human_oral_trophic_level_choice)
	GSC_MIxS_human_oral_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_human_oral_relationship_to_oxygen_choice)
	GSC_MIxS_human_oral_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_human_oral_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_human_oral_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_human_oral_observed_biotic_relationship_choice)
	GSC_MIxS_human_oral_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_human_oral_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_human_oral_project_name': GSC_MIxS_human_oral_project_name,
		'GSC_MIxS_human_oral_experimental_factor': GSC_MIxS_human_oral_experimental_factor,
		'GSC_MIxS_human_oral_ploidy': GSC_MIxS_human_oral_ploidy,
		'GSC_MIxS_human_oral_number_of_replicons': GSC_MIxS_human_oral_number_of_replicons,
		'GSC_MIxS_human_oral_extrachromosomal_elements': GSC_MIxS_human_oral_extrachromosomal_elements,
		'GSC_MIxS_human_oral_estimated_size': GSC_MIxS_human_oral_estimated_size,
		'GSC_MIxS_human_oral_reference_for_biomaterial': GSC_MIxS_human_oral_reference_for_biomaterial,
		'GSC_MIxS_human_oral_annotation_source': GSC_MIxS_human_oral_annotation_source,
		'GSC_MIxS_human_oral_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_human_oral_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_human_oral_nucleic_acid_extraction': GSC_MIxS_human_oral_nucleic_acid_extraction,
		'GSC_MIxS_human_oral_nucleic_acid_amplification': GSC_MIxS_human_oral_nucleic_acid_amplification,
		'GSC_MIxS_human_oral_library_size': GSC_MIxS_human_oral_library_size,
		'GSC_MIxS_human_oral_library_reads_sequenced': GSC_MIxS_human_oral_library_reads_sequenced,
		'GSC_MIxS_human_oral_library_construction_method': GSC_MIxS_human_oral_library_construction_method,
		'GSC_MIxS_human_oral_library_vector': GSC_MIxS_human_oral_library_vector,
		'GSC_MIxS_human_oral_library_screening_strategy': GSC_MIxS_human_oral_library_screening_strategy,
		'GSC_MIxS_human_oral_target_gene': GSC_MIxS_human_oral_target_gene,
		'GSC_MIxS_human_oral_target_subfragment': GSC_MIxS_human_oral_target_subfragment,
		'GSC_MIxS_human_oral_pcr_primers': GSC_MIxS_human_oral_pcr_primers,
		'GSC_MIxS_human_oral_multiplex_identifiers': GSC_MIxS_human_oral_multiplex_identifiers,
		'GSC_MIxS_human_oral_adapters': GSC_MIxS_human_oral_adapters,
		'GSC_MIxS_human_oral_pcr_conditions': GSC_MIxS_human_oral_pcr_conditions,
		'GSC_MIxS_human_oral_sequencing_method': GSC_MIxS_human_oral_sequencing_method,
		'GSC_MIxS_human_oral_sequence_quality_check': GSC_MIxS_human_oral_sequence_quality_check,
		'GSC_MIxS_human_oral_chimera_check_software': GSC_MIxS_human_oral_chimera_check_software,
		'GSC_MIxS_human_oral_relevant_electronic_resources': GSC_MIxS_human_oral_relevant_electronic_resources,
		'GSC_MIxS_human_oral_relevant_standard_operating_procedures': GSC_MIxS_human_oral_relevant_standard_operating_procedures,
		'GSC_MIxS_human_oral_negative_control_type': GSC_MIxS_human_oral_negative_control_type,
		'GSC_MIxS_human_oral_positive_control_type': GSC_MIxS_human_oral_positive_control_type,
		'GSC_MIxS_human_oral_collection_date': GSC_MIxS_human_oral_collection_date,
		'GSC_MIxS_human_oral_geographic_location_country_and_or_sea': GSC_MIxS_human_oral_geographic_location_country_and_or_sea,
		'GSC_MIxS_human_oral_geographic_location_latitude': GSC_MIxS_human_oral_geographic_location_latitude,
		'GSC_MIxS_human_oral_geographic_location_longitude': GSC_MIxS_human_oral_geographic_location_longitude,
		'GSC_MIxS_human_oral_geographic_location_region_and_locality': GSC_MIxS_human_oral_geographic_location_region_and_locality,
		'GSC_MIxS_human_oral_broad_scale_environmental_context': GSC_MIxS_human_oral_broad_scale_environmental_context,
		'GSC_MIxS_human_oral_local_environmental_context': GSC_MIxS_human_oral_local_environmental_context,
		'GSC_MIxS_human_oral_environmental_medium': GSC_MIxS_human_oral_environmental_medium,
		'GSC_MIxS_human_oral_source_material_identifiers': GSC_MIxS_human_oral_source_material_identifiers,
		'GSC_MIxS_human_oral_sample_material_processing': GSC_MIxS_human_oral_sample_material_processing,
		'GSC_MIxS_human_oral_isolation_and_growth_condition': GSC_MIxS_human_oral_isolation_and_growth_condition,
		'GSC_MIxS_human_oral_propagation': GSC_MIxS_human_oral_propagation,
		'GSC_MIxS_human_oral_amount_or_size_of_sample_collected': GSC_MIxS_human_oral_amount_or_size_of_sample_collected,
		'GSC_MIxS_human_oral_host_body_product': GSC_MIxS_human_oral_host_body_product,
		'GSC_MIxS_human_oral_medical_history_performed': GSC_MIxS_human_oral_medical_history_performed,
		'GSC_MIxS_human_oral_oxygenation_status_of_sample': GSC_MIxS_human_oral_oxygenation_status_of_sample,
		'GSC_MIxS_human_oral_organism_count': GSC_MIxS_human_oral_organism_count,
		'GSC_MIxS_human_oral_sample_storage_duration': GSC_MIxS_human_oral_sample_storage_duration,
		'GSC_MIxS_human_oral_sample_storage_temperature': GSC_MIxS_human_oral_sample_storage_temperature,
		'GSC_MIxS_human_oral_sample_storage_location': GSC_MIxS_human_oral_sample_storage_location,
		'GSC_MIxS_human_oral_sample_collection_device': GSC_MIxS_human_oral_sample_collection_device,
		'GSC_MIxS_human_oral_sample_collection_method': GSC_MIxS_human_oral_sample_collection_method,
		'GSC_MIxS_human_oral_nose_mouth_teeth_throat_disorder': GSC_MIxS_human_oral_nose_mouth_teeth_throat_disorder,
		'GSC_MIxS_human_oral_host_disease_status': GSC_MIxS_human_oral_host_disease_status,
		'GSC_MIxS_human_oral_host_subject_id': GSC_MIxS_human_oral_host_subject_id,
		'GSC_MIxS_human_oral_IHMC_medication_code': GSC_MIxS_human_oral_IHMC_medication_code,
		'GSC_MIxS_human_oral_host_age': GSC_MIxS_human_oral_host_age,
		'GSC_MIxS_human_oral_host_body_site': GSC_MIxS_human_oral_host_body_site,
		'GSC_MIxS_human_oral_host_height': GSC_MIxS_human_oral_host_height,
		'GSC_MIxS_human_oral_host_body_mass_index': GSC_MIxS_human_oral_host_body_mass_index,
		'GSC_MIxS_human_oral_ethnicity': GSC_MIxS_human_oral_ethnicity,
		'GSC_MIxS_human_oral_host_occupation': GSC_MIxS_human_oral_host_occupation,
		'GSC_MIxS_human_oral_host_total_mass': GSC_MIxS_human_oral_host_total_mass,
		'GSC_MIxS_human_oral_host_phenotype': GSC_MIxS_human_oral_host_phenotype,
		'GSC_MIxS_human_oral_host_body_temperature': GSC_MIxS_human_oral_host_body_temperature,
		'GSC_MIxS_human_oral_host_sex': GSC_MIxS_human_oral_host_sex,
		'GSC_MIxS_human_oral_temperature': GSC_MIxS_human_oral_temperature,
		'GSC_MIxS_human_oral_salinity': GSC_MIxS_human_oral_salinity,
		'GSC_MIxS_human_oral_time_since_last_toothbrushing': GSC_MIxS_human_oral_time_since_last_toothbrushing,
		'GSC_MIxS_human_oral_host_diet': GSC_MIxS_human_oral_host_diet,
		'GSC_MIxS_human_oral_host_last_meal': GSC_MIxS_human_oral_host_last_meal,
		'GSC_MIxS_human_oral_host_family_relationship': GSC_MIxS_human_oral_host_family_relationship,
		'GSC_MIxS_human_oral_host_genotype': GSC_MIxS_human_oral_host_genotype,
		'GSC_MIxS_human_oral_host_pulse': GSC_MIxS_human_oral_host_pulse,
		'GSC_MIxS_human_oral_subspecific_genetic_lineage': GSC_MIxS_human_oral_subspecific_genetic_lineage,
		'GSC_MIxS_human_oral_trophic_level': GSC_MIxS_human_oral_trophic_level,
		'GSC_MIxS_human_oral_relationship_to_oxygen': GSC_MIxS_human_oral_relationship_to_oxygen,
		'GSC_MIxS_human_oral_known_pathogenicity': GSC_MIxS_human_oral_known_pathogenicity,
		'GSC_MIxS_human_oral_encoded_traits': GSC_MIxS_human_oral_encoded_traits,
		'GSC_MIxS_human_oral_observed_biotic_relationship': GSC_MIxS_human_oral_observed_biotic_relationship,
		'GSC_MIxS_human_oral_chemical_administration': GSC_MIxS_human_oral_chemical_administration,
		'GSC_MIxS_human_oral_perturbation': GSC_MIxS_human_oral_perturbation,
	}

class GSC_MIxS_human_oral_unit(SelfDescribingModel):

	GSC_MIxS_human_oral_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_human_oral_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_human_oral_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_human_oral_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_human_oral_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_human_oral_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_human_oral_host_age_units = [('centuries', 'centuries'), ('days', 'days'), ('decades', 'decades'), ('hours', 'hours'), ('minutes', 'minutes'), ('months', 'months'), ('seconds', 'seconds'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_human_oral_host_height_units = [('cm', 'cm'), ('m', 'm'), ('mm', 'mm')]
	GSC_MIxS_human_oral_host_body_mass_index_units = [('k', 'k'), ('g', 'g'), ('/', '/'), ('m', 'm'), ('2', '2')]
	GSC_MIxS_human_oral_host_total_mass_units = [('g', 'g'), ('kg', 'kg')]
	GSC_MIxS_human_oral_host_body_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_human_oral_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_human_oral_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]
	GSC_MIxS_human_oral_time_since_last_toothbrushing_units = [('hours', 'hours'), ('minutes', 'minutes')]
	GSC_MIxS_human_oral_host_pulse_units = [('b', 'b'), ('p', 'p'), ('m', 'm')]

	fields = {
		'GSC_MIxS_human_oral_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_human_oral_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_human_oral_geographic_location_latitude_units': GSC_MIxS_human_oral_geographic_location_latitude_units,
		'GSC_MIxS_human_oral_geographic_location_longitude_units': GSC_MIxS_human_oral_geographic_location_longitude_units,
		'GSC_MIxS_human_oral_amount_or_size_of_sample_collected_units': GSC_MIxS_human_oral_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_human_oral_sample_storage_duration_units': GSC_MIxS_human_oral_sample_storage_duration_units,
		'GSC_MIxS_human_oral_sample_storage_temperature_units': GSC_MIxS_human_oral_sample_storage_temperature_units,
		'GSC_MIxS_human_oral_host_age_units': GSC_MIxS_human_oral_host_age_units,
		'GSC_MIxS_human_oral_host_height_units': GSC_MIxS_human_oral_host_height_units,
		'GSC_MIxS_human_oral_host_body_mass_index_units': GSC_MIxS_human_oral_host_body_mass_index_units,
		'GSC_MIxS_human_oral_host_total_mass_units': GSC_MIxS_human_oral_host_total_mass_units,
		'GSC_MIxS_human_oral_host_body_temperature_units': GSC_MIxS_human_oral_host_body_temperature_units,
		'GSC_MIxS_human_oral_temperature_units': GSC_MIxS_human_oral_temperature_units,
		'GSC_MIxS_human_oral_salinity_units': GSC_MIxS_human_oral_salinity_units,
		'GSC_MIxS_human_oral_time_since_last_toothbrushing_units': GSC_MIxS_human_oral_time_since_last_toothbrushing_units,
		'GSC_MIxS_human_oral_host_pulse_units': GSC_MIxS_human_oral_host_pulse_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_human_oral_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_human_oral_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_geographic_location_latitude_units, blank=False)
	GSC_MIxS_human_oral_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_geographic_location_longitude_units, blank=False)
	GSC_MIxS_human_oral_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_human_oral_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_sample_storage_duration_units, blank=False)
	GSC_MIxS_human_oral_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_sample_storage_temperature_units, blank=False)
	GSC_MIxS_human_oral_host_age = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_host_age_units, blank=False)
	GSC_MIxS_human_oral_host_height = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_host_height_units, blank=False)
	GSC_MIxS_human_oral_host_body_mass_index = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_host_body_mass_index_units, blank=False)
	GSC_MIxS_human_oral_host_total_mass = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_host_total_mass_units, blank=False)
	GSC_MIxS_human_oral_host_body_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_host_body_temperature_units, blank=False)
	GSC_MIxS_human_oral_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_temperature_units, blank=False)
	GSC_MIxS_human_oral_salinity = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_salinity_units, blank=False)
	GSC_MIxS_human_oral_time_since_last_toothbrushing = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_time_since_last_toothbrushing_units, blank=False)
	GSC_MIxS_human_oral_host_pulse = models.CharField(max_length=100, choices=GSC_MIxS_human_oral_host_pulse_units, blank=False)

class GSC_MIxS_sediment(SelfDescribingModel):

	GSC_MIxS_sediment_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_sediment_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_sediment_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_sediment_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_sediment_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_sediment_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_sediment_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_sediment_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_sediment_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_sediment_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_sediment_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_sediment_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_sediment_altitude_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_sediment_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_sediment_depth_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_elevation_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_density_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_alkyl_diethers_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_aminopeptidase_activity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_ammonium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_bacterial_carbon_production_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_bishomohopanol_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_bromide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_calcium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_carbon_nitrogen_ratio_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_chloride_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_chlorophyll_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_diether_lipids_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_dissolved_carbon_dioxide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_dissolved_hydrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_dissolved_inorganic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_dissolved_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_dissolved_organic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_methane_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_dissolved_oxygen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_glucosidase_activity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_magnesium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_n_alkanes_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_nitrate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_nitrite_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_organic_matter_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_organic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_particulate_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_petroleum_hydrocarbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_phaeopigments_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_phosphate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_phospholipid_fatty_acid_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_potassium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_redox_potential_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_total_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_silicate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_sodium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_total_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_water_content_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_sulfate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_sulfide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_sediment_total_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_sediment_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_sediment_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_sediment_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_sediment_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_sediment_number_of_replicons_validator)])
	GSC_MIxS_sediment_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_sediment_extrachromosomal_elements_validator)])
	GSC_MIxS_sediment_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_sediment_estimated_size_validator)])
	GSC_MIxS_sediment_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_sediment_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_sediment_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_sediment_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_sediment_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_sediment_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_sediment_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_sediment_library_size_validator)])
	GSC_MIxS_sediment_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_sediment_library_reads_sequenced_validator)])
	GSC_MIxS_sediment_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_sediment_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_sediment_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_sediment_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_sediment_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_sediment_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_sediment_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_sediment_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_sediment_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_sediment_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_sediment_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_sediment_sequence_quality_check_choice)
	GSC_MIxS_sediment_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_sediment_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_sediment_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_sediment_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_sediment_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_sediment_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_sediment_collection_date_validator)])
	GSC_MIxS_sediment_altitude= models.CharField(max_length=100, blank=True,help_text="The altitu", validators=[RegexValidator(GSC_MIxS_sediment_altitude_validator)])
	GSC_MIxS_sediment_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_sediment_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_sediment_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_sediment_geographic_location_latitude_validator)])
	GSC_MIxS_sediment_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_sediment_geographic_location_longitude_validator)])
	GSC_MIxS_sediment_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_sediment_depth= models.CharField(max_length=100, blank=False,help_text="The vertic", validators=[RegexValidator(GSC_MIxS_sediment_depth_validator)])
	GSC_MIxS_sediment_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_sediment_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_sediment_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_sediment_elevation= models.CharField(max_length=100, blank=False,help_text="The elevat", validators=[RegexValidator(GSC_MIxS_sediment_elevation_validator)])
	GSC_MIxS_sediment_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_sediment_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_sediment_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_sediment_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_sediment_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_sediment_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_sediment_biomass= models.CharField(max_length=100, blank=True,help_text="amount of ")
	GSC_MIxS_sediment_density= models.CharField(max_length=100, blank=True,help_text="density of", validators=[RegexValidator(GSC_MIxS_sediment_density_validator)])
	GSC_MIxS_sediment_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_sediment_oxygenation_status_of_sample_choice)
	GSC_MIxS_sediment_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_sediment_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_sediment_sample_storage_duration_validator)])
	GSC_MIxS_sediment_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_sediment_sample_storage_temperature_validator)])
	GSC_MIxS_sediment_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_sediment_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_sediment_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_sediment_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_sediment_host_scientific_name= models.CharField(max_length=100, blank=True,help_text="Scientific")
	GSC_MIxS_sediment_alkyl_diethers= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_alkyl_diethers_validator)])
	GSC_MIxS_sediment_aminopeptidase_activity= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_sediment_aminopeptidase_activity_validator)])
	GSC_MIxS_sediment_ammonium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_ammonium_validator)])
	GSC_MIxS_sediment_bacterial_carbon_production= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_sediment_bacterial_carbon_production_validator)])
	GSC_MIxS_sediment_bishomohopanol= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_bishomohopanol_validator)])
	GSC_MIxS_sediment_bromide= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_bromide_validator)])
	GSC_MIxS_sediment_calcium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_calcium_validator)])
	GSC_MIxS_sediment_carbon_nitrogen_ratio= models.CharField(max_length=100, blank=True,help_text="ratio of a", validators=[RegexValidator(GSC_MIxS_sediment_carbon_nitrogen_ratio_validator)])
	GSC_MIxS_sediment_chloride= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_chloride_validator)])
	GSC_MIxS_sediment_chlorophyll= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_chlorophyll_validator)])
	GSC_MIxS_sediment_diether_lipids= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_diether_lipids_validator)])
	GSC_MIxS_sediment_dissolved_carbon_dioxide= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_dissolved_carbon_dioxide_validator)])
	GSC_MIxS_sediment_dissolved_hydrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_dissolved_hydrogen_validator)])
	GSC_MIxS_sediment_dissolved_inorganic_carbon= models.CharField(max_length=100, blank=True,help_text="dissolved ", validators=[RegexValidator(GSC_MIxS_sediment_dissolved_inorganic_carbon_validator)])
	GSC_MIxS_sediment_dissolved_organic_carbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_dissolved_organic_carbon_validator)])
	GSC_MIxS_sediment_dissolved_organic_nitrogen= models.CharField(max_length=100, blank=True,help_text="dissolved ", validators=[RegexValidator(GSC_MIxS_sediment_dissolved_organic_nitrogen_validator)])
	GSC_MIxS_sediment_methane= models.CharField(max_length=100, blank=True,help_text="methane (g", validators=[RegexValidator(GSC_MIxS_sediment_methane_validator)])
	GSC_MIxS_sediment_dissolved_oxygen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_dissolved_oxygen_validator)])
	GSC_MIxS_sediment_glucosidase_activity= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_sediment_glucosidase_activity_validator)])
	GSC_MIxS_sediment_magnesium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_magnesium_validator)])
	GSC_MIxS_sediment_n_alkanes= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_n_alkanes_validator)])
	GSC_MIxS_sediment_nitrate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_nitrate_validator)])
	GSC_MIxS_sediment_nitrite= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_nitrite_validator)])
	GSC_MIxS_sediment_nitrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_nitrogen_validator)])
	GSC_MIxS_sediment_organic_carbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_organic_carbon_validator)])
	GSC_MIxS_sediment_organic_matter= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_organic_matter_validator)])
	GSC_MIxS_sediment_organic_nitrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_organic_nitrogen_validator)])
	GSC_MIxS_sediment_particulate_organic_carbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_particulate_organic_carbon_validator)])
	GSC_MIxS_sediment_petroleum_hydrocarbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_petroleum_hydrocarbon_validator)])
	GSC_MIxS_sediment_phaeopigments= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_phaeopigments_validator)])
	GSC_MIxS_sediment_phosphate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_phosphate_validator)])
	GSC_MIxS_sediment_phospholipid_fatty_acid= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_phospholipid_fatty_acid_validator)])
	GSC_MIxS_sediment_potassium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_potassium_validator)])
	GSC_MIxS_sediment_redox_potential= models.CharField(max_length=100, blank=True,help_text="redox pote", validators=[RegexValidator(GSC_MIxS_sediment_redox_potential_validator)])
	GSC_MIxS_sediment_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_sediment_salinity_validator)])
	GSC_MIxS_sediment_total_carbon= models.CharField(max_length=100, blank=True,help_text="total carb", validators=[RegexValidator(GSC_MIxS_sediment_total_carbon_validator)])
	GSC_MIxS_sediment_silicate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_silicate_validator)])
	GSC_MIxS_sediment_sodium= models.CharField(max_length=100, blank=True,help_text="sodium con", validators=[RegexValidator(GSC_MIxS_sediment_sodium_validator)])
	GSC_MIxS_sediment_total_organic_carbon= models.CharField(max_length=100, blank=True,help_text="Definition", validators=[RegexValidator(GSC_MIxS_sediment_total_organic_carbon_validator)])
	GSC_MIxS_sediment_water_content= models.CharField(max_length=100, blank=True,help_text="water cont", validators=[RegexValidator(GSC_MIxS_sediment_water_content_validator)])
	GSC_MIxS_sediment_sulfate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_sulfate_validator)])
	GSC_MIxS_sediment_sulfide= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_sediment_sulfide_validator)])
	GSC_MIxS_sediment_total_nitrogen= models.CharField(max_length=100, blank=True,help_text="total nitr", validators=[RegexValidator(GSC_MIxS_sediment_total_nitrogen_validator)])
	GSC_MIxS_sediment_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_sediment_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_sediment_trophic_level_choice)
	GSC_MIxS_sediment_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_sediment_relationship_to_oxygen_choice)
	GSC_MIxS_sediment_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_sediment_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_sediment_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_sediment_observed_biotic_relationship_choice)
	GSC_MIxS_sediment_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_sediment_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_sediment_project_name': GSC_MIxS_sediment_project_name,
		'GSC_MIxS_sediment_experimental_factor': GSC_MIxS_sediment_experimental_factor,
		'GSC_MIxS_sediment_ploidy': GSC_MIxS_sediment_ploidy,
		'GSC_MIxS_sediment_number_of_replicons': GSC_MIxS_sediment_number_of_replicons,
		'GSC_MIxS_sediment_extrachromosomal_elements': GSC_MIxS_sediment_extrachromosomal_elements,
		'GSC_MIxS_sediment_estimated_size': GSC_MIxS_sediment_estimated_size,
		'GSC_MIxS_sediment_reference_for_biomaterial': GSC_MIxS_sediment_reference_for_biomaterial,
		'GSC_MIxS_sediment_annotation_source': GSC_MIxS_sediment_annotation_source,
		'GSC_MIxS_sediment_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_sediment_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_sediment_nucleic_acid_extraction': GSC_MIxS_sediment_nucleic_acid_extraction,
		'GSC_MIxS_sediment_nucleic_acid_amplification': GSC_MIxS_sediment_nucleic_acid_amplification,
		'GSC_MIxS_sediment_library_size': GSC_MIxS_sediment_library_size,
		'GSC_MIxS_sediment_library_reads_sequenced': GSC_MIxS_sediment_library_reads_sequenced,
		'GSC_MIxS_sediment_library_construction_method': GSC_MIxS_sediment_library_construction_method,
		'GSC_MIxS_sediment_library_vector': GSC_MIxS_sediment_library_vector,
		'GSC_MIxS_sediment_library_screening_strategy': GSC_MIxS_sediment_library_screening_strategy,
		'GSC_MIxS_sediment_target_gene': GSC_MIxS_sediment_target_gene,
		'GSC_MIxS_sediment_target_subfragment': GSC_MIxS_sediment_target_subfragment,
		'GSC_MIxS_sediment_pcr_primers': GSC_MIxS_sediment_pcr_primers,
		'GSC_MIxS_sediment_multiplex_identifiers': GSC_MIxS_sediment_multiplex_identifiers,
		'GSC_MIxS_sediment_adapters': GSC_MIxS_sediment_adapters,
		'GSC_MIxS_sediment_pcr_conditions': GSC_MIxS_sediment_pcr_conditions,
		'GSC_MIxS_sediment_sequencing_method': GSC_MIxS_sediment_sequencing_method,
		'GSC_MIxS_sediment_sequence_quality_check': GSC_MIxS_sediment_sequence_quality_check,
		'GSC_MIxS_sediment_chimera_check_software': GSC_MIxS_sediment_chimera_check_software,
		'GSC_MIxS_sediment_relevant_electronic_resources': GSC_MIxS_sediment_relevant_electronic_resources,
		'GSC_MIxS_sediment_relevant_standard_operating_procedures': GSC_MIxS_sediment_relevant_standard_operating_procedures,
		'GSC_MIxS_sediment_negative_control_type': GSC_MIxS_sediment_negative_control_type,
		'GSC_MIxS_sediment_positive_control_type': GSC_MIxS_sediment_positive_control_type,
		'GSC_MIxS_sediment_collection_date': GSC_MIxS_sediment_collection_date,
		'GSC_MIxS_sediment_altitude': GSC_MIxS_sediment_altitude,
		'GSC_MIxS_sediment_geographic_location_country_and_or_sea': GSC_MIxS_sediment_geographic_location_country_and_or_sea,
		'GSC_MIxS_sediment_geographic_location_latitude': GSC_MIxS_sediment_geographic_location_latitude,
		'GSC_MIxS_sediment_geographic_location_longitude': GSC_MIxS_sediment_geographic_location_longitude,
		'GSC_MIxS_sediment_geographic_location_region_and_locality': GSC_MIxS_sediment_geographic_location_region_and_locality,
		'GSC_MIxS_sediment_depth': GSC_MIxS_sediment_depth,
		'GSC_MIxS_sediment_broad_scale_environmental_context': GSC_MIxS_sediment_broad_scale_environmental_context,
		'GSC_MIxS_sediment_local_environmental_context': GSC_MIxS_sediment_local_environmental_context,
		'GSC_MIxS_sediment_environmental_medium': GSC_MIxS_sediment_environmental_medium,
		'GSC_MIxS_sediment_elevation': GSC_MIxS_sediment_elevation,
		'GSC_MIxS_sediment_source_material_identifiers': GSC_MIxS_sediment_source_material_identifiers,
		'GSC_MIxS_sediment_sample_material_processing': GSC_MIxS_sediment_sample_material_processing,
		'GSC_MIxS_sediment_isolation_and_growth_condition': GSC_MIxS_sediment_isolation_and_growth_condition,
		'GSC_MIxS_sediment_propagation': GSC_MIxS_sediment_propagation,
		'GSC_MIxS_sediment_amount_or_size_of_sample_collected': GSC_MIxS_sediment_amount_or_size_of_sample_collected,
		'GSC_MIxS_sediment_biomass': GSC_MIxS_sediment_biomass,
		'GSC_MIxS_sediment_density': GSC_MIxS_sediment_density,
		'GSC_MIxS_sediment_oxygenation_status_of_sample': GSC_MIxS_sediment_oxygenation_status_of_sample,
		'GSC_MIxS_sediment_organism_count': GSC_MIxS_sediment_organism_count,
		'GSC_MIxS_sediment_sample_storage_duration': GSC_MIxS_sediment_sample_storage_duration,
		'GSC_MIxS_sediment_sample_storage_temperature': GSC_MIxS_sediment_sample_storage_temperature,
		'GSC_MIxS_sediment_sample_storage_location': GSC_MIxS_sediment_sample_storage_location,
		'GSC_MIxS_sediment_sample_collection_device': GSC_MIxS_sediment_sample_collection_device,
		'GSC_MIxS_sediment_sample_collection_method': GSC_MIxS_sediment_sample_collection_method,
		'GSC_MIxS_sediment_host_disease_status': GSC_MIxS_sediment_host_disease_status,
		'GSC_MIxS_sediment_host_scientific_name': GSC_MIxS_sediment_host_scientific_name,
		'GSC_MIxS_sediment_alkyl_diethers': GSC_MIxS_sediment_alkyl_diethers,
		'GSC_MIxS_sediment_aminopeptidase_activity': GSC_MIxS_sediment_aminopeptidase_activity,
		'GSC_MIxS_sediment_ammonium': GSC_MIxS_sediment_ammonium,
		'GSC_MIxS_sediment_bacterial_carbon_production': GSC_MIxS_sediment_bacterial_carbon_production,
		'GSC_MIxS_sediment_bishomohopanol': GSC_MIxS_sediment_bishomohopanol,
		'GSC_MIxS_sediment_bromide': GSC_MIxS_sediment_bromide,
		'GSC_MIxS_sediment_calcium': GSC_MIxS_sediment_calcium,
		'GSC_MIxS_sediment_carbon_nitrogen_ratio': GSC_MIxS_sediment_carbon_nitrogen_ratio,
		'GSC_MIxS_sediment_chloride': GSC_MIxS_sediment_chloride,
		'GSC_MIxS_sediment_chlorophyll': GSC_MIxS_sediment_chlorophyll,
		'GSC_MIxS_sediment_diether_lipids': GSC_MIxS_sediment_diether_lipids,
		'GSC_MIxS_sediment_dissolved_carbon_dioxide': GSC_MIxS_sediment_dissolved_carbon_dioxide,
		'GSC_MIxS_sediment_dissolved_hydrogen': GSC_MIxS_sediment_dissolved_hydrogen,
		'GSC_MIxS_sediment_dissolved_inorganic_carbon': GSC_MIxS_sediment_dissolved_inorganic_carbon,
		'GSC_MIxS_sediment_dissolved_organic_carbon': GSC_MIxS_sediment_dissolved_organic_carbon,
		'GSC_MIxS_sediment_dissolved_organic_nitrogen': GSC_MIxS_sediment_dissolved_organic_nitrogen,
		'GSC_MIxS_sediment_methane': GSC_MIxS_sediment_methane,
		'GSC_MIxS_sediment_dissolved_oxygen': GSC_MIxS_sediment_dissolved_oxygen,
		'GSC_MIxS_sediment_glucosidase_activity': GSC_MIxS_sediment_glucosidase_activity,
		'GSC_MIxS_sediment_magnesium': GSC_MIxS_sediment_magnesium,
		'GSC_MIxS_sediment_n_alkanes': GSC_MIxS_sediment_n_alkanes,
		'GSC_MIxS_sediment_nitrate': GSC_MIxS_sediment_nitrate,
		'GSC_MIxS_sediment_nitrite': GSC_MIxS_sediment_nitrite,
		'GSC_MIxS_sediment_nitrogen': GSC_MIxS_sediment_nitrogen,
		'GSC_MIxS_sediment_organic_carbon': GSC_MIxS_sediment_organic_carbon,
		'GSC_MIxS_sediment_organic_matter': GSC_MIxS_sediment_organic_matter,
		'GSC_MIxS_sediment_organic_nitrogen': GSC_MIxS_sediment_organic_nitrogen,
		'GSC_MIxS_sediment_particulate_organic_carbon': GSC_MIxS_sediment_particulate_organic_carbon,
		'GSC_MIxS_sediment_petroleum_hydrocarbon': GSC_MIxS_sediment_petroleum_hydrocarbon,
		'GSC_MIxS_sediment_phaeopigments': GSC_MIxS_sediment_phaeopigments,
		'GSC_MIxS_sediment_phosphate': GSC_MIxS_sediment_phosphate,
		'GSC_MIxS_sediment_phospholipid_fatty_acid': GSC_MIxS_sediment_phospholipid_fatty_acid,
		'GSC_MIxS_sediment_potassium': GSC_MIxS_sediment_potassium,
		'GSC_MIxS_sediment_redox_potential': GSC_MIxS_sediment_redox_potential,
		'GSC_MIxS_sediment_salinity': GSC_MIxS_sediment_salinity,
		'GSC_MIxS_sediment_total_carbon': GSC_MIxS_sediment_total_carbon,
		'GSC_MIxS_sediment_silicate': GSC_MIxS_sediment_silicate,
		'GSC_MIxS_sediment_sodium': GSC_MIxS_sediment_sodium,
		'GSC_MIxS_sediment_total_organic_carbon': GSC_MIxS_sediment_total_organic_carbon,
		'GSC_MIxS_sediment_water_content': GSC_MIxS_sediment_water_content,
		'GSC_MIxS_sediment_sulfate': GSC_MIxS_sediment_sulfate,
		'GSC_MIxS_sediment_sulfide': GSC_MIxS_sediment_sulfide,
		'GSC_MIxS_sediment_total_nitrogen': GSC_MIxS_sediment_total_nitrogen,
		'GSC_MIxS_sediment_subspecific_genetic_lineage': GSC_MIxS_sediment_subspecific_genetic_lineage,
		'GSC_MIxS_sediment_trophic_level': GSC_MIxS_sediment_trophic_level,
		'GSC_MIxS_sediment_relationship_to_oxygen': GSC_MIxS_sediment_relationship_to_oxygen,
		'GSC_MIxS_sediment_known_pathogenicity': GSC_MIxS_sediment_known_pathogenicity,
		'GSC_MIxS_sediment_encoded_traits': GSC_MIxS_sediment_encoded_traits,
		'GSC_MIxS_sediment_observed_biotic_relationship': GSC_MIxS_sediment_observed_biotic_relationship,
		'GSC_MIxS_sediment_chemical_administration': GSC_MIxS_sediment_chemical_administration,
		'GSC_MIxS_sediment_perturbation': GSC_MIxS_sediment_perturbation,
	}

class GSC_MIxS_sediment_unit(SelfDescribingModel):

	GSC_MIxS_sediment_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_sediment_altitude_units = [('m', 'm')]
	GSC_MIxS_sediment_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_sediment_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_sediment_depth_units = [('m', 'm')]
	GSC_MIxS_sediment_elevation_units = [('m', 'm')]
	GSC_MIxS_sediment_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_sediment_biomass_units = [('g', 'g'), ('kg', 'kg'), ('t', 't')]
	GSC_MIxS_sediment_density_units = [('g', 'g'), ('/', '/'), ('m', 'm'), ('3', '3')]
	GSC_MIxS_sediment_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_sediment_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_sediment_alkyl_diethers_units = [('M/L', 'M/L'), ('µg/L', 'µg/L')]
	GSC_MIxS_sediment_aminopeptidase_activity_units = [('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L'), ('/', '/'), ('h', 'h')]
	GSC_MIxS_sediment_ammonium_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_bacterial_carbon_production_units = [('n', 'n'), ('g', 'g'), ('/', '/'), ('h', 'h')]
	GSC_MIxS_sediment_bishomohopanol_units = [('µg/L', 'µg/L'), ('µg/g', 'µg/g')]
	GSC_MIxS_sediment_bromide_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_sediment_calcium_units = [('mg/L', 'mg/L'), ('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_sediment_chloride_units = [('m', 'm'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_chlorophyll_units = [('mg/m3', 'mg/m3'), ('µg/L', 'µg/L')]
	GSC_MIxS_sediment_diether_lipids_units = [('n', 'n'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_dissolved_carbon_dioxide_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_dissolved_hydrogen_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_dissolved_inorganic_carbon_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_dissolved_organic_carbon_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_dissolved_organic_nitrogen_units = [('mg/L', 'mg/L'), ('µg/L', 'µg/L')]
	GSC_MIxS_sediment_methane_units = [('µ', 'µ'), ('M', 'M'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_dissolved_oxygen_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('k', 'k'), ('g', 'g')]
	GSC_MIxS_sediment_glucosidase_activity_units = [('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L'), ('/', '/'), ('h', 'h')]
	GSC_MIxS_sediment_magnesium_units = [('mg/L', 'mg/L'), ('mol/L', 'mol/L'), ('parts/million', 'parts/million')]
	GSC_MIxS_sediment_n_alkanes_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_nitrate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_nitrite_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_nitrogen_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_organic_carbon_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_organic_matter_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_organic_nitrogen_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_particulate_organic_carbon_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_petroleum_hydrocarbon_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_phaeopigments_units = [('mg/m3', 'mg/m3'), ('µg/L', 'µg/L')]
	GSC_MIxS_sediment_phosphate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_phospholipid_fatty_acid_units = [('mol/L', 'mol/L'), ('mol/g', 'mol/g')]
	GSC_MIxS_sediment_potassium_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_sediment_redox_potential_units = [('m', 'm'), ('V', 'V')]
	GSC_MIxS_sediment_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]
	GSC_MIxS_sediment_total_carbon_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_silicate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_sediment_sodium_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_sediment_total_organic_carbon_units = [('g', 'g'), ('/', '/'), ('k', 'k'), ('g', 'g')]
	GSC_MIxS_sediment_water_content_units = [('cm3/cm3', 'cm3/cm3'), ('g/g', 'g/g')]
	GSC_MIxS_sediment_sulfate_units = [('mg/L', 'mg/L'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_sediment_sulfide_units = [('mg/L', 'mg/L'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_sediment_total_nitrogen_units = [('µg/L', 'µg/L'), ('µmol/L', 'µmol/L')]

	fields = {
		'GSC_MIxS_sediment_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_sediment_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_sediment_altitude_units': GSC_MIxS_sediment_altitude_units,
		'GSC_MIxS_sediment_geographic_location_latitude_units': GSC_MIxS_sediment_geographic_location_latitude_units,
		'GSC_MIxS_sediment_geographic_location_longitude_units': GSC_MIxS_sediment_geographic_location_longitude_units,
		'GSC_MIxS_sediment_depth_units': GSC_MIxS_sediment_depth_units,
		'GSC_MIxS_sediment_elevation_units': GSC_MIxS_sediment_elevation_units,
		'GSC_MIxS_sediment_amount_or_size_of_sample_collected_units': GSC_MIxS_sediment_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_sediment_biomass_units': GSC_MIxS_sediment_biomass_units,
		'GSC_MIxS_sediment_density_units': GSC_MIxS_sediment_density_units,
		'GSC_MIxS_sediment_sample_storage_duration_units': GSC_MIxS_sediment_sample_storage_duration_units,
		'GSC_MIxS_sediment_sample_storage_temperature_units': GSC_MIxS_sediment_sample_storage_temperature_units,
		'GSC_MIxS_sediment_alkyl_diethers_units': GSC_MIxS_sediment_alkyl_diethers_units,
		'GSC_MIxS_sediment_aminopeptidase_activity_units': GSC_MIxS_sediment_aminopeptidase_activity_units,
		'GSC_MIxS_sediment_ammonium_units': GSC_MIxS_sediment_ammonium_units,
		'GSC_MIxS_sediment_bacterial_carbon_production_units': GSC_MIxS_sediment_bacterial_carbon_production_units,
		'GSC_MIxS_sediment_bishomohopanol_units': GSC_MIxS_sediment_bishomohopanol_units,
		'GSC_MIxS_sediment_bromide_units': GSC_MIxS_sediment_bromide_units,
		'GSC_MIxS_sediment_calcium_units': GSC_MIxS_sediment_calcium_units,
		'GSC_MIxS_sediment_chloride_units': GSC_MIxS_sediment_chloride_units,
		'GSC_MIxS_sediment_chlorophyll_units': GSC_MIxS_sediment_chlorophyll_units,
		'GSC_MIxS_sediment_diether_lipids_units': GSC_MIxS_sediment_diether_lipids_units,
		'GSC_MIxS_sediment_dissolved_carbon_dioxide_units': GSC_MIxS_sediment_dissolved_carbon_dioxide_units,
		'GSC_MIxS_sediment_dissolved_hydrogen_units': GSC_MIxS_sediment_dissolved_hydrogen_units,
		'GSC_MIxS_sediment_dissolved_inorganic_carbon_units': GSC_MIxS_sediment_dissolved_inorganic_carbon_units,
		'GSC_MIxS_sediment_dissolved_organic_carbon_units': GSC_MIxS_sediment_dissolved_organic_carbon_units,
		'GSC_MIxS_sediment_dissolved_organic_nitrogen_units': GSC_MIxS_sediment_dissolved_organic_nitrogen_units,
		'GSC_MIxS_sediment_methane_units': GSC_MIxS_sediment_methane_units,
		'GSC_MIxS_sediment_dissolved_oxygen_units': GSC_MIxS_sediment_dissolved_oxygen_units,
		'GSC_MIxS_sediment_glucosidase_activity_units': GSC_MIxS_sediment_glucosidase_activity_units,
		'GSC_MIxS_sediment_magnesium_units': GSC_MIxS_sediment_magnesium_units,
		'GSC_MIxS_sediment_n_alkanes_units': GSC_MIxS_sediment_n_alkanes_units,
		'GSC_MIxS_sediment_nitrate_units': GSC_MIxS_sediment_nitrate_units,
		'GSC_MIxS_sediment_nitrite_units': GSC_MIxS_sediment_nitrite_units,
		'GSC_MIxS_sediment_nitrogen_units': GSC_MIxS_sediment_nitrogen_units,
		'GSC_MIxS_sediment_organic_carbon_units': GSC_MIxS_sediment_organic_carbon_units,
		'GSC_MIxS_sediment_organic_matter_units': GSC_MIxS_sediment_organic_matter_units,
		'GSC_MIxS_sediment_organic_nitrogen_units': GSC_MIxS_sediment_organic_nitrogen_units,
		'GSC_MIxS_sediment_particulate_organic_carbon_units': GSC_MIxS_sediment_particulate_organic_carbon_units,
		'GSC_MIxS_sediment_petroleum_hydrocarbon_units': GSC_MIxS_sediment_petroleum_hydrocarbon_units,
		'GSC_MIxS_sediment_phaeopigments_units': GSC_MIxS_sediment_phaeopigments_units,
		'GSC_MIxS_sediment_phosphate_units': GSC_MIxS_sediment_phosphate_units,
		'GSC_MIxS_sediment_phospholipid_fatty_acid_units': GSC_MIxS_sediment_phospholipid_fatty_acid_units,
		'GSC_MIxS_sediment_potassium_units': GSC_MIxS_sediment_potassium_units,
		'GSC_MIxS_sediment_redox_potential_units': GSC_MIxS_sediment_redox_potential_units,
		'GSC_MIxS_sediment_salinity_units': GSC_MIxS_sediment_salinity_units,
		'GSC_MIxS_sediment_total_carbon_units': GSC_MIxS_sediment_total_carbon_units,
		'GSC_MIxS_sediment_silicate_units': GSC_MIxS_sediment_silicate_units,
		'GSC_MIxS_sediment_sodium_units': GSC_MIxS_sediment_sodium_units,
		'GSC_MIxS_sediment_total_organic_carbon_units': GSC_MIxS_sediment_total_organic_carbon_units,
		'GSC_MIxS_sediment_water_content_units': GSC_MIxS_sediment_water_content_units,
		'GSC_MIxS_sediment_sulfate_units': GSC_MIxS_sediment_sulfate_units,
		'GSC_MIxS_sediment_sulfide_units': GSC_MIxS_sediment_sulfide_units,
		'GSC_MIxS_sediment_total_nitrogen_units': GSC_MIxS_sediment_total_nitrogen_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_sediment_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_sediment_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_sediment_altitude = models.CharField(max_length=100, choices=GSC_MIxS_sediment_altitude_units, blank=False)
	GSC_MIxS_sediment_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_sediment_geographic_location_latitude_units, blank=False)
	GSC_MIxS_sediment_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_sediment_geographic_location_longitude_units, blank=False)
	GSC_MIxS_sediment_depth = models.CharField(max_length=100, choices=GSC_MIxS_sediment_depth_units, blank=False)
	GSC_MIxS_sediment_elevation = models.CharField(max_length=100, choices=GSC_MIxS_sediment_elevation_units, blank=False)
	GSC_MIxS_sediment_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_sediment_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_sediment_biomass = models.CharField(max_length=100, choices=GSC_MIxS_sediment_biomass_units, blank=False)
	GSC_MIxS_sediment_density = models.CharField(max_length=100, choices=GSC_MIxS_sediment_density_units, blank=False)
	GSC_MIxS_sediment_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_sediment_sample_storage_duration_units, blank=False)
	GSC_MIxS_sediment_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_sediment_sample_storage_temperature_units, blank=False)
	GSC_MIxS_sediment_alkyl_diethers = models.CharField(max_length=100, choices=GSC_MIxS_sediment_alkyl_diethers_units, blank=False)
	GSC_MIxS_sediment_aminopeptidase_activity = models.CharField(max_length=100, choices=GSC_MIxS_sediment_aminopeptidase_activity_units, blank=False)
	GSC_MIxS_sediment_ammonium = models.CharField(max_length=100, choices=GSC_MIxS_sediment_ammonium_units, blank=False)
	GSC_MIxS_sediment_bacterial_carbon_production = models.CharField(max_length=100, choices=GSC_MIxS_sediment_bacterial_carbon_production_units, blank=False)
	GSC_MIxS_sediment_bishomohopanol = models.CharField(max_length=100, choices=GSC_MIxS_sediment_bishomohopanol_units, blank=False)
	GSC_MIxS_sediment_bromide = models.CharField(max_length=100, choices=GSC_MIxS_sediment_bromide_units, blank=False)
	GSC_MIxS_sediment_calcium = models.CharField(max_length=100, choices=GSC_MIxS_sediment_calcium_units, blank=False)
	GSC_MIxS_sediment_chloride = models.CharField(max_length=100, choices=GSC_MIxS_sediment_chloride_units, blank=False)
	GSC_MIxS_sediment_chlorophyll = models.CharField(max_length=100, choices=GSC_MIxS_sediment_chlorophyll_units, blank=False)
	GSC_MIxS_sediment_diether_lipids = models.CharField(max_length=100, choices=GSC_MIxS_sediment_diether_lipids_units, blank=False)
	GSC_MIxS_sediment_dissolved_carbon_dioxide = models.CharField(max_length=100, choices=GSC_MIxS_sediment_dissolved_carbon_dioxide_units, blank=False)
	GSC_MIxS_sediment_dissolved_hydrogen = models.CharField(max_length=100, choices=GSC_MIxS_sediment_dissolved_hydrogen_units, blank=False)
	GSC_MIxS_sediment_dissolved_inorganic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_sediment_dissolved_inorganic_carbon_units, blank=False)
	GSC_MIxS_sediment_dissolved_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_sediment_dissolved_organic_carbon_units, blank=False)
	GSC_MIxS_sediment_dissolved_organic_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_sediment_dissolved_organic_nitrogen_units, blank=False)
	GSC_MIxS_sediment_methane = models.CharField(max_length=100, choices=GSC_MIxS_sediment_methane_units, blank=False)
	GSC_MIxS_sediment_dissolved_oxygen = models.CharField(max_length=100, choices=GSC_MIxS_sediment_dissolved_oxygen_units, blank=False)
	GSC_MIxS_sediment_glucosidase_activity = models.CharField(max_length=100, choices=GSC_MIxS_sediment_glucosidase_activity_units, blank=False)
	GSC_MIxS_sediment_magnesium = models.CharField(max_length=100, choices=GSC_MIxS_sediment_magnesium_units, blank=False)
	GSC_MIxS_sediment_n_alkanes = models.CharField(max_length=100, choices=GSC_MIxS_sediment_n_alkanes_units, blank=False)
	GSC_MIxS_sediment_nitrate = models.CharField(max_length=100, choices=GSC_MIxS_sediment_nitrate_units, blank=False)
	GSC_MIxS_sediment_nitrite = models.CharField(max_length=100, choices=GSC_MIxS_sediment_nitrite_units, blank=False)
	GSC_MIxS_sediment_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_sediment_nitrogen_units, blank=False)
	GSC_MIxS_sediment_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_sediment_organic_carbon_units, blank=False)
	GSC_MIxS_sediment_organic_matter = models.CharField(max_length=100, choices=GSC_MIxS_sediment_organic_matter_units, blank=False)
	GSC_MIxS_sediment_organic_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_sediment_organic_nitrogen_units, blank=False)
	GSC_MIxS_sediment_particulate_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_sediment_particulate_organic_carbon_units, blank=False)
	GSC_MIxS_sediment_petroleum_hydrocarbon = models.CharField(max_length=100, choices=GSC_MIxS_sediment_petroleum_hydrocarbon_units, blank=False)
	GSC_MIxS_sediment_phaeopigments = models.CharField(max_length=100, choices=GSC_MIxS_sediment_phaeopigments_units, blank=False)
	GSC_MIxS_sediment_phosphate = models.CharField(max_length=100, choices=GSC_MIxS_sediment_phosphate_units, blank=False)
	GSC_MIxS_sediment_phospholipid_fatty_acid = models.CharField(max_length=100, choices=GSC_MIxS_sediment_phospholipid_fatty_acid_units, blank=False)
	GSC_MIxS_sediment_potassium = models.CharField(max_length=100, choices=GSC_MIxS_sediment_potassium_units, blank=False)
	GSC_MIxS_sediment_redox_potential = models.CharField(max_length=100, choices=GSC_MIxS_sediment_redox_potential_units, blank=False)
	GSC_MIxS_sediment_salinity = models.CharField(max_length=100, choices=GSC_MIxS_sediment_salinity_units, blank=False)
	GSC_MIxS_sediment_total_carbon = models.CharField(max_length=100, choices=GSC_MIxS_sediment_total_carbon_units, blank=False)
	GSC_MIxS_sediment_silicate = models.CharField(max_length=100, choices=GSC_MIxS_sediment_silicate_units, blank=False)
	GSC_MIxS_sediment_sodium = models.CharField(max_length=100, choices=GSC_MIxS_sediment_sodium_units, blank=False)
	GSC_MIxS_sediment_total_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_sediment_total_organic_carbon_units, blank=False)
	GSC_MIxS_sediment_water_content = models.CharField(max_length=100, choices=GSC_MIxS_sediment_water_content_units, blank=False)
	GSC_MIxS_sediment_sulfate = models.CharField(max_length=100, choices=GSC_MIxS_sediment_sulfate_units, blank=False)
	GSC_MIxS_sediment_sulfide = models.CharField(max_length=100, choices=GSC_MIxS_sediment_sulfide_units, blank=False)
	GSC_MIxS_sediment_total_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_sediment_total_nitrogen_units, blank=False)

class GSC_MIxS_human_associated(SelfDescribingModel):

	GSC_MIxS_human_associated_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_human_associated_study_completion_status_choice = [('No - adverse event', 'No - adverse event'), ('No - lost to follow up', 'No - lost to follow up'), ('No - non-compliance', 'No - non-compliance'), ('No - other', 'No - other'), ('Yes', 'Yes')]
	GSC_MIxS_human_associated_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_human_associated_medical_history_performed_choice = [('No', 'No'), ('Yes', 'Yes')]
	GSC_MIxS_human_associated_urine_collection_method_choice = [('catheter', 'catheter'), ('clean catch', 'clean catch')]
	GSC_MIxS_human_associated_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_human_associated_host_HIV_status_choice = [('No', 'No'), ('Yes', 'Yes')]
	GSC_MIxS_human_associated_IHMC_medication_code_choice = [('01=1=Analgesics/NSAIDS', '01=1=Analgesics/NSAIDS'), ('02=2=Anesthetics', '02=2=Anesthetics'), ('03=3=Antacids/H2 antagonists', '03=3=Antacids/H2 antagonists'), ('04=4=Anti-acne', '04=4=Anti-acne'), ('05=5=Anti-asthma/bronchodilators', '05=5=Anti-asthma/bronchodilators'), ('06=6=Anti-cholesterol/Anti-hyperlipidemic', '06=6=Anti-cholesterol/Anti-hyperlipidemic'), ('07=7=Anti-coagulants', '07=7=Anti-coagulants'), ('08=8=Antibiotics/(anti)-infectives, parasitics, microbials', '08=8=Antibiotics/(anti)-infectives, parasitics, microbials'), ('09=9=Antidepressants/mood-altering drugs', '09=9=Antidepressants/mood-altering drugs'), ('10=10=Antihistamines/ Decongestants', '10=10=Antihistamines/ Decongestants'), ('11=11=Antihypertensives', '11=11=Antihypertensives'), ('12=12=Cardiovascular, other than hyperlipidemic/HTN', '12=12=Cardiovascular, other than hyperlipidemic/HTN'), ('13=13=Contraceptives (oral, implant, injectable)', '13=13=Contraceptives (oral, implant, injectable)'), ('14=14=Emergency/support medications', '14=14=Emergency/support medications'), ('15=15=Endocrine/Metabolic agents', '15=15=Endocrine/Metabolic agents'), ('16=16=GI meds (anti-diarrheal, emetic, spasmodics)', '16=16=GI meds (anti-diarrheal, emetic, spasmodics)'), ('17=17=Herbal/homeopathic products', '17=17=Herbal/homeopathic products'), ('18=18=Hormones/steroids', '18=18=Hormones/steroids'), ('19=19=OTC cold & flu', '19=19=OTC cold & flu'), ('20=20=Vaccine prophylaxis', '20=20=Vaccine prophylaxis'), ('21=21=Vitamins, minerals, food supplements', '21=21=Vitamins, minerals, food supplements'), ('99=99=Other', '99=99=Other')]
	GSC_MIxS_human_associated_host_occupation_choice = [('01=01 Accounting/Finance', '01=01 Accounting/Finance'), ('02=02 Advertising/Public Relations', '02=02 Advertising/Public Relations'), ('03=03 Arts/Entertainment/Publishing', '03=03 Arts/Entertainment/Publishing'), ('04=04 Automotive', '04=04 Automotive'), ('05=05 Banking/ Mortgage', '05=05 Banking/ Mortgage'), ('06=06 Biotech', '06=06 Biotech'), ('07=07 Broadcast/Journalism', '07=07 Broadcast/Journalism'), ('08=08 Business Development', '08=08 Business Development'), ('09=09 Clerical/Administrative', '09=09 Clerical/Administrative'), ('10=10 Construction/Trades', '10=10 Construction/Trades'), ('11=11 Consultant', '11=11 Consultant'), ('12=12 Customer Services', '12=12 Customer Services'), ('13=13 Design', '13=13 Design'), ('14=14 Education', '14=14 Education'), ('15=15 Engineering', '15=15 Engineering'), ('16=16 Entry Level', '16=16 Entry Level'), ('17=17 Executive', '17=17 Executive'), ('18=18 Food Service', '18=18 Food Service'), ('19=19 Government', '19=19 Government'), ('20=20 Grocery', '20=20 Grocery'), ('21=21 Healthcare', '21=21 Healthcare'), ('22=22 Hospitality', '22=22 Hospitality'), ('23=23 Human Resources', '23=23 Human Resources'), ('24=24 Information Technology', '24=24 Information Technology'), ('25=25 Insurance', '25=25 Insurance'), ('26=26 Law/Legal', '26=26 Law/Legal'), ('27=27 Management', '27=27 Management'), ('28=28 Manufacturing', '28=28 Manufacturing'), ('29=29 Marketing', '29=29 Marketing'), ('30=30 Pharmaceutical', '30=30 Pharmaceutical'), ('31=31 Professional Services', '31=31 Professional Services'), ('32=32 Purchasing', '32=32 Purchasing'), ('33=33 Quality Assurance (QA)', '33=33 Quality Assurance (QA)'), ('34=34 Research', '34=34 Research'), ('35=35 Restaurant', '35=35 Restaurant'), ('36=36 Retail', '36=36 Retail'), ('37=37 Sales', '37=37 Sales'), ('38=38 Science', '38=38 Science'), ('39=39 Security/Law Enforcement', '39=39 Security/Law Enforcement'), ('40=40 Shipping/Distribution', '40=40 Shipping/Distribution'), ('41=41 Strategy', '41=41 Strategy'), ('42=42 Student', '42=42 Student'), ('43=43 Telecommunications', '43=43 Telecommunications'), ('44=44 Training', '44=44 Training'), ('45=45 Transportation', '45=45 Transportation'), ('46=46 Warehouse', '46=46 Warehouse'), ('47=47 Other', '47=47 Other'), ('99=99 Unknown/Refused', '99=99 Unknown/Refused')]
	GSC_MIxS_human_associated_host_sex_choice = [('female', 'female'), ('hermaphrodite', 'hermaphrodite'), ('male', 'male'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('neuter', 'neuter'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('other', 'other'), ('restricted access', 'restricted access')]
	GSC_MIxS_human_associated_smoker_choice = [('ex-smoker', 'ex-smoker'), ('non-smoker', 'non-smoker'), ('smoker', 'smoker')]
	GSC_MIxS_human_associated_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_human_associated_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_human_associated_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_human_associated_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_associated_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_associated_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_associated_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_associated_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_associated_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_human_associated_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_associated_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_associated_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_human_associated_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_associated_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_associated_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_associated_host_age_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_associated_host_height_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_associated_host_body_mass_index_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_associated_host_total_mass_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_associated_host_body_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_associated_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_associated_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_human_associated_host_pulse_validator = "[+-]?[0-9]+"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_human_associated_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_human_associated_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_human_associated_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_human_associated_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_human_associated_number_of_replicons_validator)])
	GSC_MIxS_human_associated_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_human_associated_extrachromosomal_elements_validator)])
	GSC_MIxS_human_associated_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_human_associated_estimated_size_validator)])
	GSC_MIxS_human_associated_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_human_associated_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_human_associated_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_human_associated_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_human_associated_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_human_associated_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_human_associated_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_human_associated_library_size_validator)])
	GSC_MIxS_human_associated_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_human_associated_library_reads_sequenced_validator)])
	GSC_MIxS_human_associated_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_human_associated_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_human_associated_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_human_associated_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_human_associated_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_human_associated_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_human_associated_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_human_associated_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_human_associated_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_human_associated_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_human_associated_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_human_associated_sequence_quality_check_choice)
	GSC_MIxS_human_associated_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_human_associated_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_human_associated_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_human_associated_study_completion_status= models.CharField(max_length=100, blank=True,help_text="specificat", choices=GSC_MIxS_human_associated_study_completion_status_choice)
	GSC_MIxS_human_associated_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_human_associated_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_human_associated_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_human_associated_collection_date_validator)])
	GSC_MIxS_human_associated_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_human_associated_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_human_associated_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_human_associated_geographic_location_latitude_validator)])
	GSC_MIxS_human_associated_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_human_associated_geographic_location_longitude_validator)])
	GSC_MIxS_human_associated_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_human_associated_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_associated_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_associated_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_human_associated_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_human_associated_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_human_associated_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_human_associated_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_human_associated_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_human_associated_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_human_associated_host_body_product= models.CharField(max_length=100, blank=True,help_text="substance ")
	GSC_MIxS_human_associated_medical_history_performed= models.CharField(max_length=100, blank=True,help_text="whether fu", choices=GSC_MIxS_human_associated_medical_history_performed_choice)
	GSC_MIxS_human_associated_urine_collection_method= models.CharField(max_length=100, blank=True,help_text="specificat", choices=GSC_MIxS_human_associated_urine_collection_method_choice)
	GSC_MIxS_human_associated_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_human_associated_oxygenation_status_of_sample_choice)
	GSC_MIxS_human_associated_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_human_associated_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_human_associated_sample_storage_duration_validator)])
	GSC_MIxS_human_associated_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_human_associated_sample_storage_temperature_validator)])
	GSC_MIxS_human_associated_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_human_associated_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_human_associated_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_human_associated_host_HIV_status= models.CharField(max_length=100, blank=True,help_text="HIV status", choices=GSC_MIxS_human_associated_host_HIV_status_choice)
	GSC_MIxS_human_associated_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_human_associated_lung_pulmonary_disorder= models.CharField(max_length=100, blank=True,help_text="History of")
	GSC_MIxS_human_associated_lung_nose_throat_disorder= models.CharField(max_length=100, blank=True,help_text="History of")
	GSC_MIxS_human_associated_blood_blood_disorder= models.CharField(max_length=100, blank=True,help_text="History of")
	GSC_MIxS_human_associated_urine_kidney_disorder= models.CharField(max_length=100, blank=True,help_text="History of")
	GSC_MIxS_human_associated_urine_urogenital_tract_disorder= models.CharField(max_length=100, blank=True,help_text="History of")
	GSC_MIxS_human_associated_host_subject_id= models.CharField(max_length=100, blank=True,help_text="a unique i")
	GSC_MIxS_human_associated_IHMC_medication_code= models.CharField(max_length=100, blank=True,help_text="can includ", choices=GSC_MIxS_human_associated_IHMC_medication_code_choice)
	GSC_MIxS_human_associated_host_age= models.CharField(max_length=100, blank=True,help_text="age of hos", validators=[RegexValidator(GSC_MIxS_human_associated_host_age_validator)])
	GSC_MIxS_human_associated_host_body_site= models.CharField(max_length=100, blank=True,help_text="name of bo")
	GSC_MIxS_human_associated_drug_usage= models.CharField(max_length=100, blank=True,help_text="any drug u")
	GSC_MIxS_human_associated_host_height= models.CharField(max_length=100, blank=True,help_text="the height", validators=[RegexValidator(GSC_MIxS_human_associated_host_height_validator)])
	GSC_MIxS_human_associated_host_body_mass_index= models.CharField(max_length=100, blank=True,help_text="body mass ", validators=[RegexValidator(GSC_MIxS_human_associated_host_body_mass_index_validator)])
	GSC_MIxS_human_associated_ethnicity= models.CharField(max_length=100, blank=True,help_text="A category")
	GSC_MIxS_human_associated_host_occupation= models.CharField(max_length=100, blank=True,help_text="most frequ", choices=GSC_MIxS_human_associated_host_occupation_choice)
	GSC_MIxS_human_associated_host_total_mass= models.CharField(max_length=100, blank=True,help_text="total mass", validators=[RegexValidator(GSC_MIxS_human_associated_host_total_mass_validator)])
	GSC_MIxS_human_associated_host_phenotype= models.CharField(max_length=100, blank=True,help_text="phenotype ")
	GSC_MIxS_human_associated_host_body_temperature= models.CharField(max_length=100, blank=True,help_text="core body ", validators=[RegexValidator(GSC_MIxS_human_associated_host_body_temperature_validator)])
	GSC_MIxS_human_associated_host_sex= models.CharField(max_length=100, blank=True,help_text="Gender or ", choices=GSC_MIxS_human_associated_host_sex_choice)
	GSC_MIxS_human_associated_host_scientific_name= models.CharField(max_length=100, blank=True,help_text="Scientific")
	GSC_MIxS_human_associated_presence_of_pets_or_farm_animals= models.CharField(max_length=100, blank=True,help_text="specificat")
	GSC_MIxS_human_associated_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_human_associated_temperature_validator)])
	GSC_MIxS_human_associated_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_human_associated_salinity_validator)])
	GSC_MIxS_human_associated_smoker= models.CharField(max_length=100, blank=True,help_text="specificat", choices=GSC_MIxS_human_associated_smoker_choice)
	GSC_MIxS_human_associated_major_diet_change_in_last_six_months= models.CharField(max_length=100, blank=True,help_text="specificat")
	GSC_MIxS_human_associated_weight_loss_in_last_three_months= models.CharField(max_length=100, blank=True,help_text="specificat")
	GSC_MIxS_human_associated_travel_outside_the_country_in_last_six_months= models.CharField(max_length=100, blank=True,help_text="specificat")
	GSC_MIxS_human_associated_host_diet= models.CharField(max_length=100, blank=True,help_text="type of di")
	GSC_MIxS_human_associated_twin_sibling_presence= models.CharField(max_length=100, blank=True,help_text="specificat")
	GSC_MIxS_human_associated_host_last_meal= models.CharField(max_length=100, blank=True,help_text="content of")
	GSC_MIxS_human_associated_amniotic_fluid_gestation_state= models.CharField(max_length=100, blank=True,help_text="specificat")
	GSC_MIxS_human_associated_host_family_relationship= models.CharField(max_length=100, blank=True,help_text="relationsh")
	GSC_MIxS_human_associated_amniotic_fluid_maternal_health_status= models.CharField(max_length=100, blank=True,help_text="specificat")
	GSC_MIxS_human_associated_host_genotype= models.CharField(max_length=100, blank=True,help_text="observed g")
	GSC_MIxS_human_associated_amniotic_fluid_foetal_health_status= models.CharField(max_length=100, blank=True,help_text="specificat")
	GSC_MIxS_human_associated_host_pulse= models.CharField(max_length=100, blank=True,help_text="resting pu", validators=[RegexValidator(GSC_MIxS_human_associated_host_pulse_validator)])
	GSC_MIxS_human_associated_amniotic_fluid_color= models.CharField(max_length=100, blank=True,help_text="specificat")
	GSC_MIxS_human_associated_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_human_associated_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_human_associated_trophic_level_choice)
	GSC_MIxS_human_associated_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_human_associated_relationship_to_oxygen_choice)
	GSC_MIxS_human_associated_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_human_associated_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_human_associated_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_human_associated_observed_biotic_relationship_choice)
	GSC_MIxS_human_associated_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_human_associated_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_human_associated_project_name': GSC_MIxS_human_associated_project_name,
		'GSC_MIxS_human_associated_experimental_factor': GSC_MIxS_human_associated_experimental_factor,
		'GSC_MIxS_human_associated_ploidy': GSC_MIxS_human_associated_ploidy,
		'GSC_MIxS_human_associated_number_of_replicons': GSC_MIxS_human_associated_number_of_replicons,
		'GSC_MIxS_human_associated_extrachromosomal_elements': GSC_MIxS_human_associated_extrachromosomal_elements,
		'GSC_MIxS_human_associated_estimated_size': GSC_MIxS_human_associated_estimated_size,
		'GSC_MIxS_human_associated_reference_for_biomaterial': GSC_MIxS_human_associated_reference_for_biomaterial,
		'GSC_MIxS_human_associated_annotation_source': GSC_MIxS_human_associated_annotation_source,
		'GSC_MIxS_human_associated_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_human_associated_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_human_associated_nucleic_acid_extraction': GSC_MIxS_human_associated_nucleic_acid_extraction,
		'GSC_MIxS_human_associated_nucleic_acid_amplification': GSC_MIxS_human_associated_nucleic_acid_amplification,
		'GSC_MIxS_human_associated_library_size': GSC_MIxS_human_associated_library_size,
		'GSC_MIxS_human_associated_library_reads_sequenced': GSC_MIxS_human_associated_library_reads_sequenced,
		'GSC_MIxS_human_associated_library_construction_method': GSC_MIxS_human_associated_library_construction_method,
		'GSC_MIxS_human_associated_library_vector': GSC_MIxS_human_associated_library_vector,
		'GSC_MIxS_human_associated_library_screening_strategy': GSC_MIxS_human_associated_library_screening_strategy,
		'GSC_MIxS_human_associated_target_gene': GSC_MIxS_human_associated_target_gene,
		'GSC_MIxS_human_associated_target_subfragment': GSC_MIxS_human_associated_target_subfragment,
		'GSC_MIxS_human_associated_pcr_primers': GSC_MIxS_human_associated_pcr_primers,
		'GSC_MIxS_human_associated_multiplex_identifiers': GSC_MIxS_human_associated_multiplex_identifiers,
		'GSC_MIxS_human_associated_adapters': GSC_MIxS_human_associated_adapters,
		'GSC_MIxS_human_associated_pcr_conditions': GSC_MIxS_human_associated_pcr_conditions,
		'GSC_MIxS_human_associated_sequencing_method': GSC_MIxS_human_associated_sequencing_method,
		'GSC_MIxS_human_associated_sequence_quality_check': GSC_MIxS_human_associated_sequence_quality_check,
		'GSC_MIxS_human_associated_chimera_check_software': GSC_MIxS_human_associated_chimera_check_software,
		'GSC_MIxS_human_associated_relevant_electronic_resources': GSC_MIxS_human_associated_relevant_electronic_resources,
		'GSC_MIxS_human_associated_relevant_standard_operating_procedures': GSC_MIxS_human_associated_relevant_standard_operating_procedures,
		'GSC_MIxS_human_associated_study_completion_status': GSC_MIxS_human_associated_study_completion_status,
		'GSC_MIxS_human_associated_negative_control_type': GSC_MIxS_human_associated_negative_control_type,
		'GSC_MIxS_human_associated_positive_control_type': GSC_MIxS_human_associated_positive_control_type,
		'GSC_MIxS_human_associated_collection_date': GSC_MIxS_human_associated_collection_date,
		'GSC_MIxS_human_associated_geographic_location_country_and_or_sea': GSC_MIxS_human_associated_geographic_location_country_and_or_sea,
		'GSC_MIxS_human_associated_geographic_location_latitude': GSC_MIxS_human_associated_geographic_location_latitude,
		'GSC_MIxS_human_associated_geographic_location_longitude': GSC_MIxS_human_associated_geographic_location_longitude,
		'GSC_MIxS_human_associated_geographic_location_region_and_locality': GSC_MIxS_human_associated_geographic_location_region_and_locality,
		'GSC_MIxS_human_associated_broad_scale_environmental_context': GSC_MIxS_human_associated_broad_scale_environmental_context,
		'GSC_MIxS_human_associated_local_environmental_context': GSC_MIxS_human_associated_local_environmental_context,
		'GSC_MIxS_human_associated_environmental_medium': GSC_MIxS_human_associated_environmental_medium,
		'GSC_MIxS_human_associated_source_material_identifiers': GSC_MIxS_human_associated_source_material_identifiers,
		'GSC_MIxS_human_associated_sample_material_processing': GSC_MIxS_human_associated_sample_material_processing,
		'GSC_MIxS_human_associated_isolation_and_growth_condition': GSC_MIxS_human_associated_isolation_and_growth_condition,
		'GSC_MIxS_human_associated_propagation': GSC_MIxS_human_associated_propagation,
		'GSC_MIxS_human_associated_amount_or_size_of_sample_collected': GSC_MIxS_human_associated_amount_or_size_of_sample_collected,
		'GSC_MIxS_human_associated_host_body_product': GSC_MIxS_human_associated_host_body_product,
		'GSC_MIxS_human_associated_medical_history_performed': GSC_MIxS_human_associated_medical_history_performed,
		'GSC_MIxS_human_associated_urine_collection_method': GSC_MIxS_human_associated_urine_collection_method,
		'GSC_MIxS_human_associated_oxygenation_status_of_sample': GSC_MIxS_human_associated_oxygenation_status_of_sample,
		'GSC_MIxS_human_associated_organism_count': GSC_MIxS_human_associated_organism_count,
		'GSC_MIxS_human_associated_sample_storage_duration': GSC_MIxS_human_associated_sample_storage_duration,
		'GSC_MIxS_human_associated_sample_storage_temperature': GSC_MIxS_human_associated_sample_storage_temperature,
		'GSC_MIxS_human_associated_sample_storage_location': GSC_MIxS_human_associated_sample_storage_location,
		'GSC_MIxS_human_associated_sample_collection_device': GSC_MIxS_human_associated_sample_collection_device,
		'GSC_MIxS_human_associated_sample_collection_method': GSC_MIxS_human_associated_sample_collection_method,
		'GSC_MIxS_human_associated_host_HIV_status': GSC_MIxS_human_associated_host_HIV_status,
		'GSC_MIxS_human_associated_host_disease_status': GSC_MIxS_human_associated_host_disease_status,
		'GSC_MIxS_human_associated_lung_pulmonary_disorder': GSC_MIxS_human_associated_lung_pulmonary_disorder,
		'GSC_MIxS_human_associated_lung_nose_throat_disorder': GSC_MIxS_human_associated_lung_nose_throat_disorder,
		'GSC_MIxS_human_associated_blood_blood_disorder': GSC_MIxS_human_associated_blood_blood_disorder,
		'GSC_MIxS_human_associated_urine_kidney_disorder': GSC_MIxS_human_associated_urine_kidney_disorder,
		'GSC_MIxS_human_associated_urine_urogenital_tract_disorder': GSC_MIxS_human_associated_urine_urogenital_tract_disorder,
		'GSC_MIxS_human_associated_host_subject_id': GSC_MIxS_human_associated_host_subject_id,
		'GSC_MIxS_human_associated_IHMC_medication_code': GSC_MIxS_human_associated_IHMC_medication_code,
		'GSC_MIxS_human_associated_host_age': GSC_MIxS_human_associated_host_age,
		'GSC_MIxS_human_associated_host_body_site': GSC_MIxS_human_associated_host_body_site,
		'GSC_MIxS_human_associated_drug_usage': GSC_MIxS_human_associated_drug_usage,
		'GSC_MIxS_human_associated_host_height': GSC_MIxS_human_associated_host_height,
		'GSC_MIxS_human_associated_host_body_mass_index': GSC_MIxS_human_associated_host_body_mass_index,
		'GSC_MIxS_human_associated_ethnicity': GSC_MIxS_human_associated_ethnicity,
		'GSC_MIxS_human_associated_host_occupation': GSC_MIxS_human_associated_host_occupation,
		'GSC_MIxS_human_associated_host_total_mass': GSC_MIxS_human_associated_host_total_mass,
		'GSC_MIxS_human_associated_host_phenotype': GSC_MIxS_human_associated_host_phenotype,
		'GSC_MIxS_human_associated_host_body_temperature': GSC_MIxS_human_associated_host_body_temperature,
		'GSC_MIxS_human_associated_host_sex': GSC_MIxS_human_associated_host_sex,
		'GSC_MIxS_human_associated_host_scientific_name': GSC_MIxS_human_associated_host_scientific_name,
		'GSC_MIxS_human_associated_presence_of_pets_or_farm_animals': GSC_MIxS_human_associated_presence_of_pets_or_farm_animals,
		'GSC_MIxS_human_associated_temperature': GSC_MIxS_human_associated_temperature,
		'GSC_MIxS_human_associated_salinity': GSC_MIxS_human_associated_salinity,
		'GSC_MIxS_human_associated_smoker': GSC_MIxS_human_associated_smoker,
		'GSC_MIxS_human_associated_major_diet_change_in_last_six_months': GSC_MIxS_human_associated_major_diet_change_in_last_six_months,
		'GSC_MIxS_human_associated_weight_loss_in_last_three_months': GSC_MIxS_human_associated_weight_loss_in_last_three_months,
		'GSC_MIxS_human_associated_travel_outside_the_country_in_last_six_months': GSC_MIxS_human_associated_travel_outside_the_country_in_last_six_months,
		'GSC_MIxS_human_associated_host_diet': GSC_MIxS_human_associated_host_diet,
		'GSC_MIxS_human_associated_twin_sibling_presence': GSC_MIxS_human_associated_twin_sibling_presence,
		'GSC_MIxS_human_associated_host_last_meal': GSC_MIxS_human_associated_host_last_meal,
		'GSC_MIxS_human_associated_amniotic_fluid_gestation_state': GSC_MIxS_human_associated_amniotic_fluid_gestation_state,
		'GSC_MIxS_human_associated_host_family_relationship': GSC_MIxS_human_associated_host_family_relationship,
		'GSC_MIxS_human_associated_amniotic_fluid_maternal_health_status': GSC_MIxS_human_associated_amniotic_fluid_maternal_health_status,
		'GSC_MIxS_human_associated_host_genotype': GSC_MIxS_human_associated_host_genotype,
		'GSC_MIxS_human_associated_amniotic_fluid_foetal_health_status': GSC_MIxS_human_associated_amniotic_fluid_foetal_health_status,
		'GSC_MIxS_human_associated_host_pulse': GSC_MIxS_human_associated_host_pulse,
		'GSC_MIxS_human_associated_amniotic_fluid_color': GSC_MIxS_human_associated_amniotic_fluid_color,
		'GSC_MIxS_human_associated_subspecific_genetic_lineage': GSC_MIxS_human_associated_subspecific_genetic_lineage,
		'GSC_MIxS_human_associated_trophic_level': GSC_MIxS_human_associated_trophic_level,
		'GSC_MIxS_human_associated_relationship_to_oxygen': GSC_MIxS_human_associated_relationship_to_oxygen,
		'GSC_MIxS_human_associated_known_pathogenicity': GSC_MIxS_human_associated_known_pathogenicity,
		'GSC_MIxS_human_associated_encoded_traits': GSC_MIxS_human_associated_encoded_traits,
		'GSC_MIxS_human_associated_observed_biotic_relationship': GSC_MIxS_human_associated_observed_biotic_relationship,
		'GSC_MIxS_human_associated_chemical_administration': GSC_MIxS_human_associated_chemical_administration,
		'GSC_MIxS_human_associated_perturbation': GSC_MIxS_human_associated_perturbation,
	}

class GSC_MIxS_human_associated_unit(SelfDescribingModel):

	GSC_MIxS_human_associated_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_human_associated_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_human_associated_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_human_associated_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_human_associated_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_human_associated_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_human_associated_host_age_units = [('centuries', 'centuries'), ('days', 'days'), ('decades', 'decades'), ('hours', 'hours'), ('minutes', 'minutes'), ('months', 'months'), ('seconds', 'seconds'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_human_associated_host_height_units = [('cm', 'cm'), ('m', 'm'), ('mm', 'mm')]
	GSC_MIxS_human_associated_host_body_mass_index_units = [('k', 'k'), ('g', 'g'), ('/', '/'), ('m', 'm'), ('2', '2')]
	GSC_MIxS_human_associated_host_total_mass_units = [('g', 'g'), ('kg', 'kg')]
	GSC_MIxS_human_associated_host_body_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_human_associated_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_human_associated_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]
	GSC_MIxS_human_associated_weight_loss_in_last_three_months_units = [('g', 'g'), ('kg', 'kg')]
	GSC_MIxS_human_associated_host_pulse_units = [('b', 'b'), ('p', 'p'), ('m', 'm')]

	fields = {
		'GSC_MIxS_human_associated_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_human_associated_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_human_associated_geographic_location_latitude_units': GSC_MIxS_human_associated_geographic_location_latitude_units,
		'GSC_MIxS_human_associated_geographic_location_longitude_units': GSC_MIxS_human_associated_geographic_location_longitude_units,
		'GSC_MIxS_human_associated_amount_or_size_of_sample_collected_units': GSC_MIxS_human_associated_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_human_associated_sample_storage_duration_units': GSC_MIxS_human_associated_sample_storage_duration_units,
		'GSC_MIxS_human_associated_sample_storage_temperature_units': GSC_MIxS_human_associated_sample_storage_temperature_units,
		'GSC_MIxS_human_associated_host_age_units': GSC_MIxS_human_associated_host_age_units,
		'GSC_MIxS_human_associated_host_height_units': GSC_MIxS_human_associated_host_height_units,
		'GSC_MIxS_human_associated_host_body_mass_index_units': GSC_MIxS_human_associated_host_body_mass_index_units,
		'GSC_MIxS_human_associated_host_total_mass_units': GSC_MIxS_human_associated_host_total_mass_units,
		'GSC_MIxS_human_associated_host_body_temperature_units': GSC_MIxS_human_associated_host_body_temperature_units,
		'GSC_MIxS_human_associated_temperature_units': GSC_MIxS_human_associated_temperature_units,
		'GSC_MIxS_human_associated_salinity_units': GSC_MIxS_human_associated_salinity_units,
		'GSC_MIxS_human_associated_weight_loss_in_last_three_months_units': GSC_MIxS_human_associated_weight_loss_in_last_three_months_units,
		'GSC_MIxS_human_associated_host_pulse_units': GSC_MIxS_human_associated_host_pulse_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_human_associated_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_human_associated_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_geographic_location_latitude_units, blank=False)
	GSC_MIxS_human_associated_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_geographic_location_longitude_units, blank=False)
	GSC_MIxS_human_associated_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_human_associated_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_sample_storage_duration_units, blank=False)
	GSC_MIxS_human_associated_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_sample_storage_temperature_units, blank=False)
	GSC_MIxS_human_associated_host_age = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_host_age_units, blank=False)
	GSC_MIxS_human_associated_host_height = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_host_height_units, blank=False)
	GSC_MIxS_human_associated_host_body_mass_index = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_host_body_mass_index_units, blank=False)
	GSC_MIxS_human_associated_host_total_mass = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_host_total_mass_units, blank=False)
	GSC_MIxS_human_associated_host_body_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_host_body_temperature_units, blank=False)
	GSC_MIxS_human_associated_temperature = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_temperature_units, blank=False)
	GSC_MIxS_human_associated_salinity = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_salinity_units, blank=False)
	GSC_MIxS_human_associated_weight_loss_in_last_three_months = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_weight_loss_in_last_three_months_units, blank=False)
	GSC_MIxS_human_associated_host_pulse = models.CharField(max_length=100, choices=GSC_MIxS_human_associated_host_pulse_units, blank=False)

class GSC_MIxS_air(SelfDescribingModel):

	GSC_MIxS_air_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_air_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_air_ventilation_type_choice = [('forced ventilation', 'forced ventilation'), ('mechanical ventilation', 'mechanical ventilation'), ('natural ventilation', 'natural ventilation')]
	GSC_MIxS_air_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_air_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_air_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_air_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_air_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_air_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_air_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_air_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_air_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_air_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_air_altitude_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_air_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_air_elevation_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_ventilation_rate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_barometric_pressure_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_humidity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_solar_irradiance_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_wind_speed_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_carbon_dioxide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_carbon_monoxide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_oxygen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_air_particulate_matter_concentration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_methane_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_air_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_air_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_air_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_air_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_air_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_air_number_of_replicons_validator)])
	GSC_MIxS_air_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_air_extrachromosomal_elements_validator)])
	GSC_MIxS_air_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_air_estimated_size_validator)])
	GSC_MIxS_air_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_air_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_air_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_air_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_air_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_air_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_air_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_air_library_size_validator)])
	GSC_MIxS_air_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_air_library_reads_sequenced_validator)])
	GSC_MIxS_air_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_air_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_air_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_air_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_air_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_air_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_air_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_air_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_air_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_air_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_air_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_air_sequence_quality_check_choice)
	GSC_MIxS_air_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_air_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_air_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_air_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_air_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_air_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_air_collection_date_validator)])
	GSC_MIxS_air_altitude= models.CharField(max_length=100, blank=False,help_text="The altitu", validators=[RegexValidator(GSC_MIxS_air_altitude_validator)])
	GSC_MIxS_air_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_air_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_air_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_air_geographic_location_latitude_validator)])
	GSC_MIxS_air_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_air_geographic_location_longitude_validator)])
	GSC_MIxS_air_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_air_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_air_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_air_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_air_elevation= models.CharField(max_length=100, blank=True,help_text="The elevat", validators=[RegexValidator(GSC_MIxS_air_elevation_validator)])
	GSC_MIxS_air_ventilation_rate= models.CharField(max_length=100, blank=True,help_text="ventilatio", validators=[RegexValidator(GSC_MIxS_air_ventilation_rate_validator)])
	GSC_MIxS_air_ventilation_type= models.CharField(max_length=100, blank=True,help_text="The intent", choices=GSC_MIxS_air_ventilation_type_choice)
	GSC_MIxS_air_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_air_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_air_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_air_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_air_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_air_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_air_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_air_oxygenation_status_of_sample_choice)
	GSC_MIxS_air_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_air_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_air_sample_storage_duration_validator)])
	GSC_MIxS_air_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_air_sample_storage_temperature_validator)])
	GSC_MIxS_air_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_air_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_air_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_air_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_air_host_scientific_name= models.CharField(max_length=100, blank=True,help_text="Scientific")
	GSC_MIxS_air_barometric_pressure= models.CharField(max_length=100, blank=True,help_text="force per ", validators=[RegexValidator(GSC_MIxS_air_barometric_pressure_validator)])
	GSC_MIxS_air_humidity= models.CharField(max_length=100, blank=True,help_text="amount of ", validators=[RegexValidator(GSC_MIxS_air_humidity_validator)])
	GSC_MIxS_air_pollutants= models.CharField(max_length=100, blank=True,help_text="pollutant ")
	GSC_MIxS_air_solar_irradiance= models.CharField(max_length=100, blank=True,help_text="the amount", validators=[RegexValidator(GSC_MIxS_air_solar_irradiance_validator)])
	GSC_MIxS_air_wind_direction= models.CharField(max_length=100, blank=True,help_text="wind direc")
	GSC_MIxS_air_wind_speed= models.CharField(max_length=100, blank=True,help_text="speed of w", validators=[RegexValidator(GSC_MIxS_air_wind_speed_validator)])
	GSC_MIxS_air_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_air_temperature_validator)])
	GSC_MIxS_air_carbon_dioxide= models.CharField(max_length=100, blank=True,help_text="carbon dio", validators=[RegexValidator(GSC_MIxS_air_carbon_dioxide_validator)])
	GSC_MIxS_air_carbon_monoxide= models.CharField(max_length=100, blank=True,help_text="carbon mon", validators=[RegexValidator(GSC_MIxS_air_carbon_monoxide_validator)])
	GSC_MIxS_air_oxygen= models.CharField(max_length=100, blank=True,help_text="oxygen (ga", validators=[RegexValidator(GSC_MIxS_air_oxygen_validator)])
	GSC_MIxS_air_air_particulate_matter_concentration= models.CharField(max_length=100, blank=True,help_text="Concentrat", validators=[RegexValidator(GSC_MIxS_air_air_particulate_matter_concentration_validator)])
	GSC_MIxS_air_volatile_organic_compounds= models.CharField(max_length=100, blank=True,help_text="concentrat")
	GSC_MIxS_air_methane= models.CharField(max_length=100, blank=True,help_text="methane (g", validators=[RegexValidator(GSC_MIxS_air_methane_validator)])
	GSC_MIxS_air_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_air_salinity_validator)])
	GSC_MIxS_air_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_air_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_air_trophic_level_choice)
	GSC_MIxS_air_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_air_relationship_to_oxygen_choice)
	GSC_MIxS_air_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_air_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_air_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_air_observed_biotic_relationship_choice)
	GSC_MIxS_air_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_air_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_air_project_name': GSC_MIxS_air_project_name,
		'GSC_MIxS_air_experimental_factor': GSC_MIxS_air_experimental_factor,
		'GSC_MIxS_air_ploidy': GSC_MIxS_air_ploidy,
		'GSC_MIxS_air_number_of_replicons': GSC_MIxS_air_number_of_replicons,
		'GSC_MIxS_air_extrachromosomal_elements': GSC_MIxS_air_extrachromosomal_elements,
		'GSC_MIxS_air_estimated_size': GSC_MIxS_air_estimated_size,
		'GSC_MIxS_air_reference_for_biomaterial': GSC_MIxS_air_reference_for_biomaterial,
		'GSC_MIxS_air_annotation_source': GSC_MIxS_air_annotation_source,
		'GSC_MIxS_air_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_air_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_air_nucleic_acid_extraction': GSC_MIxS_air_nucleic_acid_extraction,
		'GSC_MIxS_air_nucleic_acid_amplification': GSC_MIxS_air_nucleic_acid_amplification,
		'GSC_MIxS_air_library_size': GSC_MIxS_air_library_size,
		'GSC_MIxS_air_library_reads_sequenced': GSC_MIxS_air_library_reads_sequenced,
		'GSC_MIxS_air_library_construction_method': GSC_MIxS_air_library_construction_method,
		'GSC_MIxS_air_library_vector': GSC_MIxS_air_library_vector,
		'GSC_MIxS_air_library_screening_strategy': GSC_MIxS_air_library_screening_strategy,
		'GSC_MIxS_air_target_gene': GSC_MIxS_air_target_gene,
		'GSC_MIxS_air_target_subfragment': GSC_MIxS_air_target_subfragment,
		'GSC_MIxS_air_pcr_primers': GSC_MIxS_air_pcr_primers,
		'GSC_MIxS_air_multiplex_identifiers': GSC_MIxS_air_multiplex_identifiers,
		'GSC_MIxS_air_adapters': GSC_MIxS_air_adapters,
		'GSC_MIxS_air_pcr_conditions': GSC_MIxS_air_pcr_conditions,
		'GSC_MIxS_air_sequencing_method': GSC_MIxS_air_sequencing_method,
		'GSC_MIxS_air_sequence_quality_check': GSC_MIxS_air_sequence_quality_check,
		'GSC_MIxS_air_chimera_check_software': GSC_MIxS_air_chimera_check_software,
		'GSC_MIxS_air_relevant_electronic_resources': GSC_MIxS_air_relevant_electronic_resources,
		'GSC_MIxS_air_relevant_standard_operating_procedures': GSC_MIxS_air_relevant_standard_operating_procedures,
		'GSC_MIxS_air_negative_control_type': GSC_MIxS_air_negative_control_type,
		'GSC_MIxS_air_positive_control_type': GSC_MIxS_air_positive_control_type,
		'GSC_MIxS_air_collection_date': GSC_MIxS_air_collection_date,
		'GSC_MIxS_air_altitude': GSC_MIxS_air_altitude,
		'GSC_MIxS_air_geographic_location_country_and_or_sea': GSC_MIxS_air_geographic_location_country_and_or_sea,
		'GSC_MIxS_air_geographic_location_latitude': GSC_MIxS_air_geographic_location_latitude,
		'GSC_MIxS_air_geographic_location_longitude': GSC_MIxS_air_geographic_location_longitude,
		'GSC_MIxS_air_geographic_location_region_and_locality': GSC_MIxS_air_geographic_location_region_and_locality,
		'GSC_MIxS_air_broad_scale_environmental_context': GSC_MIxS_air_broad_scale_environmental_context,
		'GSC_MIxS_air_local_environmental_context': GSC_MIxS_air_local_environmental_context,
		'GSC_MIxS_air_environmental_medium': GSC_MIxS_air_environmental_medium,
		'GSC_MIxS_air_elevation': GSC_MIxS_air_elevation,
		'GSC_MIxS_air_ventilation_rate': GSC_MIxS_air_ventilation_rate,
		'GSC_MIxS_air_ventilation_type': GSC_MIxS_air_ventilation_type,
		'GSC_MIxS_air_source_material_identifiers': GSC_MIxS_air_source_material_identifiers,
		'GSC_MIxS_air_sample_material_processing': GSC_MIxS_air_sample_material_processing,
		'GSC_MIxS_air_isolation_and_growth_condition': GSC_MIxS_air_isolation_and_growth_condition,
		'GSC_MIxS_air_propagation': GSC_MIxS_air_propagation,
		'GSC_MIxS_air_amount_or_size_of_sample_collected': GSC_MIxS_air_amount_or_size_of_sample_collected,
		'GSC_MIxS_air_oxygenation_status_of_sample': GSC_MIxS_air_oxygenation_status_of_sample,
		'GSC_MIxS_air_organism_count': GSC_MIxS_air_organism_count,
		'GSC_MIxS_air_sample_storage_duration': GSC_MIxS_air_sample_storage_duration,
		'GSC_MIxS_air_sample_storage_temperature': GSC_MIxS_air_sample_storage_temperature,
		'GSC_MIxS_air_sample_storage_location': GSC_MIxS_air_sample_storage_location,
		'GSC_MIxS_air_sample_collection_device': GSC_MIxS_air_sample_collection_device,
		'GSC_MIxS_air_sample_collection_method': GSC_MIxS_air_sample_collection_method,
		'GSC_MIxS_air_host_disease_status': GSC_MIxS_air_host_disease_status,
		'GSC_MIxS_air_host_scientific_name': GSC_MIxS_air_host_scientific_name,
		'GSC_MIxS_air_barometric_pressure': GSC_MIxS_air_barometric_pressure,
		'GSC_MIxS_air_humidity': GSC_MIxS_air_humidity,
		'GSC_MIxS_air_pollutants': GSC_MIxS_air_pollutants,
		'GSC_MIxS_air_solar_irradiance': GSC_MIxS_air_solar_irradiance,
		'GSC_MIxS_air_wind_direction': GSC_MIxS_air_wind_direction,
		'GSC_MIxS_air_wind_speed': GSC_MIxS_air_wind_speed,
		'GSC_MIxS_air_temperature': GSC_MIxS_air_temperature,
		'GSC_MIxS_air_carbon_dioxide': GSC_MIxS_air_carbon_dioxide,
		'GSC_MIxS_air_carbon_monoxide': GSC_MIxS_air_carbon_monoxide,
		'GSC_MIxS_air_oxygen': GSC_MIxS_air_oxygen,
		'GSC_MIxS_air_air_particulate_matter_concentration': GSC_MIxS_air_air_particulate_matter_concentration,
		'GSC_MIxS_air_volatile_organic_compounds': GSC_MIxS_air_volatile_organic_compounds,
		'GSC_MIxS_air_methane': GSC_MIxS_air_methane,
		'GSC_MIxS_air_salinity': GSC_MIxS_air_salinity,
		'GSC_MIxS_air_subspecific_genetic_lineage': GSC_MIxS_air_subspecific_genetic_lineage,
		'GSC_MIxS_air_trophic_level': GSC_MIxS_air_trophic_level,
		'GSC_MIxS_air_relationship_to_oxygen': GSC_MIxS_air_relationship_to_oxygen,
		'GSC_MIxS_air_known_pathogenicity': GSC_MIxS_air_known_pathogenicity,
		'GSC_MIxS_air_encoded_traits': GSC_MIxS_air_encoded_traits,
		'GSC_MIxS_air_observed_biotic_relationship': GSC_MIxS_air_observed_biotic_relationship,
		'GSC_MIxS_air_chemical_administration': GSC_MIxS_air_chemical_administration,
		'GSC_MIxS_air_perturbation': GSC_MIxS_air_perturbation,
	}

class GSC_MIxS_air_unit(SelfDescribingModel):

	GSC_MIxS_air_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_air_altitude_units = [('m', 'm')]
	GSC_MIxS_air_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_air_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_air_elevation_units = [('m', 'm')]
	GSC_MIxS_air_ventilation_rate_units = [('L/sec', 'L/sec'), ('m3/min', 'm3/min')]
	GSC_MIxS_air_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_air_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_air_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_air_barometric_pressure_units = [('Torr', 'Torr'), ('in. Hg', 'in. Hg'), ('millibar(hPa)', 'millibar(hPa)'), ('mm Hg', 'mm Hg')]
	GSC_MIxS_air_humidity_units = [('%', '%'), ('g/m3', 'g/m3')]
	GSC_MIxS_air_pollutants_units = [('M/L', 'M/L'), ('g', 'g'), ('mg/L', 'mg/L')]
	GSC_MIxS_air_solar_irradiance_units = [('W', 'W'), ('/', '/'), ('m', 'm'), ('2', '2')]
	GSC_MIxS_air_wind_speed_units = [('km/h', 'km/h'), ('m/s', 'm/s')]
	GSC_MIxS_air_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_air_carbon_dioxide_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_air_carbon_monoxide_units = [('µ', 'µ'), ('M', 'M'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_air_oxygen_units = [('mg/L', 'mg/L'), ('parts/million', 'parts/million')]
	GSC_MIxS_air_air_particulate_matter_concentration_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('m', 'm'), ('3', '3')]
	GSC_MIxS_air_volatile_organic_compounds_units = [('parts/million', 'parts/million'), ('µg/m3', 'µg/m3')]
	GSC_MIxS_air_methane_units = [('µ', 'µ'), ('M', 'M'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_air_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]

	fields = {
		'GSC_MIxS_air_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_air_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_air_altitude_units': GSC_MIxS_air_altitude_units,
		'GSC_MIxS_air_geographic_location_latitude_units': GSC_MIxS_air_geographic_location_latitude_units,
		'GSC_MIxS_air_geographic_location_longitude_units': GSC_MIxS_air_geographic_location_longitude_units,
		'GSC_MIxS_air_elevation_units': GSC_MIxS_air_elevation_units,
		'GSC_MIxS_air_ventilation_rate_units': GSC_MIxS_air_ventilation_rate_units,
		'GSC_MIxS_air_amount_or_size_of_sample_collected_units': GSC_MIxS_air_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_air_sample_storage_duration_units': GSC_MIxS_air_sample_storage_duration_units,
		'GSC_MIxS_air_sample_storage_temperature_units': GSC_MIxS_air_sample_storage_temperature_units,
		'GSC_MIxS_air_barometric_pressure_units': GSC_MIxS_air_barometric_pressure_units,
		'GSC_MIxS_air_humidity_units': GSC_MIxS_air_humidity_units,
		'GSC_MIxS_air_pollutants_units': GSC_MIxS_air_pollutants_units,
		'GSC_MIxS_air_solar_irradiance_units': GSC_MIxS_air_solar_irradiance_units,
		'GSC_MIxS_air_wind_speed_units': GSC_MIxS_air_wind_speed_units,
		'GSC_MIxS_air_temperature_units': GSC_MIxS_air_temperature_units,
		'GSC_MIxS_air_carbon_dioxide_units': GSC_MIxS_air_carbon_dioxide_units,
		'GSC_MIxS_air_carbon_monoxide_units': GSC_MIxS_air_carbon_monoxide_units,
		'GSC_MIxS_air_oxygen_units': GSC_MIxS_air_oxygen_units,
		'GSC_MIxS_air_air_particulate_matter_concentration_units': GSC_MIxS_air_air_particulate_matter_concentration_units,
		'GSC_MIxS_air_volatile_organic_compounds_units': GSC_MIxS_air_volatile_organic_compounds_units,
		'GSC_MIxS_air_methane_units': GSC_MIxS_air_methane_units,
		'GSC_MIxS_air_salinity_units': GSC_MIxS_air_salinity_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_air_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_air_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_air_altitude = models.CharField(max_length=100, choices=GSC_MIxS_air_altitude_units, blank=False)
	GSC_MIxS_air_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_air_geographic_location_latitude_units, blank=False)
	GSC_MIxS_air_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_air_geographic_location_longitude_units, blank=False)
	GSC_MIxS_air_elevation = models.CharField(max_length=100, choices=GSC_MIxS_air_elevation_units, blank=False)
	GSC_MIxS_air_ventilation_rate = models.CharField(max_length=100, choices=GSC_MIxS_air_ventilation_rate_units, blank=False)
	GSC_MIxS_air_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_air_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_air_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_air_sample_storage_duration_units, blank=False)
	GSC_MIxS_air_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_air_sample_storage_temperature_units, blank=False)
	GSC_MIxS_air_barometric_pressure = models.CharField(max_length=100, choices=GSC_MIxS_air_barometric_pressure_units, blank=False)
	GSC_MIxS_air_humidity = models.CharField(max_length=100, choices=GSC_MIxS_air_humidity_units, blank=False)
	GSC_MIxS_air_pollutants = models.CharField(max_length=100, choices=GSC_MIxS_air_pollutants_units, blank=False)
	GSC_MIxS_air_solar_irradiance = models.CharField(max_length=100, choices=GSC_MIxS_air_solar_irradiance_units, blank=False)
	GSC_MIxS_air_wind_speed = models.CharField(max_length=100, choices=GSC_MIxS_air_wind_speed_units, blank=False)
	GSC_MIxS_air_temperature = models.CharField(max_length=100, choices=GSC_MIxS_air_temperature_units, blank=False)
	GSC_MIxS_air_carbon_dioxide = models.CharField(max_length=100, choices=GSC_MIxS_air_carbon_dioxide_units, blank=False)
	GSC_MIxS_air_carbon_monoxide = models.CharField(max_length=100, choices=GSC_MIxS_air_carbon_monoxide_units, blank=False)
	GSC_MIxS_air_oxygen = models.CharField(max_length=100, choices=GSC_MIxS_air_oxygen_units, blank=False)
	GSC_MIxS_air_air_particulate_matter_concentration = models.CharField(max_length=100, choices=GSC_MIxS_air_air_particulate_matter_concentration_units, blank=False)
	GSC_MIxS_air_volatile_organic_compounds = models.CharField(max_length=100, choices=GSC_MIxS_air_volatile_organic_compounds_units, blank=False)
	GSC_MIxS_air_methane = models.CharField(max_length=100, choices=GSC_MIxS_air_methane_units, blank=False)
	GSC_MIxS_air_salinity = models.CharField(max_length=100, choices=GSC_MIxS_air_salinity_units, blank=False)

class GSC_MIxS_microbial_mat_biolfilm(SelfDescribingModel):

	GSC_MIxS_microbial_mat_biolfilm_sequence_quality_check_choice = [('manual', 'manual'), ('none', 'none'), ('software', 'software')]
	GSC_MIxS_microbial_mat_biolfilm_geographic_location_country_and_or_sea_choice = [('Afghanistan', 'Afghanistan'), ('Albania', 'Albania'), ('Algeria', 'Algeria'), ('American Samoa', 'American Samoa'), ('Andorra', 'Andorra'), ('Angola', 'Angola'), ('Anguilla', 'Anguilla'), ('Antarctica', 'Antarctica'), ('Antigua and Barbuda', 'Antigua and Barbuda'), ('Arctic Ocean', 'Arctic Ocean'), ('Argentina', 'Argentina'), ('Armenia', 'Armenia'), ('Aruba', 'Aruba'), ('Ashmore and Cartier Islands', 'Ashmore and Cartier Islands'), ('Atlantic Ocean', 'Atlantic Ocean'), ('Australia', 'Australia'), ('Austria', 'Austria'), ('Azerbaijan', 'Azerbaijan'), ('Bahamas', 'Bahamas'), ('Bahrain', 'Bahrain'), ('Baker Island', 'Baker Island'), ('Baltic Sea', 'Baltic Sea'), ('Bangladesh', 'Bangladesh'), ('Barbados', 'Barbados'), ('Bassas da India', 'Bassas da India'), ('Belarus', 'Belarus'), ('Belgium', 'Belgium'), ('Belize', 'Belize'), ('Benin', 'Benin'), ('Bermuda', 'Bermuda'), ('Bhutan', 'Bhutan'), ('Bolivia', 'Bolivia'), ('Borneo', 'Borneo'), ('Bosnia and Herzegovina', 'Bosnia and Herzegovina'), ('Botswana', 'Botswana'), ('Bouvet Island', 'Bouvet Island'), ('Brazil', 'Brazil'), ('British Virgin Islands', 'British Virgin Islands'), ('Brunei', 'Brunei'), ('Bulgaria', 'Bulgaria'), ('Burkina Faso', 'Burkina Faso'), ('Burundi', 'Burundi'), ('Cambodia', 'Cambodia'), ('Cameroon', 'Cameroon'), ('Canada', 'Canada'), ('Cape Verde', 'Cape Verde'), ('Cayman Islands', 'Cayman Islands'), ('Central African Republic', 'Central African Republic'), ('Chad', 'Chad'), ('Chile', 'Chile'), ('China', 'China'), ('Christmas Island', 'Christmas Island'), ('Clipperton Island', 'Clipperton Island'), ('Cocos Islands', 'Cocos Islands'), ('Colombia', 'Colombia'), ('Comoros', 'Comoros'), ('Cook Islands', 'Cook Islands'), ('Coral Sea Islands', 'Coral Sea Islands'), ('Costa Rica', 'Costa Rica'), ("Cote d'Ivoire", "Cote d'Ivoire"), ('Croatia', 'Croatia'), ('Cuba', 'Cuba'), ('Curacao', 'Curacao'), ('Cyprus', 'Cyprus'), ('Czech Republic', 'Czech Republic'), ('Democratic Republic of the Congo', 'Democratic Republic of the Congo'), ('Denmark', 'Denmark'), ('Djibouti', 'Djibouti'), ('Dominica', 'Dominica'), ('Dominican Republic', 'Dominican Republic'), ('East Timor', 'East Timor'), ('Ecuador', 'Ecuador'), ('Egypt', 'Egypt'), ('El Salvador', 'El Salvador'), ('Equatorial Guinea', 'Equatorial Guinea'), ('Eritrea', 'Eritrea'), ('Estonia', 'Estonia'), ('Ethiopia', 'Ethiopia'), ('Europa Island', 'Europa Island'), ('Falkland Islands (Islas Malvinas)', 'Falkland Islands (Islas Malvinas)'), ('Faroe Islands', 'Faroe Islands'), ('Fiji', 'Fiji'), ('Finland', 'Finland'), ('France', 'France'), ('French Guiana', 'French Guiana'), ('French Polynesia', 'French Polynesia'), ('French Southern and Antarctic Lands', 'French Southern and Antarctic Lands'), ('Gabon', 'Gabon'), ('Gambia', 'Gambia'), ('Gaza Strip', 'Gaza Strip'), ('Georgia', 'Georgia'), ('Germany', 'Germany'), ('Ghana', 'Ghana'), ('Gibraltar', 'Gibraltar'), ('Glorioso Islands', 'Glorioso Islands'), ('Greece', 'Greece'), ('Greenland', 'Greenland'), ('Grenada', 'Grenada'), ('Guadeloupe', 'Guadeloupe'), ('Guam', 'Guam'), ('Guatemala', 'Guatemala'), ('Guernsey', 'Guernsey'), ('Guinea', 'Guinea'), ('Guinea-Bissau', 'Guinea-Bissau'), ('Guyana', 'Guyana'), ('Haiti', 'Haiti'), ('Heard Island and McDonald Islands', 'Heard Island and McDonald Islands'), ('Honduras', 'Honduras'), ('Hong Kong', 'Hong Kong'), ('Howland Island', 'Howland Island'), ('Hungary', 'Hungary'), ('Iceland', 'Iceland'), ('India', 'India'), ('Indian Ocean', 'Indian Ocean'), ('Indonesia', 'Indonesia'), ('Iran', 'Iran'), ('Iraq', 'Iraq'), ('Ireland', 'Ireland'), ('Isle of Man', 'Isle of Man'), ('Israel', 'Israel'), ('Italy', 'Italy'), ('Jamaica', 'Jamaica'), ('Jan Mayen', 'Jan Mayen'), ('Japan', 'Japan'), ('Jarvis Island', 'Jarvis Island'), ('Jersey', 'Jersey'), ('Johnston Atoll', 'Johnston Atoll'), ('Jordan', 'Jordan'), ('Juan de Nova Island', 'Juan de Nova Island'), ('Kazakhstan', 'Kazakhstan'), ('Kenya', 'Kenya'), ('Kerguelen Archipelago', 'Kerguelen Archipelago'), ('Kingman Reef', 'Kingman Reef'), ('Kiribati', 'Kiribati'), ('Kosovo', 'Kosovo'), ('Kuwait', 'Kuwait'), ('Kyrgyzstan', 'Kyrgyzstan'), ('Laos', 'Laos'), ('Latvia', 'Latvia'), ('Lebanon', 'Lebanon'), ('Lesotho', 'Lesotho'), ('Liberia', 'Liberia'), ('Libya', 'Libya'), ('Liechtenstein', 'Liechtenstein'), ('Lithuania', 'Lithuania'), ('Luxembourg', 'Luxembourg'), ('Macau', 'Macau'), ('Macedonia', 'Macedonia'), ('Madagascar', 'Madagascar'), ('Malawi', 'Malawi'), ('Malaysia', 'Malaysia'), ('Maldives', 'Maldives'), ('Mali', 'Mali'), ('Malta', 'Malta'), ('Marshall Islands', 'Marshall Islands'), ('Martinique', 'Martinique'), ('Mauritania', 'Mauritania'), ('Mauritius', 'Mauritius'), ('Mayotte', 'Mayotte'), ('Mediterranean Sea', 'Mediterranean Sea'), ('Mexico', 'Mexico'), ('Micronesia', 'Micronesia'), ('Midway Islands', 'Midway Islands'), ('Moldova', 'Moldova'), ('Monaco', 'Monaco'), ('Mongolia', 'Mongolia'), ('Montenegro', 'Montenegro'), ('Montserrat', 'Montserrat'), ('Morocco', 'Morocco'), ('Mozambique', 'Mozambique'), ('Myanmar', 'Myanmar'), ('Namibia', 'Namibia'), ('Nauru', 'Nauru'), ('Navassa Island', 'Navassa Island'), ('Nepal', 'Nepal'), ('Netherlands', 'Netherlands'), ('New Caledonia', 'New Caledonia'), ('New Zealand', 'New Zealand'), ('Nicaragua', 'Nicaragua'), ('Niger', 'Niger'), ('Nigeria', 'Nigeria'), ('Niue', 'Niue'), ('Norfolk Island', 'Norfolk Island'), ('North Korea', 'North Korea'), ('North Sea', 'North Sea'), ('Northern Mariana Islands', 'Northern Mariana Islands'), ('Norway', 'Norway'), ('Oman', 'Oman'), ('Pacific Ocean', 'Pacific Ocean'), ('Pakistan', 'Pakistan'), ('Palau', 'Palau'), ('Palmyra Atoll', 'Palmyra Atoll'), ('Panama', 'Panama'), ('Papua New Guinea', 'Papua New Guinea'), ('Paracel Islands', 'Paracel Islands'), ('Paraguay', 'Paraguay'), ('Peru', 'Peru'), ('Philippines', 'Philippines'), ('Pitcairn Islands', 'Pitcairn Islands'), ('Poland', 'Poland'), ('Portugal', 'Portugal'), ('Puerto Rico', 'Puerto Rico'), ('Qatar', 'Qatar'), ('Republic of the Congo', 'Republic of the Congo'), ('Reunion', 'Reunion'), ('Romania', 'Romania'), ('Ross Sea', 'Ross Sea'), ('Russia', 'Russia'), ('Rwanda', 'Rwanda'), ('Saint Helena', 'Saint Helena'), ('Saint Kitts and Nevis', 'Saint Kitts and Nevis'), ('Saint Lucia', 'Saint Lucia'), ('Saint Pierre and Miquelon', 'Saint Pierre and Miquelon'), ('Saint Vincent and the Grenadines', 'Saint Vincent and the Grenadines'), ('Samoa', 'Samoa'), ('San Marino', 'San Marino'), ('Sao Tome and Principe', 'Sao Tome and Principe'), ('Saudi Arabia', 'Saudi Arabia'), ('Senegal', 'Senegal'), ('Serbia', 'Serbia'), ('Seychelles', 'Seychelles'), ('Sierra Leone', 'Sierra Leone'), ('Singapore', 'Singapore'), ('Sint Maarten', 'Sint Maarten'), ('Slovakia', 'Slovakia'), ('Slovenia', 'Slovenia'), ('Solomon Islands', 'Solomon Islands'), ('Somalia', 'Somalia'), ('South Africa', 'South Africa'), ('South Georgia and the South Sandwich Islands', 'South Georgia and the South Sandwich Islands'), ('South Korea', 'South Korea'), ('Southern Ocean', 'Southern Ocean'), ('Spain', 'Spain'), ('Spratly Islands', 'Spratly Islands'), ('Sri Lanka', 'Sri Lanka'), ('Sudan', 'Sudan'), ('Suriname', 'Suriname'), ('Svalbard', 'Svalbard'), ('Swaziland', 'Swaziland'), ('Sweden', 'Sweden'), ('Switzerland', 'Switzerland'), ('Syria', 'Syria'), ('Taiwan', 'Taiwan'), ('Tajikistan', 'Tajikistan'), ('Tanzania', 'Tanzania'), ('Tasman Sea', 'Tasman Sea'), ('Thailand', 'Thailand'), ('Togo', 'Togo'), ('Tokelau', 'Tokelau'), ('Tonga', 'Tonga'), ('Trinidad and Tobago', 'Trinidad and Tobago'), ('Tromelin Island', 'Tromelin Island'), ('Tunisia', 'Tunisia'), ('Turkey', 'Turkey'), ('Turkmenistan', 'Turkmenistan'), ('Turks and Caicos Islands', 'Turks and Caicos Islands'), ('Tuvalu', 'Tuvalu'), ('USA', 'USA'), ('Uganda', 'Uganda'), ('Ukraine', 'Ukraine'), ('United Arab Emirates', 'United Arab Emirates'), ('United Kingdom', 'United Kingdom'), ('Uruguay', 'Uruguay'), ('Uzbekistan', 'Uzbekistan'), ('Vanuatu', 'Vanuatu'), ('Venezuela', 'Venezuela'), ('Viet Nam', 'Viet Nam'), ('Virgin Islands', 'Virgin Islands'), ('Wake Island', 'Wake Island'), ('Wallis and Futuna', 'Wallis and Futuna'), ('West Bank', 'West Bank'), ('Western Sahara', 'Western Sahara'), ('Yemen', 'Yemen'), ('Zambia', 'Zambia'), ('Zimbabwe', 'Zimbabwe'), ('missing: control sample', 'missing: control sample'), ('missing: data agreement established pre-2023', 'missing: data agreement established pre-2023'), ('missing: endangered species', 'missing: endangered species'), ('missing: human-identifiable', 'missing: human-identifiable'), ('missing: lab stock', 'missing: lab stock'), ('missing: sample group', 'missing: sample group'), ('missing: synthetic construct', 'missing: synthetic construct'), ('missing: third party data', 'missing: third party data'), ('not applicable', 'not applicable'), ('not collected', 'not collected'), ('not provided', 'not provided'), ('restricted access', 'restricted access')]
	GSC_MIxS_microbial_mat_biolfilm_oxygenation_status_of_sample_choice = [('aerobic', 'aerobic'), ('anaerobic', 'anaerobic')]
	GSC_MIxS_microbial_mat_biolfilm_trophic_level_choice = [('autotroph', 'autotroph'), ('carboxydotroph', 'carboxydotroph'), ('chemoautotroph', 'chemoautotroph'), ('chemoheterotroph', 'chemoheterotroph'), ('chemolithoautotroph', 'chemolithoautotroph'), ('chemolithotroph', 'chemolithotroph'), ('chemoorganoheterotroph', 'chemoorganoheterotroph'), ('chemoorganotroph', 'chemoorganotroph'), ('chemosynthetic', 'chemosynthetic'), ('chemotroph', 'chemotroph'), ('copiotroph', 'copiotroph'), ('diazotroph', 'diazotroph'), ('facultative autotroph', 'facultative autotroph'), ('heterotroph', 'heterotroph'), ('lithoautotroph', 'lithoautotroph'), ('lithoheterotroph', 'lithoheterotroph'), ('lithotroph', 'lithotroph'), ('methanotroph', 'methanotroph'), ('methylotroph', 'methylotroph'), ('mixotroph', 'mixotroph'), ('obligate chemoautolithotroph', 'obligate chemoautolithotroph'), ('oligotroph', 'oligotroph'), ('organoheterotroph', 'organoheterotroph'), ('organotroph', 'organotroph'), ('photoautotroph', 'photoautotroph'), ('photoheterotroph', 'photoheterotroph'), ('photolithoautotroph', 'photolithoautotroph'), ('photolithotroph', 'photolithotroph'), ('photosynthetic', 'photosynthetic'), ('phototroph', 'phototroph')]
	GSC_MIxS_microbial_mat_biolfilm_relationship_to_oxygen_choice = [('aerobe', 'aerobe'), ('anaerobe', 'anaerobe'), ('facultative', 'facultative'), ('microaerophilic', 'microaerophilic'), ('microanaerobe', 'microanaerobe'), ('obligate aerobe', 'obligate aerobe'), ('obligate anaerobe', 'obligate anaerobe')]
	GSC_MIxS_microbial_mat_biolfilm_observed_biotic_relationship_choice = [('commensal', 'commensal'), ('free living', 'free living'), ('mutualism', 'mutualism'), ('parasite', 'parasite'), ('symbiont', 'symbiont')]

	GSC_MIxS_microbial_mat_biolfilm_number_of_replicons_validator = "[+-]?[0-9]+"
	GSC_MIxS_microbial_mat_biolfilm_extrachromosomal_elements_validator = "[+-]?[0-9]+"
	GSC_MIxS_microbial_mat_biolfilm_estimated_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_microbial_mat_biolfilm_sample_volume_or_weight_for_DNA_extraction_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_library_size_validator = "[+-]?[0-9]+"
	GSC_MIxS_microbial_mat_biolfilm_library_reads_sequenced_validator = "[+-]?[0-9]+"
	GSC_MIxS_microbial_mat_biolfilm_collection_date_validator = "(^[12][0-9]{3}(-(0[1-9]|1[0-2])(-(0[1-9]|[12][0-9]|3[01])(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?(/[0-9]{4}(-[0-9]{2}(-[0-9]{2}(T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z?([+-][0-9]{1,2})?)?)?)?)?$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_microbial_mat_biolfilm_altitude_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_geographic_location_latitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_microbial_mat_biolfilm_geographic_location_longitude_validator = "(^[+-]?[0-9]+.?[0-9]{0,8}$)|(^not collected$)|(^not provided$)|(^restricted access$)|(^missing: control sample$)|(^missing: sample group$)|(^missing: synthetic construct$)|(^missing: lab stock$)|(^missing: third party data$)|(^missing: data agreement established pre-2023$)|(^missing: endangered species$)|(^missing: human-identifiable$)"
	GSC_MIxS_microbial_mat_biolfilm_depth_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_elevation_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_amount_or_size_of_sample_collected_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_sample_storage_duration_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_sample_storage_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_alkalinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_mean_friction_velocity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_mean_peak_friction_velocity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_pressure_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_temperature_validator = "[+-]?(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_turbidity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_pH_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_alkyl_diethers_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_aminopeptidase_activity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_ammonium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_bacterial_carbon_production_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_bishomohopanol_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_bromide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_calcium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_carbon_nitrogen_ratio_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_chloride_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_chlorophyll_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_diether_lipids_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_dissolved_carbon_dioxide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_dissolved_hydrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_dissolved_inorganic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_methane_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_dissolved_oxygen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_glucosidase_activity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_magnesium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_n_alkanes_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_nitrate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_nitrite_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_organic_matter_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_organic_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_particulate_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_petroleum_hydrocarbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_phaeopigments_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_phosphate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_phospholipid_fatty_acid_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_potassium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_redox_potential_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_salinity_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_total_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_silicate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_sodium_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_total_organic_carbon_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_water_content_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_sulfate_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_sulfide_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"
	GSC_MIxS_microbial_mat_biolfilm_total_nitrogen_validator = "(0|((0\.)|([1-9][0-9]*\.?))[0-9]*)([Ee][+-]?[0-9]+)?"

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_microbial_mat_biolfilm_project_name= models.CharField(max_length=100, blank=False,help_text="Name of th")
	GSC_MIxS_microbial_mat_biolfilm_experimental_factor= models.CharField(max_length=100, blank=True,help_text="Experiment")
	GSC_MIxS_microbial_mat_biolfilm_ploidy= models.CharField(max_length=100, blank=True,help_text="The ploidy")
	GSC_MIxS_microbial_mat_biolfilm_number_of_replicons= models.CharField(max_length=100, blank=True,help_text="Reports th", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_number_of_replicons_validator)])
	GSC_MIxS_microbial_mat_biolfilm_extrachromosomal_elements= models.CharField(max_length=100, blank=True,help_text="Do plasmid", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_extrachromosomal_elements_validator)])
	GSC_MIxS_microbial_mat_biolfilm_estimated_size= models.CharField(max_length=100, blank=True,help_text="The estima", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_estimated_size_validator)])
	GSC_MIxS_microbial_mat_biolfilm_reference_for_biomaterial= models.CharField(max_length=100, blank=True,help_text="Primary pu")
	GSC_MIxS_microbial_mat_biolfilm_annotation_source= models.CharField(max_length=100, blank=True,help_text="For cases ")
	GSC_MIxS_microbial_mat_biolfilm_sample_volume_or_weight_for_DNA_extraction= models.CharField(max_length=100, blank=True,help_text="Volume (ml", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_sample_volume_or_weight_for_DNA_extraction_validator)])
	GSC_MIxS_microbial_mat_biolfilm_nucleic_acid_extraction= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_microbial_mat_biolfilm_nucleic_acid_amplification= models.CharField(max_length=100, blank=True,help_text="A link to ")
	GSC_MIxS_microbial_mat_biolfilm_library_size= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_library_size_validator)])
	GSC_MIxS_microbial_mat_biolfilm_library_reads_sequenced= models.CharField(max_length=100, blank=True,help_text="Total numb", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_library_reads_sequenced_validator)])
	GSC_MIxS_microbial_mat_biolfilm_library_construction_method= models.CharField(max_length=100, blank=True,help_text="Library co")
	GSC_MIxS_microbial_mat_biolfilm_library_vector= models.CharField(max_length=100, blank=True,help_text="Cloning ve")
	GSC_MIxS_microbial_mat_biolfilm_library_screening_strategy= models.CharField(max_length=100, blank=True,help_text="Specific e")
	GSC_MIxS_microbial_mat_biolfilm_target_gene= models.CharField(max_length=100, blank=True,help_text="Targeted g")
	GSC_MIxS_microbial_mat_biolfilm_target_subfragment= models.CharField(max_length=100, blank=True,help_text="Name of su")
	GSC_MIxS_microbial_mat_biolfilm_pcr_primers= models.CharField(max_length=100, blank=True,help_text="PCR primer")
	GSC_MIxS_microbial_mat_biolfilm_multiplex_identifiers= models.CharField(max_length=100, blank=True,help_text="Molecular ")
	GSC_MIxS_microbial_mat_biolfilm_adapters= models.CharField(max_length=100, blank=True,help_text="Adapters p")
	GSC_MIxS_microbial_mat_biolfilm_pcr_conditions= models.CharField(max_length=100, blank=True,help_text="Descriptio")
	GSC_MIxS_microbial_mat_biolfilm_sequencing_method= models.CharField(max_length=100, blank=True,help_text="Sequencing")
	GSC_MIxS_microbial_mat_biolfilm_sequence_quality_check= models.CharField(max_length=100, blank=True,help_text="Indicate i", choices=GSC_MIxS_microbial_mat_biolfilm_sequence_quality_check_choice)
	GSC_MIxS_microbial_mat_biolfilm_chimera_check_software= models.CharField(max_length=100, blank=True,help_text="Tool(s) us")
	GSC_MIxS_microbial_mat_biolfilm_relevant_electronic_resources= models.CharField(max_length=100, blank=True,help_text="A related ")
	GSC_MIxS_microbial_mat_biolfilm_relevant_standard_operating_procedures= models.CharField(max_length=100, blank=True,help_text="Standard o")
	GSC_MIxS_microbial_mat_biolfilm_negative_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_microbial_mat_biolfilm_positive_control_type= models.CharField(max_length=100, blank=True,help_text="The substa")
	GSC_MIxS_microbial_mat_biolfilm_collection_date= models.CharField(max_length=100, blank=False,help_text="The date t", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_collection_date_validator)])
	GSC_MIxS_microbial_mat_biolfilm_altitude= models.CharField(max_length=100, blank=True,help_text="The altitu", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_altitude_validator)])
	GSC_MIxS_microbial_mat_biolfilm_geographic_location_country_and_or_sea= models.CharField(max_length=100, blank=False,help_text="The locati", choices=GSC_MIxS_microbial_mat_biolfilm_geographic_location_country_and_or_sea_choice)
	GSC_MIxS_microbial_mat_biolfilm_geographic_location_latitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_geographic_location_latitude_validator)])
	GSC_MIxS_microbial_mat_biolfilm_geographic_location_longitude= models.CharField(max_length=100, blank=False,help_text="The geogra", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_geographic_location_longitude_validator)])
	GSC_MIxS_microbial_mat_biolfilm_geographic_location_region_and_locality= models.CharField(max_length=100, blank=True,help_text="The geogra")
	GSC_MIxS_microbial_mat_biolfilm_depth= models.CharField(max_length=100, blank=False,help_text="The vertic", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_depth_validator)])
	GSC_MIxS_microbial_mat_biolfilm_broad_scale_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_microbial_mat_biolfilm_local_environmental_context= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_microbial_mat_biolfilm_environmental_medium= models.CharField(max_length=100, blank=False,help_text="Report the")
	GSC_MIxS_microbial_mat_biolfilm_elevation= models.CharField(max_length=100, blank=False,help_text="The elevat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_elevation_validator)])
	GSC_MIxS_microbial_mat_biolfilm_source_material_identifiers= models.CharField(max_length=100, blank=True,help_text="A unique i")
	GSC_MIxS_microbial_mat_biolfilm_sample_material_processing= models.CharField(max_length=100, blank=True,help_text="A brief de")
	GSC_MIxS_microbial_mat_biolfilm_isolation_and_growth_condition= models.CharField(max_length=100, blank=True,help_text="Publicatio")
	GSC_MIxS_microbial_mat_biolfilm_propagation= models.CharField(max_length=100, blank=True,help_text="The type o")
	GSC_MIxS_microbial_mat_biolfilm_amount_or_size_of_sample_collected= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_amount_or_size_of_sample_collected_validator)])
	GSC_MIxS_microbial_mat_biolfilm_biomass= models.CharField(max_length=100, blank=True,help_text="amount of ")
	GSC_MIxS_microbial_mat_biolfilm_oxygenation_status_of_sample= models.CharField(max_length=100, blank=True,help_text="oxygenatio", choices=GSC_MIxS_microbial_mat_biolfilm_oxygenation_status_of_sample_choice)
	GSC_MIxS_microbial_mat_biolfilm_organism_count= models.CharField(max_length=100, blank=True,help_text="Total cell")
	GSC_MIxS_microbial_mat_biolfilm_sample_storage_duration= models.CharField(max_length=100, blank=True,help_text="duration f", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_sample_storage_duration_validator)])
	GSC_MIxS_microbial_mat_biolfilm_sample_storage_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_sample_storage_temperature_validator)])
	GSC_MIxS_microbial_mat_biolfilm_sample_storage_location= models.CharField(max_length=100, blank=True,help_text="location a")
	GSC_MIxS_microbial_mat_biolfilm_sample_collection_device= models.CharField(max_length=100, blank=True,help_text="The device")
	GSC_MIxS_microbial_mat_biolfilm_sample_collection_method= models.CharField(max_length=100, blank=True,help_text="The method")
	GSC_MIxS_microbial_mat_biolfilm_host_disease_status= models.CharField(max_length=100, blank=True,help_text="list of di")
	GSC_MIxS_microbial_mat_biolfilm_host_scientific_name= models.CharField(max_length=100, blank=True,help_text="Scientific")
	GSC_MIxS_microbial_mat_biolfilm_alkalinity= models.CharField(max_length=100, blank=True,help_text="alkalinity", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_alkalinity_validator)])
	GSC_MIxS_microbial_mat_biolfilm_mean_friction_velocity= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_mean_friction_velocity_validator)])
	GSC_MIxS_microbial_mat_biolfilm_mean_peak_friction_velocity= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_mean_peak_friction_velocity_validator)])
	GSC_MIxS_microbial_mat_biolfilm_pressure= models.CharField(max_length=100, blank=True,help_text="pressure t", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_pressure_validator)])
	GSC_MIxS_microbial_mat_biolfilm_temperature= models.CharField(max_length=100, blank=True,help_text="temperatur", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_temperature_validator)])
	GSC_MIxS_microbial_mat_biolfilm_turbidity= models.CharField(max_length=100, blank=True,help_text="turbidity ", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_turbidity_validator)])
	GSC_MIxS_microbial_mat_biolfilm_pH= models.CharField(max_length=100, blank=True,help_text="pH measure", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_pH_validator)])
	GSC_MIxS_microbial_mat_biolfilm_alkyl_diethers= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_alkyl_diethers_validator)])
	GSC_MIxS_microbial_mat_biolfilm_aminopeptidase_activity= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_aminopeptidase_activity_validator)])
	GSC_MIxS_microbial_mat_biolfilm_ammonium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_ammonium_validator)])
	GSC_MIxS_microbial_mat_biolfilm_bacterial_carbon_production= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_bacterial_carbon_production_validator)])
	GSC_MIxS_microbial_mat_biolfilm_bishomohopanol= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_bishomohopanol_validator)])
	GSC_MIxS_microbial_mat_biolfilm_bromide= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_bromide_validator)])
	GSC_MIxS_microbial_mat_biolfilm_calcium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_calcium_validator)])
	GSC_MIxS_microbial_mat_biolfilm_carbon_nitrogen_ratio= models.CharField(max_length=100, blank=True,help_text="ratio of a", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_carbon_nitrogen_ratio_validator)])
	GSC_MIxS_microbial_mat_biolfilm_chloride= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_chloride_validator)])
	GSC_MIxS_microbial_mat_biolfilm_chlorophyll= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_chlorophyll_validator)])
	GSC_MIxS_microbial_mat_biolfilm_diether_lipids= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_diether_lipids_validator)])
	GSC_MIxS_microbial_mat_biolfilm_dissolved_carbon_dioxide= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_dissolved_carbon_dioxide_validator)])
	GSC_MIxS_microbial_mat_biolfilm_dissolved_hydrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_dissolved_hydrogen_validator)])
	GSC_MIxS_microbial_mat_biolfilm_dissolved_inorganic_carbon= models.CharField(max_length=100, blank=True,help_text="dissolved ", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_dissolved_inorganic_carbon_validator)])
	GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_carbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_carbon_validator)])
	GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_nitrogen= models.CharField(max_length=100, blank=True,help_text="dissolved ", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_nitrogen_validator)])
	GSC_MIxS_microbial_mat_biolfilm_methane= models.CharField(max_length=100, blank=True,help_text="methane (g", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_methane_validator)])
	GSC_MIxS_microbial_mat_biolfilm_dissolved_oxygen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_dissolved_oxygen_validator)])
	GSC_MIxS_microbial_mat_biolfilm_glucosidase_activity= models.CharField(max_length=100, blank=True,help_text="measuremen", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_glucosidase_activity_validator)])
	GSC_MIxS_microbial_mat_biolfilm_magnesium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_magnesium_validator)])
	GSC_MIxS_microbial_mat_biolfilm_n_alkanes= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_n_alkanes_validator)])
	GSC_MIxS_microbial_mat_biolfilm_nitrate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_nitrate_validator)])
	GSC_MIxS_microbial_mat_biolfilm_nitrite= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_nitrite_validator)])
	GSC_MIxS_microbial_mat_biolfilm_nitrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_nitrogen_validator)])
	GSC_MIxS_microbial_mat_biolfilm_organic_carbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_organic_carbon_validator)])
	GSC_MIxS_microbial_mat_biolfilm_organic_matter= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_organic_matter_validator)])
	GSC_MIxS_microbial_mat_biolfilm_organic_nitrogen= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_organic_nitrogen_validator)])
	GSC_MIxS_microbial_mat_biolfilm_particulate_organic_carbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_particulate_organic_carbon_validator)])
	GSC_MIxS_microbial_mat_biolfilm_petroleum_hydrocarbon= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_petroleum_hydrocarbon_validator)])
	GSC_MIxS_microbial_mat_biolfilm_phaeopigments= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_phaeopigments_validator)])
	GSC_MIxS_microbial_mat_biolfilm_phosphate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_phosphate_validator)])
	GSC_MIxS_microbial_mat_biolfilm_phospholipid_fatty_acid= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_phospholipid_fatty_acid_validator)])
	GSC_MIxS_microbial_mat_biolfilm_potassium= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_potassium_validator)])
	GSC_MIxS_microbial_mat_biolfilm_redox_potential= models.CharField(max_length=100, blank=True,help_text="redox pote", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_redox_potential_validator)])
	GSC_MIxS_microbial_mat_biolfilm_salinity= models.CharField(max_length=100, blank=True,help_text="The total ", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_salinity_validator)])
	GSC_MIxS_microbial_mat_biolfilm_total_carbon= models.CharField(max_length=100, blank=True,help_text="total carb", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_total_carbon_validator)])
	GSC_MIxS_microbial_mat_biolfilm_silicate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_silicate_validator)])
	GSC_MIxS_microbial_mat_biolfilm_sodium= models.CharField(max_length=100, blank=True,help_text="sodium con", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_sodium_validator)])
	GSC_MIxS_microbial_mat_biolfilm_total_organic_carbon= models.CharField(max_length=100, blank=True,help_text="Definition", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_total_organic_carbon_validator)])
	GSC_MIxS_microbial_mat_biolfilm_water_content= models.CharField(max_length=100, blank=True,help_text="water cont", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_water_content_validator)])
	GSC_MIxS_microbial_mat_biolfilm_sulfate= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_sulfate_validator)])
	GSC_MIxS_microbial_mat_biolfilm_sulfide= models.CharField(max_length=100, blank=True,help_text="concentrat", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_sulfide_validator)])
	GSC_MIxS_microbial_mat_biolfilm_total_nitrogen= models.CharField(max_length=100, blank=True,help_text="total nitr", validators=[RegexValidator(GSC_MIxS_microbial_mat_biolfilm_total_nitrogen_validator)])
	GSC_MIxS_microbial_mat_biolfilm_subspecific_genetic_lineage= models.CharField(max_length=100, blank=True,help_text="Informatio")
	GSC_MIxS_microbial_mat_biolfilm_trophic_level= models.CharField(max_length=100, blank=True,help_text="Trophic le", choices=GSC_MIxS_microbial_mat_biolfilm_trophic_level_choice)
	GSC_MIxS_microbial_mat_biolfilm_relationship_to_oxygen= models.CharField(max_length=100, blank=True,help_text="Is this or", choices=GSC_MIxS_microbial_mat_biolfilm_relationship_to_oxygen_choice)
	GSC_MIxS_microbial_mat_biolfilm_known_pathogenicity= models.CharField(max_length=100, blank=True,help_text="To what is")
	GSC_MIxS_microbial_mat_biolfilm_encoded_traits= models.CharField(max_length=100, blank=True,help_text="Should inc")
	GSC_MIxS_microbial_mat_biolfilm_observed_biotic_relationship= models.CharField(max_length=100, blank=True,help_text="Is it free", choices=GSC_MIxS_microbial_mat_biolfilm_observed_biotic_relationship_choice)
	GSC_MIxS_microbial_mat_biolfilm_chemical_administration= models.CharField(max_length=100, blank=True,help_text="list of ch")
	GSC_MIxS_microbial_mat_biolfilm_perturbation= models.CharField(max_length=100, blank=True,help_text="type of pe")

	fields = {
		'GSC_MIxS_microbial_mat_biolfilm_project_name': GSC_MIxS_microbial_mat_biolfilm_project_name,
		'GSC_MIxS_microbial_mat_biolfilm_experimental_factor': GSC_MIxS_microbial_mat_biolfilm_experimental_factor,
		'GSC_MIxS_microbial_mat_biolfilm_ploidy': GSC_MIxS_microbial_mat_biolfilm_ploidy,
		'GSC_MIxS_microbial_mat_biolfilm_number_of_replicons': GSC_MIxS_microbial_mat_biolfilm_number_of_replicons,
		'GSC_MIxS_microbial_mat_biolfilm_extrachromosomal_elements': GSC_MIxS_microbial_mat_biolfilm_extrachromosomal_elements,
		'GSC_MIxS_microbial_mat_biolfilm_estimated_size': GSC_MIxS_microbial_mat_biolfilm_estimated_size,
		'GSC_MIxS_microbial_mat_biolfilm_reference_for_biomaterial': GSC_MIxS_microbial_mat_biolfilm_reference_for_biomaterial,
		'GSC_MIxS_microbial_mat_biolfilm_annotation_source': GSC_MIxS_microbial_mat_biolfilm_annotation_source,
		'GSC_MIxS_microbial_mat_biolfilm_sample_volume_or_weight_for_DNA_extraction': GSC_MIxS_microbial_mat_biolfilm_sample_volume_or_weight_for_DNA_extraction,
		'GSC_MIxS_microbial_mat_biolfilm_nucleic_acid_extraction': GSC_MIxS_microbial_mat_biolfilm_nucleic_acid_extraction,
		'GSC_MIxS_microbial_mat_biolfilm_nucleic_acid_amplification': GSC_MIxS_microbial_mat_biolfilm_nucleic_acid_amplification,
		'GSC_MIxS_microbial_mat_biolfilm_library_size': GSC_MIxS_microbial_mat_biolfilm_library_size,
		'GSC_MIxS_microbial_mat_biolfilm_library_reads_sequenced': GSC_MIxS_microbial_mat_biolfilm_library_reads_sequenced,
		'GSC_MIxS_microbial_mat_biolfilm_library_construction_method': GSC_MIxS_microbial_mat_biolfilm_library_construction_method,
		'GSC_MIxS_microbial_mat_biolfilm_library_vector': GSC_MIxS_microbial_mat_biolfilm_library_vector,
		'GSC_MIxS_microbial_mat_biolfilm_library_screening_strategy': GSC_MIxS_microbial_mat_biolfilm_library_screening_strategy,
		'GSC_MIxS_microbial_mat_biolfilm_target_gene': GSC_MIxS_microbial_mat_biolfilm_target_gene,
		'GSC_MIxS_microbial_mat_biolfilm_target_subfragment': GSC_MIxS_microbial_mat_biolfilm_target_subfragment,
		'GSC_MIxS_microbial_mat_biolfilm_pcr_primers': GSC_MIxS_microbial_mat_biolfilm_pcr_primers,
		'GSC_MIxS_microbial_mat_biolfilm_multiplex_identifiers': GSC_MIxS_microbial_mat_biolfilm_multiplex_identifiers,
		'GSC_MIxS_microbial_mat_biolfilm_adapters': GSC_MIxS_microbial_mat_biolfilm_adapters,
		'GSC_MIxS_microbial_mat_biolfilm_pcr_conditions': GSC_MIxS_microbial_mat_biolfilm_pcr_conditions,
		'GSC_MIxS_microbial_mat_biolfilm_sequencing_method': GSC_MIxS_microbial_mat_biolfilm_sequencing_method,
		'GSC_MIxS_microbial_mat_biolfilm_sequence_quality_check': GSC_MIxS_microbial_mat_biolfilm_sequence_quality_check,
		'GSC_MIxS_microbial_mat_biolfilm_chimera_check_software': GSC_MIxS_microbial_mat_biolfilm_chimera_check_software,
		'GSC_MIxS_microbial_mat_biolfilm_relevant_electronic_resources': GSC_MIxS_microbial_mat_biolfilm_relevant_electronic_resources,
		'GSC_MIxS_microbial_mat_biolfilm_relevant_standard_operating_procedures': GSC_MIxS_microbial_mat_biolfilm_relevant_standard_operating_procedures,
		'GSC_MIxS_microbial_mat_biolfilm_negative_control_type': GSC_MIxS_microbial_mat_biolfilm_negative_control_type,
		'GSC_MIxS_microbial_mat_biolfilm_positive_control_type': GSC_MIxS_microbial_mat_biolfilm_positive_control_type,
		'GSC_MIxS_microbial_mat_biolfilm_collection_date': GSC_MIxS_microbial_mat_biolfilm_collection_date,
		'GSC_MIxS_microbial_mat_biolfilm_altitude': GSC_MIxS_microbial_mat_biolfilm_altitude,
		'GSC_MIxS_microbial_mat_biolfilm_geographic_location_country_and_or_sea': GSC_MIxS_microbial_mat_biolfilm_geographic_location_country_and_or_sea,
		'GSC_MIxS_microbial_mat_biolfilm_geographic_location_latitude': GSC_MIxS_microbial_mat_biolfilm_geographic_location_latitude,
		'GSC_MIxS_microbial_mat_biolfilm_geographic_location_longitude': GSC_MIxS_microbial_mat_biolfilm_geographic_location_longitude,
		'GSC_MIxS_microbial_mat_biolfilm_geographic_location_region_and_locality': GSC_MIxS_microbial_mat_biolfilm_geographic_location_region_and_locality,
		'GSC_MIxS_microbial_mat_biolfilm_depth': GSC_MIxS_microbial_mat_biolfilm_depth,
		'GSC_MIxS_microbial_mat_biolfilm_broad_scale_environmental_context': GSC_MIxS_microbial_mat_biolfilm_broad_scale_environmental_context,
		'GSC_MIxS_microbial_mat_biolfilm_local_environmental_context': GSC_MIxS_microbial_mat_biolfilm_local_environmental_context,
		'GSC_MIxS_microbial_mat_biolfilm_environmental_medium': GSC_MIxS_microbial_mat_biolfilm_environmental_medium,
		'GSC_MIxS_microbial_mat_biolfilm_elevation': GSC_MIxS_microbial_mat_biolfilm_elevation,
		'GSC_MIxS_microbial_mat_biolfilm_source_material_identifiers': GSC_MIxS_microbial_mat_biolfilm_source_material_identifiers,
		'GSC_MIxS_microbial_mat_biolfilm_sample_material_processing': GSC_MIxS_microbial_mat_biolfilm_sample_material_processing,
		'GSC_MIxS_microbial_mat_biolfilm_isolation_and_growth_condition': GSC_MIxS_microbial_mat_biolfilm_isolation_and_growth_condition,
		'GSC_MIxS_microbial_mat_biolfilm_propagation': GSC_MIxS_microbial_mat_biolfilm_propagation,
		'GSC_MIxS_microbial_mat_biolfilm_amount_or_size_of_sample_collected': GSC_MIxS_microbial_mat_biolfilm_amount_or_size_of_sample_collected,
		'GSC_MIxS_microbial_mat_biolfilm_biomass': GSC_MIxS_microbial_mat_biolfilm_biomass,
		'GSC_MIxS_microbial_mat_biolfilm_oxygenation_status_of_sample': GSC_MIxS_microbial_mat_biolfilm_oxygenation_status_of_sample,
		'GSC_MIxS_microbial_mat_biolfilm_organism_count': GSC_MIxS_microbial_mat_biolfilm_organism_count,
		'GSC_MIxS_microbial_mat_biolfilm_sample_storage_duration': GSC_MIxS_microbial_mat_biolfilm_sample_storage_duration,
		'GSC_MIxS_microbial_mat_biolfilm_sample_storage_temperature': GSC_MIxS_microbial_mat_biolfilm_sample_storage_temperature,
		'GSC_MIxS_microbial_mat_biolfilm_sample_storage_location': GSC_MIxS_microbial_mat_biolfilm_sample_storage_location,
		'GSC_MIxS_microbial_mat_biolfilm_sample_collection_device': GSC_MIxS_microbial_mat_biolfilm_sample_collection_device,
		'GSC_MIxS_microbial_mat_biolfilm_sample_collection_method': GSC_MIxS_microbial_mat_biolfilm_sample_collection_method,
		'GSC_MIxS_microbial_mat_biolfilm_host_disease_status': GSC_MIxS_microbial_mat_biolfilm_host_disease_status,
		'GSC_MIxS_microbial_mat_biolfilm_host_scientific_name': GSC_MIxS_microbial_mat_biolfilm_host_scientific_name,
		'GSC_MIxS_microbial_mat_biolfilm_alkalinity': GSC_MIxS_microbial_mat_biolfilm_alkalinity,
		'GSC_MIxS_microbial_mat_biolfilm_mean_friction_velocity': GSC_MIxS_microbial_mat_biolfilm_mean_friction_velocity,
		'GSC_MIxS_microbial_mat_biolfilm_mean_peak_friction_velocity': GSC_MIxS_microbial_mat_biolfilm_mean_peak_friction_velocity,
		'GSC_MIxS_microbial_mat_biolfilm_pressure': GSC_MIxS_microbial_mat_biolfilm_pressure,
		'GSC_MIxS_microbial_mat_biolfilm_temperature': GSC_MIxS_microbial_mat_biolfilm_temperature,
		'GSC_MIxS_microbial_mat_biolfilm_turbidity': GSC_MIxS_microbial_mat_biolfilm_turbidity,
		'GSC_MIxS_microbial_mat_biolfilm_pH': GSC_MIxS_microbial_mat_biolfilm_pH,
		'GSC_MIxS_microbial_mat_biolfilm_alkyl_diethers': GSC_MIxS_microbial_mat_biolfilm_alkyl_diethers,
		'GSC_MIxS_microbial_mat_biolfilm_aminopeptidase_activity': GSC_MIxS_microbial_mat_biolfilm_aminopeptidase_activity,
		'GSC_MIxS_microbial_mat_biolfilm_ammonium': GSC_MIxS_microbial_mat_biolfilm_ammonium,
		'GSC_MIxS_microbial_mat_biolfilm_bacterial_carbon_production': GSC_MIxS_microbial_mat_biolfilm_bacterial_carbon_production,
		'GSC_MIxS_microbial_mat_biolfilm_bishomohopanol': GSC_MIxS_microbial_mat_biolfilm_bishomohopanol,
		'GSC_MIxS_microbial_mat_biolfilm_bromide': GSC_MIxS_microbial_mat_biolfilm_bromide,
		'GSC_MIxS_microbial_mat_biolfilm_calcium': GSC_MIxS_microbial_mat_biolfilm_calcium,
		'GSC_MIxS_microbial_mat_biolfilm_carbon_nitrogen_ratio': GSC_MIxS_microbial_mat_biolfilm_carbon_nitrogen_ratio,
		'GSC_MIxS_microbial_mat_biolfilm_chloride': GSC_MIxS_microbial_mat_biolfilm_chloride,
		'GSC_MIxS_microbial_mat_biolfilm_chlorophyll': GSC_MIxS_microbial_mat_biolfilm_chlorophyll,
		'GSC_MIxS_microbial_mat_biolfilm_diether_lipids': GSC_MIxS_microbial_mat_biolfilm_diether_lipids,
		'GSC_MIxS_microbial_mat_biolfilm_dissolved_carbon_dioxide': GSC_MIxS_microbial_mat_biolfilm_dissolved_carbon_dioxide,
		'GSC_MIxS_microbial_mat_biolfilm_dissolved_hydrogen': GSC_MIxS_microbial_mat_biolfilm_dissolved_hydrogen,
		'GSC_MIxS_microbial_mat_biolfilm_dissolved_inorganic_carbon': GSC_MIxS_microbial_mat_biolfilm_dissolved_inorganic_carbon,
		'GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_carbon': GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_carbon,
		'GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_nitrogen': GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_nitrogen,
		'GSC_MIxS_microbial_mat_biolfilm_methane': GSC_MIxS_microbial_mat_biolfilm_methane,
		'GSC_MIxS_microbial_mat_biolfilm_dissolved_oxygen': GSC_MIxS_microbial_mat_biolfilm_dissolved_oxygen,
		'GSC_MIxS_microbial_mat_biolfilm_glucosidase_activity': GSC_MIxS_microbial_mat_biolfilm_glucosidase_activity,
		'GSC_MIxS_microbial_mat_biolfilm_magnesium': GSC_MIxS_microbial_mat_biolfilm_magnesium,
		'GSC_MIxS_microbial_mat_biolfilm_n_alkanes': GSC_MIxS_microbial_mat_biolfilm_n_alkanes,
		'GSC_MIxS_microbial_mat_biolfilm_nitrate': GSC_MIxS_microbial_mat_biolfilm_nitrate,
		'GSC_MIxS_microbial_mat_biolfilm_nitrite': GSC_MIxS_microbial_mat_biolfilm_nitrite,
		'GSC_MIxS_microbial_mat_biolfilm_nitrogen': GSC_MIxS_microbial_mat_biolfilm_nitrogen,
		'GSC_MIxS_microbial_mat_biolfilm_organic_carbon': GSC_MIxS_microbial_mat_biolfilm_organic_carbon,
		'GSC_MIxS_microbial_mat_biolfilm_organic_matter': GSC_MIxS_microbial_mat_biolfilm_organic_matter,
		'GSC_MIxS_microbial_mat_biolfilm_organic_nitrogen': GSC_MIxS_microbial_mat_biolfilm_organic_nitrogen,
		'GSC_MIxS_microbial_mat_biolfilm_particulate_organic_carbon': GSC_MIxS_microbial_mat_biolfilm_particulate_organic_carbon,
		'GSC_MIxS_microbial_mat_biolfilm_petroleum_hydrocarbon': GSC_MIxS_microbial_mat_biolfilm_petroleum_hydrocarbon,
		'GSC_MIxS_microbial_mat_biolfilm_phaeopigments': GSC_MIxS_microbial_mat_biolfilm_phaeopigments,
		'GSC_MIxS_microbial_mat_biolfilm_phosphate': GSC_MIxS_microbial_mat_biolfilm_phosphate,
		'GSC_MIxS_microbial_mat_biolfilm_phospholipid_fatty_acid': GSC_MIxS_microbial_mat_biolfilm_phospholipid_fatty_acid,
		'GSC_MIxS_microbial_mat_biolfilm_potassium': GSC_MIxS_microbial_mat_biolfilm_potassium,
		'GSC_MIxS_microbial_mat_biolfilm_redox_potential': GSC_MIxS_microbial_mat_biolfilm_redox_potential,
		'GSC_MIxS_microbial_mat_biolfilm_salinity': GSC_MIxS_microbial_mat_biolfilm_salinity,
		'GSC_MIxS_microbial_mat_biolfilm_total_carbon': GSC_MIxS_microbial_mat_biolfilm_total_carbon,
		'GSC_MIxS_microbial_mat_biolfilm_silicate': GSC_MIxS_microbial_mat_biolfilm_silicate,
		'GSC_MIxS_microbial_mat_biolfilm_sodium': GSC_MIxS_microbial_mat_biolfilm_sodium,
		'GSC_MIxS_microbial_mat_biolfilm_total_organic_carbon': GSC_MIxS_microbial_mat_biolfilm_total_organic_carbon,
		'GSC_MIxS_microbial_mat_biolfilm_water_content': GSC_MIxS_microbial_mat_biolfilm_water_content,
		'GSC_MIxS_microbial_mat_biolfilm_sulfate': GSC_MIxS_microbial_mat_biolfilm_sulfate,
		'GSC_MIxS_microbial_mat_biolfilm_sulfide': GSC_MIxS_microbial_mat_biolfilm_sulfide,
		'GSC_MIxS_microbial_mat_biolfilm_total_nitrogen': GSC_MIxS_microbial_mat_biolfilm_total_nitrogen,
		'GSC_MIxS_microbial_mat_biolfilm_subspecific_genetic_lineage': GSC_MIxS_microbial_mat_biolfilm_subspecific_genetic_lineage,
		'GSC_MIxS_microbial_mat_biolfilm_trophic_level': GSC_MIxS_microbial_mat_biolfilm_trophic_level,
		'GSC_MIxS_microbial_mat_biolfilm_relationship_to_oxygen': GSC_MIxS_microbial_mat_biolfilm_relationship_to_oxygen,
		'GSC_MIxS_microbial_mat_biolfilm_known_pathogenicity': GSC_MIxS_microbial_mat_biolfilm_known_pathogenicity,
		'GSC_MIxS_microbial_mat_biolfilm_encoded_traits': GSC_MIxS_microbial_mat_biolfilm_encoded_traits,
		'GSC_MIxS_microbial_mat_biolfilm_observed_biotic_relationship': GSC_MIxS_microbial_mat_biolfilm_observed_biotic_relationship,
		'GSC_MIxS_microbial_mat_biolfilm_chemical_administration': GSC_MIxS_microbial_mat_biolfilm_chemical_administration,
		'GSC_MIxS_microbial_mat_biolfilm_perturbation': GSC_MIxS_microbial_mat_biolfilm_perturbation,
	}

class GSC_MIxS_microbial_mat_biolfilm_unit(SelfDescribingModel):

	GSC_MIxS_microbial_mat_biolfilm_sample_volume_or_weight_for_DNA_extraction_units = [('g', 'g'), ('mL', 'mL'), ('mg', 'mg'), ('ng', 'ng')]
	GSC_MIxS_microbial_mat_biolfilm_altitude_units = [('m', 'm')]
	GSC_MIxS_microbial_mat_biolfilm_geographic_location_latitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_microbial_mat_biolfilm_geographic_location_longitude_units = [('D', 'D'), ('D', 'D')]
	GSC_MIxS_microbial_mat_biolfilm_depth_units = [('m', 'm')]
	GSC_MIxS_microbial_mat_biolfilm_elevation_units = [('m', 'm')]
	GSC_MIxS_microbial_mat_biolfilm_amount_or_size_of_sample_collected_units = [('L', 'L'), ('g', 'g'), ('kg', 'kg'), ('m2', 'm2'), ('m3', 'm3')]
	GSC_MIxS_microbial_mat_biolfilm_biomass_units = [('g', 'g'), ('kg', 'kg'), ('t', 't')]
	GSC_MIxS_microbial_mat_biolfilm_sample_storage_duration_units = [('days', 'days'), ('hours', 'hours'), ('months', 'months'), ('weeks', 'weeks'), ('years', 'years')]
	GSC_MIxS_microbial_mat_biolfilm_sample_storage_temperature_units = [('°', '°'), ('C', 'C')]
	GSC_MIxS_microbial_mat_biolfilm_alkalinity_units = [('m', 'm'), ('E', 'E'), ('q', 'q'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_mean_friction_velocity_units = [('m', 'm'), ('/', '/'), ('s', 's')]
	GSC_MIxS_microbial_mat_biolfilm_mean_peak_friction_velocity_units = [('m', 'm'), ('/', '/'), ('s', 's')]
	GSC_MIxS_microbial_mat_biolfilm_pressure_units = [('atm', 'atm'), ('bar', 'bar')]
	GSC_MIxS_microbial_mat_biolfilm_temperature_units = [('º', 'º'), ('C', 'C')]
	GSC_MIxS_microbial_mat_biolfilm_turbidity_units = [('FTU', 'FTU'), ('NTU', 'NTU')]
	GSC_MIxS_microbial_mat_biolfilm_alkyl_diethers_units = [('M/L', 'M/L'), ('µg/L', 'µg/L')]
	GSC_MIxS_microbial_mat_biolfilm_aminopeptidase_activity_units = [('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L'), ('/', '/'), ('h', 'h')]
	GSC_MIxS_microbial_mat_biolfilm_ammonium_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_bacterial_carbon_production_units = [('n', 'n'), ('g', 'g'), ('/', '/'), ('h', 'h')]
	GSC_MIxS_microbial_mat_biolfilm_bishomohopanol_units = [('µg/L', 'µg/L'), ('µg/g', 'µg/g')]
	GSC_MIxS_microbial_mat_biolfilm_bromide_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_microbial_mat_biolfilm_calcium_units = [('mg/L', 'mg/L'), ('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_microbial_mat_biolfilm_chloride_units = [('m', 'm'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_chlorophyll_units = [('mg/m3', 'mg/m3'), ('µg/L', 'µg/L')]
	GSC_MIxS_microbial_mat_biolfilm_diether_lipids_units = [('n', 'n'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_dissolved_carbon_dioxide_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_dissolved_hydrogen_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_dissolved_inorganic_carbon_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_carbon_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_nitrogen_units = [('mg/L', 'mg/L'), ('µg/L', 'µg/L')]
	GSC_MIxS_microbial_mat_biolfilm_methane_units = [('µ', 'µ'), ('M', 'M'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_dissolved_oxygen_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('k', 'k'), ('g', 'g')]
	GSC_MIxS_microbial_mat_biolfilm_glucosidase_activity_units = [('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L'), ('/', '/'), ('h', 'h')]
	GSC_MIxS_microbial_mat_biolfilm_magnesium_units = [('mg/L', 'mg/L'), ('mol/L', 'mol/L'), ('parts/million', 'parts/million')]
	GSC_MIxS_microbial_mat_biolfilm_n_alkanes_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_nitrate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_nitrite_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_nitrogen_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_organic_carbon_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_organic_matter_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_organic_nitrogen_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_particulate_organic_carbon_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_petroleum_hydrocarbon_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_phaeopigments_units = [('mg/m3', 'mg/m3'), ('µg/L', 'µg/L')]
	GSC_MIxS_microbial_mat_biolfilm_phosphate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_phospholipid_fatty_acid_units = [('mol/L', 'mol/L'), ('mol/g', 'mol/g')]
	GSC_MIxS_microbial_mat_biolfilm_potassium_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_microbial_mat_biolfilm_redox_potential_units = [('m', 'm'), ('V', 'V')]
	GSC_MIxS_microbial_mat_biolfilm_salinity_units = [('p', 'p'), ('s', 's'), ('u', 'u')]
	GSC_MIxS_microbial_mat_biolfilm_total_carbon_units = [('µ', 'µ'), ('g', 'g'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_silicate_units = [('µ', 'µ'), ('m', 'm'), ('o', 'o'), ('l', 'l'), ('/', '/'), ('L', 'L')]
	GSC_MIxS_microbial_mat_biolfilm_sodium_units = [('parts/million', 'parts/million'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_microbial_mat_biolfilm_total_organic_carbon_units = [('g', 'g'), ('/', '/'), ('k', 'k'), ('g', 'g')]
	GSC_MIxS_microbial_mat_biolfilm_water_content_units = [('cm3/cm3', 'cm3/cm3'), ('g/g', 'g/g')]
	GSC_MIxS_microbial_mat_biolfilm_sulfate_units = [('mg/L', 'mg/L'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_microbial_mat_biolfilm_sulfide_units = [('mg/L', 'mg/L'), ('µmol/L', 'µmol/L')]
	GSC_MIxS_microbial_mat_biolfilm_total_nitrogen_units = [('µg/L', 'µg/L'), ('µmol/L', 'µmol/L')]

	fields = {
		'GSC_MIxS_microbial_mat_biolfilm_sample_volume_or_weight_for_DNA_extraction_units': GSC_MIxS_microbial_mat_biolfilm_sample_volume_or_weight_for_DNA_extraction_units,
		'GSC_MIxS_microbial_mat_biolfilm_altitude_units': GSC_MIxS_microbial_mat_biolfilm_altitude_units,
		'GSC_MIxS_microbial_mat_biolfilm_geographic_location_latitude_units': GSC_MIxS_microbial_mat_biolfilm_geographic_location_latitude_units,
		'GSC_MIxS_microbial_mat_biolfilm_geographic_location_longitude_units': GSC_MIxS_microbial_mat_biolfilm_geographic_location_longitude_units,
		'GSC_MIxS_microbial_mat_biolfilm_depth_units': GSC_MIxS_microbial_mat_biolfilm_depth_units,
		'GSC_MIxS_microbial_mat_biolfilm_elevation_units': GSC_MIxS_microbial_mat_biolfilm_elevation_units,
		'GSC_MIxS_microbial_mat_biolfilm_amount_or_size_of_sample_collected_units': GSC_MIxS_microbial_mat_biolfilm_amount_or_size_of_sample_collected_units,
		'GSC_MIxS_microbial_mat_biolfilm_biomass_units': GSC_MIxS_microbial_mat_biolfilm_biomass_units,
		'GSC_MIxS_microbial_mat_biolfilm_sample_storage_duration_units': GSC_MIxS_microbial_mat_biolfilm_sample_storage_duration_units,
		'GSC_MIxS_microbial_mat_biolfilm_sample_storage_temperature_units': GSC_MIxS_microbial_mat_biolfilm_sample_storage_temperature_units,
		'GSC_MIxS_microbial_mat_biolfilm_alkalinity_units': GSC_MIxS_microbial_mat_biolfilm_alkalinity_units,
		'GSC_MIxS_microbial_mat_biolfilm_mean_friction_velocity_units': GSC_MIxS_microbial_mat_biolfilm_mean_friction_velocity_units,
		'GSC_MIxS_microbial_mat_biolfilm_mean_peak_friction_velocity_units': GSC_MIxS_microbial_mat_biolfilm_mean_peak_friction_velocity_units,
		'GSC_MIxS_microbial_mat_biolfilm_pressure_units': GSC_MIxS_microbial_mat_biolfilm_pressure_units,
		'GSC_MIxS_microbial_mat_biolfilm_temperature_units': GSC_MIxS_microbial_mat_biolfilm_temperature_units,
		'GSC_MIxS_microbial_mat_biolfilm_turbidity_units': GSC_MIxS_microbial_mat_biolfilm_turbidity_units,
		'GSC_MIxS_microbial_mat_biolfilm_alkyl_diethers_units': GSC_MIxS_microbial_mat_biolfilm_alkyl_diethers_units,
		'GSC_MIxS_microbial_mat_biolfilm_aminopeptidase_activity_units': GSC_MIxS_microbial_mat_biolfilm_aminopeptidase_activity_units,
		'GSC_MIxS_microbial_mat_biolfilm_ammonium_units': GSC_MIxS_microbial_mat_biolfilm_ammonium_units,
		'GSC_MIxS_microbial_mat_biolfilm_bacterial_carbon_production_units': GSC_MIxS_microbial_mat_biolfilm_bacterial_carbon_production_units,
		'GSC_MIxS_microbial_mat_biolfilm_bishomohopanol_units': GSC_MIxS_microbial_mat_biolfilm_bishomohopanol_units,
		'GSC_MIxS_microbial_mat_biolfilm_bromide_units': GSC_MIxS_microbial_mat_biolfilm_bromide_units,
		'GSC_MIxS_microbial_mat_biolfilm_calcium_units': GSC_MIxS_microbial_mat_biolfilm_calcium_units,
		'GSC_MIxS_microbial_mat_biolfilm_chloride_units': GSC_MIxS_microbial_mat_biolfilm_chloride_units,
		'GSC_MIxS_microbial_mat_biolfilm_chlorophyll_units': GSC_MIxS_microbial_mat_biolfilm_chlorophyll_units,
		'GSC_MIxS_microbial_mat_biolfilm_diether_lipids_units': GSC_MIxS_microbial_mat_biolfilm_diether_lipids_units,
		'GSC_MIxS_microbial_mat_biolfilm_dissolved_carbon_dioxide_units': GSC_MIxS_microbial_mat_biolfilm_dissolved_carbon_dioxide_units,
		'GSC_MIxS_microbial_mat_biolfilm_dissolved_hydrogen_units': GSC_MIxS_microbial_mat_biolfilm_dissolved_hydrogen_units,
		'GSC_MIxS_microbial_mat_biolfilm_dissolved_inorganic_carbon_units': GSC_MIxS_microbial_mat_biolfilm_dissolved_inorganic_carbon_units,
		'GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_carbon_units': GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_carbon_units,
		'GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_nitrogen_units': GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_nitrogen_units,
		'GSC_MIxS_microbial_mat_biolfilm_methane_units': GSC_MIxS_microbial_mat_biolfilm_methane_units,
		'GSC_MIxS_microbial_mat_biolfilm_dissolved_oxygen_units': GSC_MIxS_microbial_mat_biolfilm_dissolved_oxygen_units,
		'GSC_MIxS_microbial_mat_biolfilm_glucosidase_activity_units': GSC_MIxS_microbial_mat_biolfilm_glucosidase_activity_units,
		'GSC_MIxS_microbial_mat_biolfilm_magnesium_units': GSC_MIxS_microbial_mat_biolfilm_magnesium_units,
		'GSC_MIxS_microbial_mat_biolfilm_n_alkanes_units': GSC_MIxS_microbial_mat_biolfilm_n_alkanes_units,
		'GSC_MIxS_microbial_mat_biolfilm_nitrate_units': GSC_MIxS_microbial_mat_biolfilm_nitrate_units,
		'GSC_MIxS_microbial_mat_biolfilm_nitrite_units': GSC_MIxS_microbial_mat_biolfilm_nitrite_units,
		'GSC_MIxS_microbial_mat_biolfilm_nitrogen_units': GSC_MIxS_microbial_mat_biolfilm_nitrogen_units,
		'GSC_MIxS_microbial_mat_biolfilm_organic_carbon_units': GSC_MIxS_microbial_mat_biolfilm_organic_carbon_units,
		'GSC_MIxS_microbial_mat_biolfilm_organic_matter_units': GSC_MIxS_microbial_mat_biolfilm_organic_matter_units,
		'GSC_MIxS_microbial_mat_biolfilm_organic_nitrogen_units': GSC_MIxS_microbial_mat_biolfilm_organic_nitrogen_units,
		'GSC_MIxS_microbial_mat_biolfilm_particulate_organic_carbon_units': GSC_MIxS_microbial_mat_biolfilm_particulate_organic_carbon_units,
		'GSC_MIxS_microbial_mat_biolfilm_petroleum_hydrocarbon_units': GSC_MIxS_microbial_mat_biolfilm_petroleum_hydrocarbon_units,
		'GSC_MIxS_microbial_mat_biolfilm_phaeopigments_units': GSC_MIxS_microbial_mat_biolfilm_phaeopigments_units,
		'GSC_MIxS_microbial_mat_biolfilm_phosphate_units': GSC_MIxS_microbial_mat_biolfilm_phosphate_units,
		'GSC_MIxS_microbial_mat_biolfilm_phospholipid_fatty_acid_units': GSC_MIxS_microbial_mat_biolfilm_phospholipid_fatty_acid_units,
		'GSC_MIxS_microbial_mat_biolfilm_potassium_units': GSC_MIxS_microbial_mat_biolfilm_potassium_units,
		'GSC_MIxS_microbial_mat_biolfilm_redox_potential_units': GSC_MIxS_microbial_mat_biolfilm_redox_potential_units,
		'GSC_MIxS_microbial_mat_biolfilm_salinity_units': GSC_MIxS_microbial_mat_biolfilm_salinity_units,
		'GSC_MIxS_microbial_mat_biolfilm_total_carbon_units': GSC_MIxS_microbial_mat_biolfilm_total_carbon_units,
		'GSC_MIxS_microbial_mat_biolfilm_silicate_units': GSC_MIxS_microbial_mat_biolfilm_silicate_units,
		'GSC_MIxS_microbial_mat_biolfilm_sodium_units': GSC_MIxS_microbial_mat_biolfilm_sodium_units,
		'GSC_MIxS_microbial_mat_biolfilm_total_organic_carbon_units': GSC_MIxS_microbial_mat_biolfilm_total_organic_carbon_units,
		'GSC_MIxS_microbial_mat_biolfilm_water_content_units': GSC_MIxS_microbial_mat_biolfilm_water_content_units,
		'GSC_MIxS_microbial_mat_biolfilm_sulfate_units': GSC_MIxS_microbial_mat_biolfilm_sulfate_units,
		'GSC_MIxS_microbial_mat_biolfilm_sulfide_units': GSC_MIxS_microbial_mat_biolfilm_sulfide_units,
		'GSC_MIxS_microbial_mat_biolfilm_total_nitrogen_units': GSC_MIxS_microbial_mat_biolfilm_total_nitrogen_units,
	}

	sample = models.ForeignKey(Sample, on_delete=models.CASCADE)
	GSC_MIxS_microbial_mat_biolfilm_sample_volume_or_weight_for_DNA_extraction = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_sample_volume_or_weight_for_DNA_extraction_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_altitude = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_altitude_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_geographic_location_latitude = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_geographic_location_latitude_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_geographic_location_longitude = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_geographic_location_longitude_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_depth = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_depth_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_elevation = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_elevation_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_amount_or_size_of_sample_collected = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_amount_or_size_of_sample_collected_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_biomass = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_biomass_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_sample_storage_duration = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_sample_storage_duration_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_sample_storage_temperature = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_sample_storage_temperature_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_alkalinity = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_alkalinity_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_mean_friction_velocity = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_mean_friction_velocity_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_mean_peak_friction_velocity = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_mean_peak_friction_velocity_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_pressure = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_pressure_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_temperature = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_temperature_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_turbidity = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_turbidity_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_alkyl_diethers = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_alkyl_diethers_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_aminopeptidase_activity = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_aminopeptidase_activity_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_ammonium = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_ammonium_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_bacterial_carbon_production = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_bacterial_carbon_production_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_bishomohopanol = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_bishomohopanol_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_bromide = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_bromide_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_calcium = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_calcium_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_chloride = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_chloride_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_chlorophyll = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_chlorophyll_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_diether_lipids = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_diether_lipids_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_dissolved_carbon_dioxide = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_dissolved_carbon_dioxide_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_dissolved_hydrogen = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_dissolved_hydrogen_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_dissolved_inorganic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_dissolved_inorganic_carbon_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_carbon_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_dissolved_organic_nitrogen_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_methane = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_methane_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_dissolved_oxygen = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_dissolved_oxygen_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_glucosidase_activity = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_glucosidase_activity_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_magnesium = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_magnesium_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_n_alkanes = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_n_alkanes_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_nitrate = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_nitrate_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_nitrite = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_nitrite_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_nitrogen_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_organic_carbon_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_organic_matter = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_organic_matter_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_organic_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_organic_nitrogen_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_particulate_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_particulate_organic_carbon_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_petroleum_hydrocarbon = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_petroleum_hydrocarbon_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_phaeopigments = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_phaeopigments_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_phosphate = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_phosphate_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_phospholipid_fatty_acid = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_phospholipid_fatty_acid_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_potassium = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_potassium_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_redox_potential = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_redox_potential_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_salinity = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_salinity_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_total_carbon = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_total_carbon_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_silicate = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_silicate_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_sodium = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_sodium_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_total_organic_carbon = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_total_organic_carbon_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_water_content = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_water_content_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_sulfate = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_sulfate_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_sulfide = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_sulfide_units, blank=False)
	GSC_MIxS_microbial_mat_biolfilm_total_nitrogen = models.CharField(max_length=100, choices=GSC_MIxS_microbial_mat_biolfilm_total_nitrogen_units, blank=False)


