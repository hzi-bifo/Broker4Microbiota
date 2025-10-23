
from django.db import migrations, models
import django.db.models.deletion


def set_project_links(apps, schema_editor):
    MagRun = apps.get_model('app', 'MagRun')
    ProjectSubmission = apps.get_model('app', 'ProjectSubmission')

    for mag_run in MagRun.objects.filter(project__isnull=True):
        project_ids = set(
            mag_run.reads.values_list('sample__order__project_id', flat=True)
        )
        project_ids.discard(None)
        if len(project_ids) == 1:
            mag_run.project_id = project_ids.pop()
            mag_run.save(update_fields=['project'])

    for submission in ProjectSubmission.objects.all():
        if submission.project_id is None:
            project_ids = list(submission.projects.values_list('id', flat=True))
            if len(project_ids) == 1:
                submission.project_id = project_ids[0]
                submission.save(update_fields=['project'])
        if submission.project_id and not submission.projects.filter(id=submission.project_id).exists():
            submission.projects.add(submission.project_id)


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0009_alter_submgrun_yaml_and_tax_ids'),
    ]

    operations = [
        migrations.AddField(
            model_name='magrun',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='mag_runs', to='app.project'),
        ),
        migrations.AddField(
            model_name='projectsubmission',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='project_submissions', to='app.project'),
        ),
        migrations.RunPython(set_project_links, migrations.RunPython.noop),
    ]
