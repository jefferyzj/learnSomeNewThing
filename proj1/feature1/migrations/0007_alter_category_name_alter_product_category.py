# Generated by Django 5.1.2 on 2024-11-05 00:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feature1', '0006_alter_product_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(default='1', max_length=100),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(default='New', on_delete=django.db.models.deletion.CASCADE, to='feature1.category'),
        ),
    ]