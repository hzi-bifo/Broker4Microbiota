# ngs_orders

This is a Django App for collection and storage of sequenicing orders for the sequencing facility. After registration/login the user can define orders, associate samples to a order and associate samples to  MIxS Sample Checklists.

# Installation

Start the application

```
python manage.py runserver
```

# Configuration 

## Changes on the Order form

The Order form can be changed by modifying the class OrderForm in `myapp/forms.py` and the `models.py`file that defines the SQL fields. Updates on the SQL tables requires migration of the table layout.

```
python manage.py makemigrations
python manage.py migrate
```

## Configuration of MIxS Sample Checklists

The application comes with 14 MIxS Sample Checklists that are downloaded from https://www.ebi.ac.uk/ena/browser/checklists. These are stored and can be changed and updated under `staticfiles/xml/EnviornmentID.xml`. These IDs should match `MIXS_METADATA_STANDARDS` defined in `mixs_metadata_standards.py`. After the .xml files are changed, run `python manage.py collectstatic` to update the static files. 

