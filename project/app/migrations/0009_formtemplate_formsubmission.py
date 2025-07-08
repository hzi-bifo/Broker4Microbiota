# Generated manually for dynamic form system

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('app', '0008_sitesettings_submission_instructions'),
    ]

    operations = [
        migrations.CreateModel(
            name='FormTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of the form template', max_length=200)),
                ('form_type', models.CharField(choices=[('project', 'Project Form'), ('order', 'Order Form'), ('sample', 'Sample Form'), ('custom', 'Custom Form')], help_text='Type of form this template represents', max_length=20)),
                ('description', models.TextField(blank=True, help_text='Description of when to use this form template')),
                ('version', models.CharField(default='1.0', help_text='Version of this form template', max_length=20)),
                ('is_active', models.BooleanField(default=True, help_text='Whether this form template is currently active')),
                ('facility_specific', models.BooleanField(default=False, help_text='Whether this form is specific to a facility')),
                ('facility_name', models.CharField(blank=True, help_text='Name of the facility this form is for (if facility_specific)', max_length=200)),
                ('json_schema', models.JSONField(default=dict, help_text='JSON schema defining the form structure')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_form_templates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-updated_at'],
                'unique_together': {('name', 'version', 'facility_name')},
            },
        ),
        migrations.CreateModel(
            name='FormSubmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('submission_data', models.JSONField(help_text='The submitted form data')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('form_template', models.ForeignKey(help_text='The form template used for this submission', on_delete=django.db.models.deletion.PROTECT, to='app.formtemplate')),
                ('order', models.ForeignKey(blank=True, help_text='Related order (if applicable)', null=True, on_delete=django.db.models.deletion.CASCADE, to='app.order')),
                ('project', models.ForeignKey(blank=True, help_text='Related project (if applicable)', null=True, on_delete=django.db.models.deletion.CASCADE, to='app.project')),
                ('user', models.ForeignKey(help_text='User who submitted the form', on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]