# Generated by Django 2.1.1 on 2018-10-01 15:53

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('erp', '0016_auto_20181001_1132'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rental',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rent_on', models.DateField(auto_now_add=True)),
                ('due_for', models.DateField(default=datetime.date(2018, 10, 15))),
                ('returned_on', models.DateField(blank=True, null=True)),
                ('late', models.BooleanField(default=True)),
            ],
        ),
        migrations.AlterModelOptions(
            name='book',
            options={'ordering': ['generic_book', 'id']},
        ),
        migrations.RemoveField(
            model_name='book',
            name='borrower',
        ),
        migrations.RemoveField(
            model_name='book',
            name='due_back',
        ),
        migrations.AlterField(
            model_name='genericbook',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='generic_books', to='erp.Author'),
        ),
        migrations.AlterField(
            model_name='genericbook',
            name='genre',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='generic_books', to='erp.Genre'),
        ),
        migrations.AlterField(
            model_name='subscriber',
            name='subscription_date',
            field=models.DateField(auto_now_add=True),
        ),
        migrations.AddField(
            model_name='rental',
            name='book',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='erp.Book'),
        ),
        migrations.AddField(
            model_name='rental',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='rent_books', to=settings.AUTH_USER_MODEL),
        ),
    ]