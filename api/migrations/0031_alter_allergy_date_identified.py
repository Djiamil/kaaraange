# Generated by Django 5.0.4 on 2024-05-30 10:27

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0030_emergencynumber_remove_child_allergies_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='allergy',
            name='date_identified',
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]
