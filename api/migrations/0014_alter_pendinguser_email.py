# Generated by Django 5.0.4 on 2024-05-07 00:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_alter_pendinguser_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pendinguser',
            name='email',
            field=models.EmailField(default='', max_length=254, null=True, unique=True),
        ),
    ]
