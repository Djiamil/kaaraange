# Generated by Django 5.0.4 on 2024-10-30 16:37

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0050_perimetresecurite_slug_pointtrajet_slug'),
    ]

    operations = [
        migrations.CreateModel(
            name='Demande',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(default=uuid.uuid1)),
                ('relationship', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('enfant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='demandes', to='api.child')),
                ('notification', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='api.alertnotification')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='demandes_envoyees', to='api.parent')),
            ],
        ),
    ]