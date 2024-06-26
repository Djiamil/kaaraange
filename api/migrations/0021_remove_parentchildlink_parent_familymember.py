# Generated by Django 5.0.4 on 2024-05-10 10:23

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0020_alter_otp_pending_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='parentchildlink',
            name='parent',
        ),
        migrations.CreateModel(
            name='FamilyMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(default=uuid.uuid1)),
                ('relation', models.CharField(max_length=100)),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.child')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.parent')),
            ],
        ),
    ]
