# Generated manually for updating Assembly and Bin relationships

from django.db import migrations, models
import django.db.models.deletion


def populate_new_relationships(apps, schema_editor):
    """Populate the new foreign key relationships based on existing ManyToMany relationships."""
    Assembly = apps.get_model('app', 'Assembly')
    Bin = apps.get_model('app', 'Bin')
    
    # For each assembly, set the read_fk to the first associated read
    for assembly in Assembly.objects.all():
        reads = assembly.read.all()
        if reads.exists():
            assembly.read_fk = reads.first()
            assembly.save()
    
    # For each bin, set the assembly_fk to the first associated assembly
    # Since bins were previously linked to reads, we need to find assemblies through reads
    for bin in Bin.objects.all():
        reads = bin.read.all()
        if reads.exists():
            # Find assemblies that are linked to the same reads
            for read in reads:
                assemblies = Assembly.objects.filter(read=read)
                if assemblies.exists():
                    bin.assembly_fk = assemblies.first()
                    bin.save()
                    break


def reverse_populate_new_relationships(apps, schema_editor):
    """Reverse the data migration - this is a no-op since we can't easily reverse the relationships."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0011_alter_projectsubmission_projects'),
    ]

    operations = [
        # Step 1: Add new foreign key fields as nullable
        migrations.AddField(
            model_name='assembly',
            name='read_fk',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, to='app.read'),
        ),
        migrations.AddField(
            model_name='bin',
            name='assembly_fk',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.CASCADE, to='app.assembly'),
        ),
        
        # Step 2: Data migration to populate the new fields
        migrations.RunPython(
            code=populate_new_relationships,
            reverse_code=reverse_populate_new_relationships,
        ),
        
        # Step 3: Remove the old ManyToMany fields
        migrations.RemoveField(
            model_name='assembly',
            name='read',
        ),
        migrations.RemoveField(
            model_name='bin',
            name='read',
        ),
        
        # Step 4: Rename the new fields to the original names
        migrations.RenameField(
            model_name='assembly',
            old_name='read_fk',
            new_name='read',
        ),
        migrations.RenameField(
            model_name='bin',
            old_name='assembly_fk',
            new_name='assembly',
        ),
        
        # Step 5: Make the fields non-nullable
        migrations.AlterField(
            model_name='assembly',
            name='read',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.read'),
        ),
        migrations.AlterField(
            model_name='bin',
            name='assembly',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.assembly'),
        ),
    ]



