# Generated by Django 5.1.2 on 2024-11-04 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feature1', '0002_category_layer_rack_remove_product_created_at_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='SN',
            field=models.CharField(default='0000000000000', max_length=100, unique=True),
        ),
    ]
