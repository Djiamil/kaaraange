# Generated by Django 5.0.4 on 2024-09-06 13:45

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0047_remove_pointtrajet_enfant_perimetresecurite_enfant_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pointtrajet',
            name='enfant',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.child'),
        ),
    ]
