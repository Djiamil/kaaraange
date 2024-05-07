# Generated by Django 5.0.4 on 2024-05-07 00:36

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_remove_otp_user_otp_pending_user'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pendinguser',
            options={'verbose_name_plural': 'Utilisateurs en attente'},
        ),
        migrations.RemoveField(
            model_name='parent',
            name='numero_telephone',
        ),
        migrations.RemoveField(
            model_name='pendinguser',
            name='condition_utilisation',
        ),
        migrations.RemoveField(
            model_name='pendinguser',
            name='mot_de_passe',
        ),
        migrations.RemoveField(
            model_name='pendinguser',
            name='user',
        ),
        migrations.AddField(
            model_name='parent',
            name='telephone',
            field=models.CharField(max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='pendinguser',
            name='accepted_terms',
            field=models.BooleanField(default=False, verbose_name="Accepté les conditions d'utilisation"),
        ),
        migrations.AddField(
            model_name='pendinguser',
            name='date_de_naissance',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='pendinguser',
            name='email',
            field=models.EmailField(default='', max_length=254, unique=True),
        ),
        migrations.AddField(
            model_name='pendinguser',
            name='gender',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Genre'),
        ),
        migrations.AddField(
            model_name='pendinguser',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='pendinguser',
            name='is_archive',
            field=models.BooleanField(default=False, verbose_name="Accepté les conditions d'utilisation"),
        ),
        migrations.AddField(
            model_name='pendinguser',
            name='nom',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='pendinguser',
            name='otp_token',
            field=models.CharField(blank=True, max_length=6, null=True, verbose_name='Token OTP'),
        ),
        migrations.AddField(
            model_name='pendinguser',
            name='password',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='pendinguser',
            name='registration_method',
            field=models.CharField(choices=[('GOOGLE', 'GOOGLE'), ('FACEBOOK', 'FACEBOOK'), ('APPLE', 'APPLE'), ('NORMAL', 'NORMAL')], default='normal', max_length=50),
        ),
        migrations.AddField(
            model_name='pendinguser',
            name='user_type',
            field=models.CharField(choices=[('ADMIN', 'ADMIN'), ('PARENT', 'PARENT'), ('CHILD', 'CHILD'), ('TUTEUR', 'TUTEUR')], default='PARENT', max_length=50),
        ),
        migrations.AddField(
            model_name='user',
            name='nom',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='user',
            name='prenom',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='child',
            name='parent_user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='children', to='api.parent'),
        ),
        migrations.AlterField(
            model_name='pendinguser',
            name='adresse',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='pendinguser',
            name='prenom',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='pendinguser',
            name='telephone',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(default='', max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='password',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.CreateModel(
            name='ParentChildLink',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('qr_code', models.CharField(blank=True, max_length=255, null=True)),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.child')),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.parent')),
            ],
        ),
    ]
