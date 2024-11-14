# Generated by Django 5.1.3 on 2024-11-14 23:29

import django.utils.timezone
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_management', '0004_remove_product_damage_description_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='producttask',
            name='result_choice',
        ),
        migrations.RemoveField(
            model_name='producttask',
            name='result_text',
        ),
        migrations.RemoveField(
            model_name='task',
            name='result_choices',
        ),
        migrations.RemoveField(
            model_name='task',
            name='result_type',
        ),
        migrations.AddField(
            model_name='producttask',
            name='is_default',
            field=models.BooleanField(default=True, help_text='Indicates if the task was added automatically'),
        ),
        migrations.AddField(
            model_name='producttask',
            name='timestamp',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
        ),
        migrations.AddField(
            model_name='producttask',
            name='unique_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name='resultofstatus',
            name='unique_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name='task',
            name='result',
            field=models.TextField(default='Action Not Yet Done', help_text='Result of the task'),
        ),
    ]
