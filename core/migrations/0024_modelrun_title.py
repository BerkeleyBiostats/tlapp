# Generated by Django 2.1.2 on 2018-10-12 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_modelrun_base_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='modelrun',
            name='title',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
