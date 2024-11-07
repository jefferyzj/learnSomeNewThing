# Generated by Django 5.1.3 on 2024-11-07 22:56

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_management', '0002_task_producttask_product_tasks'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='process_status',
            new_name='status',
        ),
        migrations.AddField(
            model_name='producttask',
            name='result',
            field=models.CharField(blank=True, choices=[('no_detection', 'No Detection'), ('test_done', 'Test Done')], max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='task',
            name='can_be_skipped',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='task',
            name='completion_result',
            field=models.CharField(blank=True, choices=[('no_detection', 'No Detection'), ('test_done', 'Test Done')], max_length=50, null=True),
        ),
        migrations.RenameModel(
            old_name='ProcessStatus',
            new_name='Status',
        ),
        migrations.CreateModel(
            name='StatusTask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_tasks', to='product_management.status')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='task_statuses', to='product_management.task')),
            ],
        ),
    ]
