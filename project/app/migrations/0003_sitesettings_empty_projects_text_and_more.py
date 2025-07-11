# Generated by Django 5.2.4 on 2025-07-07 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_sitesettings'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='empty_projects_text',
            field=models.TextField(blank=True, default='Welcome to the Sequencing Order Management System! Start by creating your first project to organize and track your sequencing requests.', help_text='Message shown when user has no projects'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='project_form_description',
            field=models.TextField(blank=True, default='A project represents a study or experiment that groups related sequencing orders. Each project can contain multiple orders for different samples or time points.', help_text='Description shown on project creation form'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='project_form_title',
            field=models.CharField(default='Create New Sequencing Project', help_text='Title shown on project creation form', max_length=200),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='projects_with_samples_text',
            field=models.TextField(blank=True, default='You have active sequencing projects. Create a new project for a different study or continue working on your existing projects.', help_text='Message shown when user has projects with samples'),
        ),
    ]
