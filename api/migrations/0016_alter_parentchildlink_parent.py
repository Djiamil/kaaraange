# Generated by Django 5.0.4 on 2024-05-07 12:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0015_remove_child_parent_user_alter_pendinguser_email_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parentchildlink',
            name='parent',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='api.parent'),
        ),
    ]
