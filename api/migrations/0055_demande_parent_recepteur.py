# Generated by Django 5.0.4 on 2024-11-05 15:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0054_alertnotification_status_demande_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='demande',
            name='parent_recepteur',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='demandes_recues', to='api.parent'),
        ),
    ]
