# Generated by Django 5.0.4 on 2024-05-07 12:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_alter_parentchildlink_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parentchildlink',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.parent'),
        ),
    ]
