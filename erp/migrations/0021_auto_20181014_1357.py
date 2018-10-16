# Generated by Django 2.1.1 on 2018-10-14 13:57

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('erp', '0020_auto_20181008_1612'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rental',
            name='due_for',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='subscription_date',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
