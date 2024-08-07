# Generated by Django 5.0.4 on 2024-08-07 10:58

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0041_remove_alertnotification_contact_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='alertnotification',
            name='contact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.emergencycontact'),
        ),
    ]
