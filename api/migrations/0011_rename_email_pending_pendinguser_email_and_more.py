# Generated by Django 5.0.4 on 2024-05-07 00:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_alter_user_email'),
    ]

    operations = [
        migrations.RenameField(
            model_name='pendinguser',
            old_name='email_pending',
            new_name='email',
        ),
        migrations.AlterField(
            model_name='pendinguser',
            name='password',
            field=models.CharField(default=None, max_length=255),
        ),
    ]