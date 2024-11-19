# Generated by Django 5.1.3 on 2024-11-19 07:58

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name="Task",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        default="Default Action",
                        help_text="Action to be performed in this task",
                        max_length=100,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True,
                        help_text="Detailed description of the task",
                        null=True,
                    ),
                ),
                (
                    "can_be_skipped",
                    models.BooleanField(
                        default=False, help_text="Indicates if the task can be skipped"
                    ),
                ),
                (
                    "result",
                    models.TextField(
                        blank=True,
                        default="Action Not Yet Done",
                        help_text="Result of the task",
                        null=True,
                    ),
                ),
                (
                    "note",
                    models.TextField(
                        blank=True,
                        help_text="User can write down some notes on this task",
                        null=True,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Location",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("rack_name", models.CharField(default="None Rack", max_length=100)),
                ("layer_number", models.IntegerField(default=-1)),
                ("space_number", models.IntegerField(default=-1)),
            ],
            options={
                "constraints": [
                    models.UniqueConstraint(
                        fields=("rack_name", "layer_number", "space_number"),
                        name="unique_location_constraint",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("is_removed", models.BooleanField(default=False)),
                (
                    "SN",
                    models.CharField(
                        help_text="Serial number must be exactly 13 digits",
                        max_length=13,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                code="invalid_sn",
                                message="SN must be exactly 13 digits",
                                regex="^\\d{13}$",
                            )
                        ],
                    ),
                ),
                (
                    "priority_level",
                    models.CharField(
                        choices=[("normal", "Normal"), ("hot", "Hot"), ("zfa", "ZFA")],
                        default="normal",
                        help_text="Indicates if the unit is Normal, Hot, or ZFA",
                        max_length=10,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        blank=True, help_text="Notes or description of the product"
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="products",
                        to="product_management.category",
                    ),
                ),
                (
                    "location",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="product",
                        to="product_management.location",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Status",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status_changed",
                    model_utils.fields.MonitorField(
                        default=django.utils.timezone.now,
                        monitor="status",
                        verbose_name="status changed",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                            ("archived", "Archived"),
                        ],
                        default="new",
                        max_length=100,
                    ),
                ),
                ("name", models.CharField(max_length=50)),
                (
                    "possible_next_statuses",
                    models.ManyToManyField(
                        blank=True,
                        related_name="previous_statuses",
                        to="product_management.status",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ResultOfStatus",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                (
                    "summary_result",
                    models.TextField(
                        blank=True,
                        help_text="Summary of the results for this status",
                        null=True,
                    ),
                ),
                (
                    "unique_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_results",
                        to="product_management.product",
                    ),
                ),
                (
                    "status",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_results",
                        to="product_management.status",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="product",
            name="status",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="products",
                to="product_management.status",
            ),
        ),
        migrations.CreateModel(
            name="StatusTask",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_tasks",
                        to="product_management.status",
                    ),
                ),
                (
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="task_statuses",
                        to="product_management.task",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ProductTask",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                ("is_completed", models.BooleanField(default=False)),
                (
                    "is_default",
                    models.BooleanField(
                        default=True,
                        help_text="Indicates if the task was added automatically",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(
                        default=django.utils.timezone.now, editable=False
                    ),
                ),
                (
                    "unique_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="product_management.product",
                    ),
                ),
                (
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="product_management.task",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="product",
            name="tasks",
            field=models.ManyToManyField(
                through="product_management.ProductTask", to="product_management.task"
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(
                fields=("SN",), name="unique_sn_constraint"
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.CheckConstraint(
                condition=models.Q(("SN__regex", "^\\d{13}$")),
                name="check_sn_digits_constraint",
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(
                fields=("location",), name="unique_product_location_constraint"
            ),
        ),
    ]
