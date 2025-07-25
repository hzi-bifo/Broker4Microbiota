# Generated by Django 5.2.4 on 2025-07-21 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_order_checklist_changed_sampleset_field_overrides_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='sequencing_data_path',
            field=models.CharField(blank=True, default='', help_text='Directory path where sequencing files are stored (e.g., /data/sequencing or /mnt/sequencing_data)', max_length=500),
        ),
    ]
