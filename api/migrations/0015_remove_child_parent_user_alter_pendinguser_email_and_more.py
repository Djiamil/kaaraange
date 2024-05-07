# Generated by Django 5.0.4 on 2024-05-07 01:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_alter_pendinguser_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='child',
            name='parent_user',
        ),
        migrations.AlterField(
            model_name='pendinguser',
            name='email',
            field=models.EmailField(default='', max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='pendinguser',
            name='nom',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='pendinguser',
            name='password',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='pendinguser',
            name='prenom',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='nom',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='user',
            name='password',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='user',
            name='prenom',
            field=models.CharField(max_length=100),
        ),
    ]
