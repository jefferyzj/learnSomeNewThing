# Generated by Django 5.1.2 on 2024-11-04 23:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feature1', '0004_alter_layer_number_alter_position_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='feature1.category'),
        ),
        migrations.AlterField(
            model_name='product',
            name='process_status',
            field=models.CharField(choices=[('sorting_test', 'Under Sorting Test'), ('basic_check', 'Under Basic Check'), ('fa_lab', 'To FA Lab')], default='sorting_test', max_length=20),
        ),
    ]
