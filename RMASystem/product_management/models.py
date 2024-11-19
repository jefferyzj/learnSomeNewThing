from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Rack(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    @staticmethod
    def create_rack_with_layers_and_spaces(name, num_layers, num_spaces_per_layer):
        rack, created = Rack.objects.get_or_create(name=name)
        for layer_number in range(1, num_layers + 1):
            layer, _ = Layer.objects.get_or_create(rack=rack, layer_number=layer_number)
            for space_number in range(1, num_spaces_per_layer + 1):
                Space.objects.get_or_create(layer=layer, space_number=space_number)
        return rack

class Layer(models.Model):
    rack = models.ForeignKey(Rack, related_name='layers', on_delete=models.CASCADE)
    layer_number = models.IntegerField()

    def __str__(self):
        return f'Rack {self.rack.name} - Layer {self.layer_number}'

class Space(models.Model):
    layer = models.ForeignKey(Layer, related_name='spaces', on_delete=models.CASCADE)
    space_number = models.IntegerField()

    def __str__(self):
        return f'Layer {self.layer.layer_number} - Space {self.space_number}'

class Location(models.Model):
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE)
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE)
    space = models.ForeignKey(Space, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['rack', 'layer', 'space'], name='unique_location_rack_layer_space')
        ]

    def __str__(self):
        return f'Rack {self.rack.name} - Layer {self.layer.layer_number} - Space {self.space.space_number}'

class Status(models.Model):
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
        default=False, 
        help_text="Indicates if the task can be skipped"
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

    def __str__(self):
        return f'{self.status.name} - {self.task.action}'

class Product(models.Model):
    PRIORITY_LEVEL_CHOICES = [
        ('normal', 'Normal'),
        ('hot', 'Hot'),
        ('zfa', 'ZFA')
    ]

    SN = models.CharField(
        primary_key= True,
        max_length=13,
        unique=True,
        validators=[
            RegexValidator(
                regex='^\d{13}$',
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
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['SN'], name='unique_sn'),
            models.CheckConstraint(check=models.Q(SN__regex=r'^\d{13}$'), name='check_sn_digits'),
            models.UniqueConstraint(fields=['location'], name='unique_location')
        ]

    def __str__(self):
        current_task_action = self.tasks.filter(producttask__is_completed=False).first().action if self.tasks.filter(producttask__is_completed=False).exists() else "No ongoing task"
        return f'Product SN: {self.SN} | Priority: {self.get_priority_level_display()} | Current Status: {self.status.name} | Action: {current_task_action}'

    def save(self, *args, **kwargs):
        is_new = not self.pk
        previous_status = None
        if not is_new:
            previous_status = Product.objects.get(pk=self.pk).status

        super().save(*args, **kwargs)

        if is_new or previous_status != self.status:
            self.assign_tasks_for_status()

    def assign_tasks_for_status(self):
        # Fetch predefined tasks from the StatusTask model
        status_tasks = StatusTask.objects.filter(status=self.status)

        for status_task in status_tasks:
            task = status_task.task
            # Allow the same task to be added multiple times
            ProductTask.objects.create(product=self, task=task, is_default=True, timestamp=timezone.now())

    def add_non_required_task(self, task):
        # Allow the same task to be added multiple times
        ProductTask.objects.create(product=self, task=task, is_default=False, timestamp=timezone.now())

    def get_next_statuses(self):
        return self.status.possible_next_statuses.all()

    def assign_location(self, rack, layer, space):
        location, created = Location.objects.get_or_create(rack=rack, layer=layer, space=space)
        if Product.objects.filter(location=location).exclude(pk=self.pk).exists():
            raise ValueError(f"Location {location} is already occupied by another product.")
        self.location = location
        self.save()

    def assign_location_by_numbers(self, rack_name, layer_number, space_number):
        rack, created = Rack.objects.get_or_create(name=rack_name)
        layer, created = Layer.objects.get_or_create(rack=rack, layer_number=layer_number)
        space, created = Space.objects.get_or_create(layer=layer, space_number=space_number)
        
        self.assign_location(rack, layer, space)

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
        status_results = ResultOfStatus.objects.filter(product=self).order_by('created_at')
        history = []
        for result in status_results:
            tasks = self.tasks.filter(producttask__status=result.status).order_by('producttask__created_at')
            task_details = [
                {
                    "action": task.action,
                    "result": task.result,
                    "created_at": task.producttask_set.get(product=self).created_at
                }
                for task in tasks
            ]
            history.append({
                "status": result.status.name,
                "summary_result": result.summary_result,
                "tasks": task_details
            })
        return history

class ProductTask(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    is_default = models.BooleanField(default=True, help_text="Indicates if the task was added automatically")
    timestamp = models.DateTimeField(default=timezone.now, editable=False)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):
        return f'{self.product.SN} - {self.task.action} (UUID: {self.unique_id})'


class ResultOfStatus(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='status_results')
    status = models.ForeignKey(Status, on_delete=models.CASCADE, related_name='status_results')
    summary_result = models.TextField(blank=True, null=True, help_text="Summary of the results for this status")
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    unique_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)


    def __str__(self):
        return f'{self.product.SN} - {self.status.name} Result'



  
