import os
import json
import xmltodict
import pdb
import sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from django.conf import settings
import re

def get_next_node_id():
    global node_id
    node_id += 1
    return node_id

# Build up the jqtree data structure
def produceJqTree(data, jqtree_data): 
    checklist = data['CHECKLIST_SET']['CHECKLIST']['DESCRIPTOR']
    checklist_name = checklist['NAME']
    jqtree_checklist = {}
    jqtree_checklist['name'] = checklist_name
    jqtree_checklist['id'] = get_next_node_id() 
    jqtree_checklist['children'] = []
    for fieldgroup in checklist['FIELD_GROUP']:
        fieldgroup_name = fieldgroup['NAME']
        jqtree_fieldgroup = {}
        jqtree_fieldgroup['name'] = fieldgroup_name
        jqtree_fieldgroup['id'] = get_next_node_id() 
        jqtree_fieldgroup['children'] = []
        for field in fieldgroup['FIELD']:
            field_name = field['NAME']
            field_description = field['DESCRIPTION']

            # get units (if existing - could be multiple) and create as a choices option
            # 

            jqtree_field = {}
            jqtree_field['name'] = field_name
            jqtree_field['description'] = field_description
            jqtree_field['id'] = get_next_node_id() 
            jqtree_fieldgroup['children'].append(jqtree_field)
        jqtree_checklist['children'].append(jqtree_fieldgroup)
    jqtree_data.append(jqtree_checklist)

# Produce checklist structure
def produce_checklist_structure(data):

    checklist_header = data['CHECKLIST_SET']['CHECKLIST']['DESCRIPTOR']
    checklist_name = checklist_header['NAME'].replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('-', '_')

    checklist_header2 = data['CHECKLIST_SET']['CHECKLIST']['IDENTIFIERS']
    checklist_code = checklist_header2['PRIMARY_ID']

    checklist_class_name = checklist_name
    unitchecklist_class_name = f"{checklist_name}_unit"

    checklist_structure = f"'{checklist_name}': {{\"checklist_code\": \"{checklist_code}\", 'checklist_class_name': '{checklist_class_name}', 'unitchecklist_class_name': '{unitchecklist_class_name}'}},\n"

    return checklist_structure


# Produce models file
def produceModels(data, model_data, global_field_names):

    checklist = data['CHECKLIST_SET']['CHECKLIST']['DESCRIPTOR']
    # Replace those characters which are not allowed in a model name (by ?)
    checklist_name = checklist['NAME'].replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('-', '_')
    model_name = checklist_name

    checklist_header = ""
    checklist_output = ""
    unitchecklist_header = ""
    unitchecklist_output = ""
    checklist_fields_output = ""
    unitchecklist_fields_output = ""
    validator_output = ""
    choice_output = ""
    unit_output = "" 
    
    # Track field names within this checklist to avoid duplicates
    local_field_names = {}

    checklist_header = checklist_header + f"class {model_name}(SelfDescribingModel):\n"
    checklist_output = checklist_output + f"\tsampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)\n"
    checklist_output = checklist_output + f"\tsample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)\n"
    checklist_output = checklist_output + f"\tsample_type = models.IntegerField(default=1)\n"

    checklist_name_output = f"\tname = '{checklist_name}'\n"

    checklist_fields_output = f"\tfields = {{\n"

    unitchecklist_fields_output = f"\tfields = {{\n"

    unitchecklist_header = unitchecklist_header + f"class {model_name}_unit(SelfDescribingModel):\n"
    unitchecklist_output = unitchecklist_output + f"\tsampleset = models.ForeignKey(Sampleset, on_delete=models.CASCADE, default=1)\n"
    unitchecklist_output = unitchecklist_output + f"\tsample = models.ForeignKey(Sample, on_delete=models.CASCADE, default=1)\n"
    unitchecklist_output = unitchecklist_output + f"\tsample_type = models.IntegerField(default=1)\n"

    unitchecklist_name_output = f"\tname = '{checklist_name}'\n"

    for fieldgroup in checklist['FIELD_GROUP']:
        fieldgroup_name = fieldgroup['NAME']
        model_fieldgroup_name = fieldgroup_name
        for field in fieldgroup['FIELD']:
            field_name = re.sub("^16S", 'sixteen_s', re.sub("^16s", 'sixteen_s', field['NAME'].replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('-', '_')))
            original_field_name = field['NAME'] # .replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace('-', '_')

            field_description = ''
            try:
                # trimmed to ten chars
                field_description = field['DESCRIPTION'][0:10]
            except:
                pass

            field_synonym = ''
            try:
                field_synonym = field['SYNONYM']
            except:
                pass

            field_units_name = ''
            try:
                if field['UNITS']:
                    field_units = []
                    for units in field['UNITS']:
                        for unit in units['UNIT']:
                            field_units.append((unit, unit))
                    field_units_name = f"{field_name}_units"
            except:
                pass

            field_type = ''
            field_validator = ''
            try:
                if field['FIELD_TYPE']['TEXT_FIELD'] is None:
                    field_type = "TEXT"
                else:
                    field_type = "TEXT"
                    if field['FIELD_TYPE']['TEXT_FIELD']['REGEX_VALUE']:
                        field_validator = field['FIELD_TYPE']['TEXT_FIELD']['REGEX_VALUE']
                        field_validator_name = f'{field_name}_validator'
            except:
                pass

            try:
                if field['FIELD_TYPE']['TEXT_AREA_FIELD'] is None:
                    field_type = "TEXT"
            except:
                pass


            try:
                if field['FIELD_TYPE']['TEXT_CHOICE_FIELD']:
                    field_type = "TEXT_CHOICES"
                    field_choices = []
                    field_choice_name = f'{field_name}_choice'
                    for choice in field['FIELD_TYPE']['TEXT_CHOICE_FIELD']['TEXT_VALUE']:
                        choice_value = choice['VALUE']
                        field_choices.append((choice_value, choice_value))
            except:
                pass         

            try:
                if field['FIELD_TYPE']['TAXON_FIELD']:
                    field_type = "TEXT"
            except:
                pass            

            if  field_type == '':
                print(f'Unknown field type: {field_name}')

            if field['MANDATORY'] == 'optional':
                field_blank = 'True'
            else:
                field_blank = 'False'

            if field['MULTIPLICITY'] != 'multiple':
                print(f"Multiplicity not multiple: {field_name}")

            # Check for duplicates globally (for informational purposes only)
            if field_name in global_field_names:
                print(f"Field name {field_name} in {model_name} also exists in checklist {global_field_names[field_name]}")
            
            # Check for duplicates within this checklist
            if field_name in local_field_names:
                print(f"WARNING: Duplicate field name {field_name} within {model_name} checklist - skipping duplicate")
            else:
                # Add to both global and local tracking
                global_field_names[field_name] = model_name
                local_field_names[field_name] = True

                # Always add the field to this checklist, regardless of global duplicates
                checklist_output = checklist_output + f"\t{field_name }= "
                if field_type == 'TEXT' or field_type == 'TEXT_CHOICES':
                    checklist_output = checklist_output + f"models.CharField(max_length=120, blank={field_blank}"
                if field_description:
                    checklist_output = checklist_output + f",help_text=\"{field_description}\""
                if field_validator:
                    checklist_output = checklist_output + f", validators=[RegexValidator({field_validator_name})]"
                    validator_output = validator_output + f"\t{field_validator_name} = \"{field_validator}\"\n"
                if field_type == 'TEXT_CHOICES':
                    checklist_output = checklist_output + f", choices={field_choice_name}"
                    choice_output = choice_output + f"\t{field_choice_name} = {field_choices}\n"
                checklist_output = checklist_output + f")\n"

                checklist_fields_output = checklist_fields_output + f"\t\t'{field_name}': '{original_field_name}',\n"

                if field_units_name:
                    unitchecklist_output = unitchecklist_output + f"\t{field_name } = models.CharField(max_length=120, choices={field_units_name}, blank=False)\n"
                    
                    unit_output = unit_output + f"\t{field_units_name} = {field_units}\n"

                    unitchecklist_fields_output = unitchecklist_fields_output + f"\t\t'{field_name}': '{original_field_name}',\n"

    checklist_fields_output = checklist_fields_output + f"\t}}\n"
    unitchecklist_fields_output = unitchecklist_fields_output + f"\t}}\n"

    model_data = f'{checklist_header}\n{choice_output}\n{validator_output}\n{checklist_output}\n{checklist_fields_output}\n{checklist_name_output}\n{unitchecklist_header}\n{unit_output}\n{unitchecklist_fields_output}\n{unitchecklist_name_output}\n{unitchecklist_output}\n'
    return model_data

# Path to the directory containing the XML files
xml_dir = f"{settings.BASE_DIR}/static/xml"

# Path to the directory where the JSON files will be saved
json_dir = f"{settings.BASE_DIR}/static/json"

models_dir = f"{settings.BASE_DIR}/app"

jqtree_path = os.path.join(json_dir, 'jqtree.json')

models_template_path = os.path.join(models_dir, 'models_template.py')
models_path = os.path.join(models_dir, 'models_generated.py')  # Changed to avoid overwriting

# Create the JSON directory if it doesn't exist
os.makedirs(json_dir, exist_ok=True)

jqtree_data = []

model_data = ""

# Track field names globally for informational purposes only
global_field_names = {}

node_id = 0

checklist_structure = ""

print("\n=== Processing XML Files ===\n")

# Iterate over each XML file in the XML directory
for filename in sorted(os.listdir(xml_dir)):
    if filename.endswith('.xml'):
        print(f"Processing: {filename}")
        xml_path = os.path.join(xml_dir, filename)
        json_path = os.path.join(json_dir, filename.replace('.xml', '.json'))

        # Load the contents of the XML file
        with open(xml_path, 'r') as xml_file:
            xml_contents = xml_file.read()

        data = xmltodict.parse(xml_contents, force_list=('FIELD','UNITS','UNIT'))

        # Save the data as JSON
        with open(json_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        produceJqTree(data, jqtree_data)

        model_data = model_data + produceModels(data, model_data, global_field_names)

        checklist_structure = checklist_structure + produce_checklist_structure(data)

with open(jqtree_path, 'w') as jqtree_file:
    json.dump(jqtree_data, jqtree_file, indent=4)


with open(models_template_path, 'r') as models_template_file:
    models_template_contents = models_template_file.readlines()

with open(models_path, 'w') as models_file:
    for line in models_template_contents:
        models_file.write(re.sub(r'%CHECKLIST_STRUCTURE%', checklist_structure, line))
    print(model_data, file = models_file)

print(f"\n=== Generation Complete ===")
print(f"Models generated in: {models_path}")
print(f"JSON files saved in: {json_dir}")
print(f"jqTree data saved to: {jqtree_path}")