# Generated by Django 5.2.4 on 2025-07-21 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0006_remove_sitesettings_sequencing_data_path_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='sequencing_data_path',
            field=models.CharField(blank=True, default='', help_text='Directory path where sequencing files are stored (e.g., /data/sequencing or /mnt/sequencing_data)', max_length=500),
        ),
    ]
