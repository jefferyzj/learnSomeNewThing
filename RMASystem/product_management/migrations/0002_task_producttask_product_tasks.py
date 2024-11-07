# Generated by Django 5.1.3 on 2024-11-07 20:15

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_management', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='ProductTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_completed', models.BooleanField(default=False)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product_management.product')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='product_management.task')),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='tasks',
            field=models.ManyToManyField(through='product_management.ProductTask', to='product_management.task'),
        ),
    ]
