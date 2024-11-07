from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Rack(models.Model):
    number = models.IntegerField(unique=True, default=1)

    def __str__(self):
        return f"Rack {self.number}"

class Layer(models.Model):
    rack = models.ForeignKey(Rack, on_delete=models.CASCADE)
    number = models.IntegerField(default=1)

    class Meta:
        unique_together = ('rack', 'number')

    def __str__(self):
        return f"Rack {self.rack.number} - Layer {self.number}"

class Position(models.Model):
    layer = models.ForeignKey(Layer, on_delete=models.CASCADE)
    number = models.IntegerField(default=1)

    class Meta:
        unique_together = ('layer', 'number')

    def __str__(self):
        return f"Rack {self.layer.rack.number} - Layer {self.layer.number} - Position {self.number}"

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('PG520', 'PG520'),
        ('PG530', 'PG530')
    ]

    SN = models.CharField(max_length=100, unique=True, default="0000000000000")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='PG520')
    is_hot = models.BooleanField(default=False)
    is_damaged = models.BooleanField(default=False)
    damage_description = models.TextField(blank=True, null=True)
    PROCESS_CHOICES = [
        ('sorting_test', 'Under Sorting Test'),
        ('basic_check', 'Under Basic Check'),
        ('fa_lab', 'To FA Lab'),
    ]
    process_status = models.CharField(max_length=20, choices=PROCESS_CHOICES, default='sorting_test')
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.process_status != 'basic_check':
            self.position = None
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.SN
