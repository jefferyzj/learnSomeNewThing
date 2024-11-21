from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from model_utils.models import TimeStampedModel, SoftDeletableModel, StatusModel
import uuid
from .utilhelpers import PRIORITY_LEVEL_CHOICES

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

class Status(TimeStampedModel, StatusModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.status

    def get_possible_next_statuses(self):
        transitions = StatusTransition.objects.filter(from_status=self).order_by('created')
        return [transition.to_status for transition in transitions]
    
#use to define the possible transition between statuses  
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

class StatusTask(TimeStampedModel):
    status = models.ForeignKey(Status, related_name='status_tasks', on_delete=models.CASCADE)
    task = models.ForeignKey(Task, related_name='task_statuses', on_delete=models.CASCADE)
    is_predefined = models.BooleanField(default=True, help_text="Indicates if the task is predefined for this status")
    order = models.IntegerField(default=0, help_text="Order of the task within the status", unique=True)

    def __str__(self):
        return f'- The task {self.task.action} under - status {self.status.name} - with the order {self.order}'

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
    current_status = models.ForeignKey(Status, related_name='ALL_products', on_delete=models.CASCADE, default="new")
    current_task = models.ForeignKey(Task, related_name='All_products', on_delete=models.SET_NULL, null=True, blank=True)
    location = models.OneToOneField(Location, on_delete=models.CASCADE, related_name='product', null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['SN'], name='unique_sn_constraint'),
            models.CheckConstraint(check=models.Q(SN__regex=r'^\d{13}$'), name='check_sn_digits_constraint'),
            models.UniqueConstraint(fields=['location'], name='unique_product_location_constraint')
        ]

    def __str__(self):
        current_task_action = self.current_task.action if self.current_task else "No task assigned"
        return f'Product SN: {self.SN} | Priority: {self.priority_level} | Current Status: {self.current_status.name} | Action of Task: {current_task_action}'

    def save(self, *args, **kwargs):
        is_new = not self.pk
        previous_status = None

        if is_new:
            if not self.current_status:
                # Set the default status to "RMA Sorting" if the product is new and no status is provided
                rma_sorting_status= Status.objects.create(name="RMA Sorting")
                self.current_status = rma_sorting_status
        else:
            previous_status = Product.objects.get(pk=self.pk).current_status

        super().save(*args, **kwargs)
        #under a init status, assign predefined tasks to the product and locate the current task
        if is_new or previous_status != self.current_status:
            ProductStatus.objects.create(product=self, status=self.current_status)
            self.assign_predefined_tasks_by_status()
            self.locate_current_task()

    def locate_current_task(self):
        # Locate the first uncompleted task to the current_task field in the case the status of product is just updated
        first_uncompleted_task = ProductTask.objects.filter(product=self, is_completed=False).order_by('task__statustask__created').first()
        if first_uncompleted_task:
            self.current_task = first_uncompleted_task.task
        else:
            self.current_task = None
        self.save(update_fields=['current_task'])



    def assign_predefined_tasks_by_status(self):
        # Fetch predefined tasks from the StatusTask model
        status_tasks_predefined = StatusTask.objects.filter(status=self.status, is_predefined=True).order_by('created')

        for status_task in status_tasks_predefined:
            task = status_task.task
            ProductTask.objects.create(product=self, task=task, is_default=True, timestamp=timezone.now())

    def assign_tasks(self, task, set_as_predefined_of_status=False):
        # Allow the same task to be added multiple times, add the task to the ProductTask model
        ProductTask.objects.create(product=self, task=task, is_default=False, timestamp=timezone.now())
          
        # Add the task to the StatusTask model and set it as predefined for the status if needed
        StatusTask.objects.create(
            status=self.status, 
            task=task, 
            defaults={'is_predefined': set_as_predefined_of_status},
            timestamp = timezone.now(),           
        )

    def get_all_tasks(self, only_not_completed_yet=False):
        # Retrieve all statuses of this product ordered by created timestamp
        statuses = Status.objects.filter(products=self).order_by('created')
        
        all_tasks = []
        for status in statuses:
            # Retrieve tasks within each status ordered by StatusTask created order
            if only_not_completed_yet:
                tasks = Task.objects.filter(
                    producttask__product=self,
                    producttask__is_completed=False,
                    producttask__task__statustask__status=status
                ).order_by('producttask__task__statustask__created')
            else:
                tasks = Task.objects.filter(
                    producttask__product=self,
                    producttask__task__statustask__status=status
                ).order_by('producttask__task__statustask__created')
            
            all_tasks.extend(tasks)
        
        return all_tasks
        
    def get_ongoing_task(self):
        # Retrieve the first uncompleted task, ordered by the custom order field
        return self.current_task
    
    # Implement the function to skip a task. Basically, skip a task of a product is just write "skipped" in the result of the action, and update the is_completed field to True.
    def skip_task(self, task):
        # Skip a task and update the result of the task
        ProductTask.objects.filter(product=self, task=task).update(
            is_completed=True, 
            is_skipped=True,
            result="Skipped")
        # Update the current_task if the skipped task is the current task
        if self.current_task == task:
            self.current_task = None
            self.save()
        
    def update_current_task(self, is_finished=False, result=None, modified_action=None):
        # Retrieve the current ProductTask instance
        product_task = ProductTask.objects.filter(product=self, task=self.current_task)
        if product_task:
            # Update the ProductTask instance
            product_task.is_completed = is_finished
            if result is not None:
                product_task.result = result
            product_task.save()

            # Update the Task instance if modified_action is provided
            if modified_action:
                task = product_task.task
                task.action = modified_action
                task.save()

            # Update the current_task if the completed task is the current task
            if is_finished:
                self.locate_current_task()


    def get_possible_next_statuses(self):
        return self.current_status.get_possible_next_statuses()
   

    def list_status_result_history(self):
        all_product_statuses = ProductStatus.objects.filter(product=self).order_by('changed_at')
        history = [f'Product SN: {self.SN}']
        for product_status in all_product_statuses:
            status_result = product_status.get_product_status_result()
            history.append(f'{status_result} at {product_status.changed_at}')
        return "\n".join(history)
        

class ProductTask(TimeStampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    is_skipped = models.BooleanField(default=False)
    is_Predefined = models.BooleanField(default=False, help_text="Indicates if the task was added automatically")
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    def __str__(self):
        return f'{self.product.SN} - {self.task.action} (UUID: {self.unique_id})'
    
class ProductStatus(TimeStampedModel):
    product = models.ForeignKey(Product, related_name='status_history', on_delete=models.CASCADE)
    status = models.ForeignKey(Status, on_delete=models.CASCADE)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.product.SN} - {self.status.name} at {self.changed_at}'
    
    #TODO: get the result of all the tasks of product under this status, the format of the result of one task is: task action + task result + task note if it has, but at first, add the status name.
    def get_product_status_result(self):
        tasks = ProductTask.objects.filter(product=self.product, task__statustask__status=self.status).order_by('task__statustask__created')
        result = f'{self.status.name}: '
        for task in tasks:
            result += f'{task.task.action} - {task.result}'
            if task.note:
                result += f' - Note: {task.note}'
            result += ' | '
        return result
        


        