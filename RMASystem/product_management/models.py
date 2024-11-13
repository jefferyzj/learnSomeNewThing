from django.db import models

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
        return f'Rack {self.rack.name} - Layer {self.layer.layer_number}'

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
        unique_together = ('rack', 'layer', 'space')

    def __str__(self):
        return f'Rack {self.rack.name} - Layer {self.layer.layer_number} - Space {self.space.space_number}'

class Status(models.Model):
    name = models.CharField(max_length=50)
    possible_next_statuses = models.ManyToManyField('self', blank=True, related_name='previous_statuses', symmetrical=False)

    def __str__(self):
        return self.name

class Task(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    can_be_skipped = models.BooleanField(default=False)

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
    tasks = models.ManyToManyField(Task, through='ProductTask')
    location = models.OneToOneField(Location, on_delete=models.CASCADE, related_name='product', null = True, blank=True)

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
        status_tasks = Task.objects.filter(status_tasks__status=self.status)
        for task in status_tasks:
            if not self.tasks.filter(pk=task.pk).exists():
                ProductTask.objects.create(product=self, task=task)

    def add_non_required_task(self, task):
        if not self.tasks.filter(pk=task.pk).exists():
            ProductTask.objects.create(product=self, task=task)

    def update_status_if_tasks_completed(self):
        if not self.tasks.filter(producttask__is_completed=False, task__can_be_skipped=False).exists():
            next_statuses = self.get_next_statuses()
            if next_statuses.count() == 1:
                self.status = next_statuses.first()
                super().save()

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

class ProductTask(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    result = models.CharField(max_length=50, choices=[('no_detection', 'No Detection'), ('test_done', 'Test Done')], null=True, blank=True)

    def __str__(self):
        return f'{self.product.SN} - {self.task.name}'
