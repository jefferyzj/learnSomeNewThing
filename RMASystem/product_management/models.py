from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from model_utils.models import TimeStampedModel, SoftDeletableModel
import uuid
from .utilhelpers import PRIORITY_LEVEL_CHOICES
from ordered_model.models import OrderedModel

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Location(models.Model):
    rack_name = models.CharField(max_length=100, default='None Rack')
    layer_number = models.IntegerField(default=-1)
    space_number = models.IntegerField(default=-1)

    class Meta:
        unique_together = ('rack_name', 'layer_number', 'space_number')

    def __str__(self):
        return f'{self.rack_name} - Layer {self.layer_number} - Space {self.space_number}'

    @staticmethod
    def create_rack_with_layers_and_spaces(rack_name, num_layers, num_spaces_per_layer):
        for layer in range(1, num_layers + 1):
            for space in range(1, num_spaces_per_layer + 1):
                Location.objects.create(rack_name=rack_name, layer_number=layer, space_number=space)

class Status(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_closed = models.BooleanField(default=False, help_text="Indicates if the status is a closed status")
    

    def __str__(self):
        return self.name

    def get_possible_next_statuses(self):
        transitions = StatusTransition.objects.filter(from_status=self).order_by('created')
        return [transition.to_status for transition in transitions]

class StatusTransition(TimeStampedModel):
    from_status = models.ForeignKey(Status, related_name='transitions_from', on_delete=models.CASCADE)
    to_status = models.ForeignKey(Status, related_name='transitions_to', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.from_status} -> {self.to_status}'

class Task(TimeStampedModel):
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
        result = self.result if self.result else "Not yet done"
        note = f" | Note: {self.note}" if self.note else ""
        return f"This Task: Action: {self.action} | Result: {result} | Note: {note}."

class StatusTask(OrderedModel):
    status = models.ForeignKey(Status, related_name='status_tasks', on_delete=models.CASCADE)
    task = models.ForeignKey(Task, related_name='task_statuses', on_delete=models.CASCADE)
    is_predefined = models.BooleanField(default=True, help_text="Indicates if the task is predefined for this status")
    order = models.PositiveIntegerField(default=0, editable=False, db_index=True)
    
    order_with_respect_to = 'status'

    class Meta(OrderedModel.Meta):
        ordering = ['order']

    def __str__(self):
        return f'- The task {self.task.action} under - status {self.status.name} - with the order {self.order}'
    
class ProductTask(TimeStampedModel):
    product = models.ForeignKey('Product', related_name='tasks_of_product', on_delete=models.CASCADE)
    task = models.ForeignKey(Task, related_name='products_of_task', on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    is_skipped = models.BooleanField(default=False)
    is_predefined = models.BooleanField(default=False, help_text="Indicates if the task was added automatically")
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    def __str__(self):
        return f'{self.product.SN} - {self.task.action} (UUID: {self.unique_id})'
    
class ProductStatus(TimeStampedModel):
    product = models.ForeignKey('Product', related_name='status_history_of_product', on_delete=models.CASCADE)
    status = models.ForeignKey(Status, related_name='products_under_status', on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.product.SN} - {self.status.name} at {self.changed_at}'
    
    def get_product_status_result(self):
        tasks = ProductTask.objects.filter(product=self.product, task__statustask__status=self.status).order_by('task__statustask__created')
        result = f'{self.status.name}: '
        for task in tasks:
            result += f'{task.task.action} - {task.result}'
            if task.note:
                result += f' - Note: {task.note}'
            result += ' | '
        return result

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
    category = models.ForeignKey('Category', related_name='products', on_delete=models.CASCADE)
    priority_level = models.CharField(max_length=10, choices=PRIORITY_LEVEL_CHOICES, default='normal', help_text="Indicates if the unit is Normal, Hot, or ZFA")
    description = models.TextField(blank=True, help_text="Notes or description of the product")
    current_status = models.ForeignKey('Status', related_name='ALL_products', on_delete=models.CASCADE, null=True, blank=True)
    current_task = models.ForeignKey('Task', related_name='All_products', on_delete=models.SET_NULL, null=True, blank=True)
    location = models.OneToOneField('Location', on_delete=models.CASCADE, related_name='product', null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['SN'], name='unique_sn_constraint'),
            models.CheckConstraint(check=models.Q(SN__regex=r'^\d{13}$'), name='check_sn_digits_constraint'),
            models.UniqueConstraint(fields=['location'], name='unique_product_location_constraint')
        ]

    def __str__(self):
        current_task_action = self.current_task.action if self.current_task else "No task assigned"
        return f'Product SN: {self.SN} | Priority: {self.priority_level} | Current Status: {self.current_status.name if self.current_status else "No status"} | Action of Task: {current_task_action}'

    def save(self, *args, **kwargs):
        is_new = not self.pk
        previous_status = None

        if is_new:
            if not self.current_status:
                rma_sorting_status, created = Status.objects.get_or_create(name="RMA Sorting")
                self.current_status = rma_sorting_status
        else:
            previous_status = Product.objects.get(pk=self.pk).current_status

        super().save(*args, **kwargs)
        
        if is_new or previous_status != self.current_status:
            ProductStatus.objects.create(product=self, status=self.current_status)
            self.assign_predefined_tasks_by_status()
            self.locate_current_task()

            # Check if the product is moving to a closed status
            if self.current_status and self.current_status.is_closed:
                # Release the location
                self.location = None
                # Set current_task to None
                self.current_task = None
                # Save the changes
                self.save(update_fields=['location', 'current_task'])

    def locate_current_task(self):
        first_uncompleted_task = self.tasks_of_product.filter(is_completed=False).select_related('task__statustask').order_by('task__statustask__order').first()
        new_current_task = first_uncompleted_task.task if first_uncompleted_task else None

        if self.current_task != new_current_task:
            self.current_task = new_current_task
            self.save(update_fields=['current_task'])

    def assign_predefined_tasks_by_status(self):
        status_tasks_predefined = self.current_status.status_tasks.filter(is_predefined=True).order_by('order')
        for status_task in status_tasks_predefined:
            ProductTask.objects.create(product=self, task=status_task.task, is_predefined=True)

    def assign_tasks(self, task, set_as_predefined_of_status=False):
        # Check if a StatusTask with the same status and task already exists
        if not StatusTask.objects.filter(status=self.current_status, task=task).exists():
            StatusTask.objects.create(
                status=self.current_status,
                task=task,
                defaults={'is_predefined': set_as_predefined_of_status}
            )
        # Create a ProductTask for the product
        ProductTask.objects.create(product=self, task=task, is_predefined=False)

    def insert_task_at_position(self, task, position, set_as_predefined_of_status=False):
        # Get the number of completed tasks
        num_completed_tasks = self.tasks_of_product.filter(is_completed=True).count()

        # Check if the target position is within the range of completed tasks
        if position <= num_completed_tasks:
            raise ValueError("Cannot insert a task at a position within the range of completed tasks.")

        # Create the new task at the specified position
        status_task = StatusTask.objects.create(
            status=self.current_status,
            task=task,
            is_predefined=set_as_predefined_of_status
        )
        
        # Move the task to the specified position
        status_task.to(position - 1)  # `to` method uses zero-based index
        
        # Assign the task to the product
        ProductTask.objects.create(product=self, task=task, is_predefined=set_as_predefined_of_status)

    def get_all_tasks(self, only_not_completed_yet=False):
        tasks = self.tasks_of_product.select_related('task__statustask__status').order_by(
            'task__statustask__status__created', 'task__statustask__order'
        )
        if only_not_completed_yet:
            tasks = tasks.filter(is_completed=False)
        return tasks


    def get_ongoing_task(self):
        return self.current_task

    def skip_task(self, task):
        self.tasks_of_product.filter(task=task).update(
            is_completed=True, 
            is_skipped=True,
            result="Skipped"
        )
        if self.current_task == task:
            self.current_task = None
            self.save()

    def update_current_task(self, is_finished=False, result=None, modified_action=None):
        product_task = self.tasks_of_product.filter(task=self.current_task).first()
        if product_task:
            product_task.is_completed = is_finished
            if result is not None:
                product_task.result = result
            product_task.save()

            if modified_action:
                task = product_task.task
                task.action = modified_action
                task.save()

            if is_finished:
                self.locate_current_task()

    def get_possible_next_statuses(self):
        return self.current_status.get_possible_next_statuses()

    def list_status_result_history(self):
        all_product_statuses = self.status_history_of_product.order_by('changed_at')
        history = [f'Product SN: {self.SN}']
        for product_status in all_product_statuses:
            status_result = product_status.get_product_status_result()
            history.append(f'{status_result} at {product_status.changed_at}')
        return "\n".join(history)
    