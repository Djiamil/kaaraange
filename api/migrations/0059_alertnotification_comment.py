# Generated by Django 5.0.4 on 2024-12-09 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0058_perimetresecurite_is_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='alertnotification',
            name='comment',
            field=models.TextField(blank=True, max_length=10, null=True),
        ),
    ]