# Generated manually to add missing fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_alter_ena_binned_metagenome_assembly_quality_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='ena_binned_metagenome',
            name='sample_collection_method',
            field=models.CharField(blank=True, help_text='The method', max_length=120, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='gsc_mimags',
            name='sample_collection_device',
            field=models.CharField(blank=True, help_text='The method', max_length=120, default=''),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='gsc_mimags',
            name='sample_collection_method',
            field=models.CharField(blank=True, help_text='The method', max_length=120, default=''),
            preserve_default=False,
        ),
    ]