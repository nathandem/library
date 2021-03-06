# Generated by Django 2.1.1 on 2018-09-25 16:39

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0014_auto_20180924_1435'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='librarian',
            name='has_rent_issue',
        ),
        migrations.AddField(
            model_name='bookinstance',
            name='joined_library_on',
            field=models.DateField(default=datetime.date.today),
        ),
        migrations.AddField(
            model_name='bookinstance',
            name='left_library_cause',
            field=models.CharField(blank=True, choices=[('WORN', 'Worn-out'), ('STOLEN', 'Stolen'), ('NEVER_RETURNED', 'Never returned')], max_length=15, null=True),
        ),
        migrations.AddField(
            model_name='bookinstance',
            name='left_library_on',
            field=models.DateField(blank=True, null=True),
        ),
    ]
