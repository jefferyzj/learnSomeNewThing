from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Rack(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Layer(models.Model):
    rack = models.ForeignKey(Rack, related_name='layers', on_delete=models.CASCADE)
    layer_number = models.IntegerField()

    def __str__(self):
        return f'Rack {self.rack.name} - Layer {self.layer_number}'

class Position(models.Model):
    layer = models.ForeignKey(Layer, related_name='positions', on_delete=models.CASCADE)
    position_number = models.IntegerField()

    def __str__(self):
        return f'Layer {self.layer.layer_number} - Position {self.position_number}'

class Status(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Task(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    can_be_skipped = models.BooleanField(default=False)  # Indicates if the task can be skipped
    completion_result = models.CharField(max_length=50, choices=[('no_detection', 'No Detection'), ('test_done', 'Test Done')], null=True, blank=True)  # To capture task results

    def __str__(self):
        return self.name

class StatusTask(models.Model):
    status = models.ForeignKey(Status, related_name='status_tasks', on_delete=models.CASCADE)
    task = models.ForeignKey(Task, related_name='task_statuses', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.status.name} - {self.task.name}'

class Product(models.Model):
    SN = models.CharField(max_length=100, unique=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    is_hot = models.BooleanField(default=False)
    is_damaged = models.BooleanField(default=False)
    damage_description = models.TextField(blank=True, null=True)
    status = models.ForeignKey(Status, related_name='products', on_delete=models.CASCADE)
    position = models.ForeignKey(Position, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    tasks = models.ManyToManyField(Task, through='ProductTask')

    def __str__(self):
        return self.SN

    def save(self, *args, **kwargs):
        is_new = not self.pk
        previous_status = None
        if not is_new:
            previous_status = Product.objects.get(pk=self.pk).status
        
        super().save(*args, **kwargs)

        if is_new or previous_status != self.status:
            self.assign_tasks_for_status()

    def assign_tasks_for_status(self):
        self.tasks.clear()
        status_tasks = Task.objects.filter(status_tasks__status=self.status)
        for task in status_tasks:
            ProductTask.objects.create(product=self, task=task)

    def update_status_if_tasks_completed(self):
        if not self.tasks.filter(producttask__is_completed=False, task__can_be_skipped=False).exists():
            next_status = self.get_next_status()
            if next_status:
                self.status = next_status
                super().save()

    def get_next_status(self):
        current_status = self.status
        next_status = Status.objects.filter(id__gt=current_status.id).order_by('id').first()
        return next_status

class ProductTask(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    result = models.CharField(max_length=50, choices=[('no_detection', 'No Detection'), ('test_done', 'Test Done')], null=True, blank=True)  # Task result

    def __str__(self):
        return f'{self.product.SN} - {self.task.name}'
