# Generated by Django 2.1.2 on 2018-11-02 23:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_auto_20181012_2301'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelrun',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='core.ModelRun'),
        ),
    ]
