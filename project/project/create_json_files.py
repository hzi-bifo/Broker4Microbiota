import os
import json
import xmltodict
import pdb

# Path to the directory containing the XML files
xml_dir = '/home/gary/git/django_ngs_metadata_collection/project/static/xml'

# Path to the directory where the JSON files will be saved
json_dir = '/home/gary/git/django_ngs_metadata_collection/project/static/json'

jqtree_path = os.path.join(json_dir, 'jqtree.json')

# Create the JSON directory if it doesn't exist
os.makedirs(json_dir, exist_ok=True)

pdb.set_trace()

jqtree_data = []


# Iterate over each XML file in the XML directory
for filename in os.listdir(xml_dir):
    if filename.endswith('.xml'):
        xml_path = os.path.join(xml_dir, filename)
        json_path = os.path.join(json_dir, filename.replace('.xml', '.json'))

        # Load the contents of the XML file
        with open(xml_path, 'r') as xml_file:
            xml_contents = xml_file.read()

        data = xmltodict.parse(xml_contents, force_list={'FIELD'})

        checklist = data['CHECKLIST_SET']['CHECKLIST']['DESCRIPTOR']
        checklist_name = checklist['NAME']
        jqtree_checklist = {}
        jqtree_checklist['name'] = checklist_name
        jqtree_checklist['children'] = []
        for fieldgroup in checklist['FIELD_GROUP']:
            fieldgroup_name = fieldgroup['NAME']
            jqtree_fieldgroup = {}
            jqtree_fieldgroup['name'] = fieldgroup_name
            jqtree_fieldgroup['children'] = []
            for field in fieldgroup['FIELD']:
                field_name = field['NAME']
                field_description = field['DESCRIPTION']
                jqtree_field = {}
                jqtree_field['name'] = field_name
                jqtree_fieldgroup['children'].append(jqtree_field)
                print(f'{checklist_name}: {fieldgroup_name}: {field_name}')
            jqtree_checklist['children'].append(jqtree_fieldgroup)
        jqtree_data.append(jqtree_checklist)

        with open(jqtree_path, 'w') as jqtree_file:
            json.dump(jqtree_data, jqtree_file, indent=4)

        # Show description in seperate panel
        # search
        # drag to outside field

        # Save the data as JSON
        with open(json_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)