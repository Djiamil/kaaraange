# Generated by Django 5.0.4 on 2024-10-31 16:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0051_demande'),
    ]

    operations = [
        migrations.AddField(
            model_name='familymember',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
