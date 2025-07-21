#!/usr/bin/env python
"""
Script to make all checklist fields nullable (blank=True) to allow migrations
"""
import re

def fix_models_file():
    # Read the models.py file
    with open('app/models.py', 'r') as f:
        content = f.read()
    
    # Pattern to find blank=False in checklist models
    # This will match lines like: project_name= models.CharField(max_length=120, blank=False,help_text="Name of th")
    pattern = r'(models\.CharField\(max_length=120, )blank=False(,.*?\))'
    
    # Replace blank=False with blank=True
    content = re.sub(pattern, r'\1blank=True\2', content)
    
    # Also fix fields that might not have blank specified at all for required fields
    # This pattern matches CharField without blank parameter
    pattern2 = r'(models\.CharField\(max_length=120)(,help_text=.*?\))'
    
    def add_blank_true(match):
        # Check if blank is already in the string
        if 'blank=' not in match.group(0):
            return match.group(1) + ', blank=True' + match.group(2)
        return match.group(0)
    
    content = re.sub(pattern2, add_blank_true, content)
    
    # Fix unit model fields that have choices but no blank parameter
    # Pattern: field = models.CharField(max_length=120, choices=..., blank=False)
    pattern3 = r'(= models\.CharField\(max_length=120, choices=[^,]+), blank=False\)'
    content = re.sub(pattern3, r'\1, blank=True)', content)
    
    # Add blank=True to CharField fields with choices that don't have blank specified
    pattern4 = r'(= models\.CharField\(max_length=120, choices=[^)]+)(\))'
    
    def add_blank_to_choices(match):
        if 'blank=' not in match.group(0):
            return match.group(1) + ', blank=True' + match.group(2)
        return match.group(0)
    
    content = re.sub(pattern4, add_blank_to_choices, content)
    
    # Write the modified content back
    with open('app/models.py', 'w') as f:
        f.write(content)
    
    print("Fixed models.py - all CharField fields in checklists are now nullable (blank=True)")
    print("You can now run: python manage.py makemigrations")

if __name__ == '__main__':
    fix_models_file()