# Generated by Django 5.0.4 on 2024-06-04 17:14

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0033_allergy_slug_emergencyalert_slug_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='emergencyalert',
            name='parent',
        ),
        migrations.AlterField(
            model_name='emergencyalert',
            name='alert_type',
            field=models.CharField(choices=[('assistance', 'Assistance'), ('danger', 'Danger'), ('prevenu', "Prévenu par l'enfant")], default="Prévenu par l'enfant", max_length=20),
        ),
        migrations.CreateModel(
            name='AlertNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notified_at', models.DateTimeField(auto_now_add=True)),
                ('alert', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='api.emergencyalert')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.emergencycontact')),
            ],
        ),
    ]
