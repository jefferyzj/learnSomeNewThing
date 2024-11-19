from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from model_utils.models import TimeStampedModel, SoftDeletableModel, StatusModel
import uuid
from .utilhelpers import PRIORITY_LEVEL_CHOICES, STATUS_CHOICES

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Location(models.Model):
    rack_name = models.CharField(max_length=100, default='None Rack')
    layer_number = models.IntegerField(default=-1)
    space_number = models.IntegerField(default=-1)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['rack_name', 'layer_number', 'space_number'], name='unique_location_constraint')
        ]

    def __str__(self):
        return f'Rack {self.rack_name} - Layer {self.layer_number} - Space {self.space_number}'

    @staticmethod
    def create_rack_with_layers_and_spaces(rack_name, num_layers, num_spaces_per_layer):
        for layer_number in range(1, num_layers + 1):
            for space_number in range(1, num_spaces_per_layer + 1):
                Location.objects.get_or_create(rack_name=rack_name, layer_number=layer_number, space_number=space_number)

class Status(StatusModel):
    STATUS = STATUS_CHOICES
    status = models.CharField(choices=STATUS, default=STATUS.new, max_length=100)
    name = models.CharField(max_length=50)
    possible_next_statuses = models.ManyToManyField('self', blank=True, related_name='previous_statuses', symmetrical=False)

    def __str__(self):
        return self.name

class Task(models.Model):
    action = models.CharField(
        max_length=100, 
        help_text="Action to be performed in this task", 
        default="Default Action"
    )
    description = models.TextField(
        help_text="Detailed description of the task", 
        blank=True, 
        null=True
    )
    can_be_skipped = models.BooleanField(
        default=True, 
        help_text="Indicates if the task can be skipped, default is True"
    )
    result = models.TextField(
        default="Action Not Yet Done", 
        help_text="Result of the task", 
        blank=True, 
        null=True
    )
    note = models.TextField(
        help_text="User can write down some notes on this task", 
        blank=True, 
        null=True
    )

    def __str__(self):
        return self.action

class StatusTask(models.Model):
    status = models.ForeignKey(Status, related_name='status_tasks', on_delete=models.CASCADE)
    task = models.ForeignKey(Task, related_name='task_statuses', on_delete=models.CASCADE)
    is_predefined = models.BooleanField(default=True, help_text="Indicates if the task is predefined for this status")
    order = models.IntegerField(default=0, help_text="Order of the task within the status")

    def __str__(self):
        return f'{self.status.name} - {self.task.action}'

class Product(TimeStampedModel, SoftDeletableModel):
    SN = models.CharField(
        primary_key=True,
        max_length=13,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^\d{13}$',
                message='SN must be exactly 13 digits',
                code='invalid_sn'
            )
        ],
        help_text="Serial number must be exactly 13 digits"
    )
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    priority_level = models.CharField(max_length=10, choices=PRIORITY_LEVEL_CHOICES, default='normal', help_text="Indicates if the unit is Normal, Hot, or ZFA")
    description = models.TextField(blank=True, help_text="Notes or description of the product")
    status = models.ForeignKey(Status, related_name='products', on_delete=models.CASCADE)
    tasks = models.ManyToManyField(Task, through='ProductTask')
    location = models.OneToOneField(Location, on_delete=models.CASCADE, related_name='product', null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['SN'], name='unique_sn_constraint'),
            models.CheckConstraint(check=models.Q(SN__regex=r'^\d{13}$'), name='check_sn_digits_constraint'),
            models.UniqueConstraint(fields=['location'], name='unique_product_location_constraint')
        ]

    def __str__(self):
        current_task_action = self.tasks.filter(producttask__is_completed=False).order_by('producttask__order').first().action if self.tasks.filter(producttask__is_completed=False).exists() else "No ongoing task"
        return f'Product SN: {self.SN} | Priority: {self.get_priority_level_display()} | Current Status: {self.status.name} | Action: {current_task_action}'

    def save(self, *args, **kwargs):
        is_new = not self.pk
        previous_status = None
        if not is_new:
            previous_status = Product.objects.get(pk=self.pk).status

        super().save(*args, **kwargs)

        if is_new or previous_status != self.status:
            self.assign_predefined_tasks_by_status()

    def assign_predefined_tasks_by_status(self):
        # Fetch predefined tasks from the StatusTask model
        status_tasks_predefined = StatusTask.objects.filter(status=self.status, is_predefined=True).order_by('order')

        for status_task in status_tasks_predefined:
            task = status_task.task
            # Use the order from the StatusTask model
            ProductTask.objects.create(product=self, task=task, is_default=True, timestamp=timezone.now())

    def assign_tasks(self, task, set_as_predefined_of_status=False):
        # Allow the same task to be added multiple times, add the task to the ProductTask model
        ProductTask.objects.create(product=self, task=task, is_default=False, timestamp=timezone.now())
        
        # Add the task to the StatusTask model and set it as predefined for the status if needed
        StatusTask.objects.get_or_create(status=self.status, task=task, defaults={'is_predefined': set_as_predefined_of_status})

    def get_next_order(self):
        # Get the next order value for a new task
        max_order = self.tasks.through.objects.filter(product=self).aggregate(models.Max('order'))['order__max']
        return (max_order or 0) + 1

    def get_all_tasks(self):
        # Retrieve all tasks associated with this product, ordered by the custom order field
        return self.tasks.filter(producttask__is_completed=False).order_by('producttask__order')

    def get_ongoing_task(self):
        # Retrieve the first uncompleted task, ordered by the custom order field
        ongoing_task = self.tasks.filter(producttask__is_completed=False).order_by('producttask__order').first()
        return ongoing_task

    def remove_task(self, task):
        # Remove a task from the product
        ProductTask.objects.filter(product=self, task=task).delete()

    def insert_task(self, task, position):
        # Insert a task at a specific position, reordering other tasks
        tasks = list(self.get_all_tasks())
        tasks.insert(position, task)
        for index, task in enumerate(tasks):
            ProductTask.objects.filter(product=self, task=task).update(order=index)

    def get_next_statuses(self):
        return self.status.possible_next_statuses.all()

    def generate_result_of_status(self):
        # Collect results of completed tasks and actions of uncompleted tasks
        completed_tasks = self.tasks.filter(producttask__is_completed=True, producttask__task__status_tasks__status=self.status)
        uncompleted_tasks = self.tasks.filter(producttask__is_completed=False, producttask__task__status_tasks__status=self.status)

        completed_task_details = [f"{task.action}: {task.result}" for task in completed_tasks]
        uncompleted_task_details = [f"{task.action}: Not completed" for task in uncompleted_tasks]

        summary_result = "\n".join(completed_task_details + uncompleted_task_details)

        result_of_status, created = ResultOfStatus.objects.get_or_create(
            product=self,
            status=self.status,
            defaults={'summary_result': summary_result}
        )
        if not created:
            result_of_status.summary_result = summary_result
            result_of_status.save()

        return result_of_status

    def list_status_history(self):
        status_results = ResultOfStatus.objects.filter(product=self).order_by('created')
        history = []
        for result in status_results:
            tasks = self.tasks.filter(producttask__status=result.status).order_by('producttask__created')
            task_details = [
                {
                    "action": task.action,
                    "result": task.result,
                    "created_at": task.producttask_set.get(product=self).created
                }
                for task in tasks
            ]
            history.append({
                "status": result.status.name,
                "summary_result": result.summary_result,
                "tasks": task_details
            })
        return history

class ProductTask(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    is_default = models.BooleanField(default=True, help_text="Indicates if the task was added automatically")
    timestamp = models.DateTimeField(default=timezone.now, editable=False)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    def __str__(self):
        return f'{self.product.SN} - {self.task.action} (UUID: {self.unique_id})'
class ResultOfStatus(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='status_results')
    status = models.ForeignKey(Status, on_delete=models.CASCADE, related_name='status_results')
    summary_result = models.TextField(blank=True, null=True, help_text="Summary of the results for this status")
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f'{self.product.SN} - {self.status.name} Result'
