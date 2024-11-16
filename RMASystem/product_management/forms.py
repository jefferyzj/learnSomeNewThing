from django import forms
from .models import Product, Category, Rack, Layer, Space, Status, Task, ProductTask, StatusTask

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class RackForm(forms.ModelForm):
    num_layers = forms.IntegerField(required=False, min_value=1, label="Number of Layers")
    num_spaces_per_layer = forms.IntegerField(required=False, min_value=1, label="Number of Spaces per Layer")

    class Meta:
        model = Rack
        fields = ['name']

    def save(self, commit=True):
        rack = super().save(commit=commit)
        if commit:
            num_layers = self.cleaned_data.get('num_layers')
            num_spaces_per_layer = self.cleaned_data.get('num_spaces_per_layer')
            if num_layers and num_spaces_per_layer:
                for layer_number in range(1, num_layers + 1):
                    layer = Layer.objects.create(rack=rack, layer_number=layer_number)
                    for space_number in range(1, num_spaces_per_layer + 1):
                        Space.objects.create(layer=layer, space_number=space_number)
        return rack

class LayerForm(forms.ModelForm):
    class Meta:
        model = Layer
        fields = ['rack', 'layer_number']

class SpaceForm(forms.ModelForm):
    class Meta:
        model = Space
        fields = ['layer', 'space_number']

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['action', 'description', 'can_be_skipped', 'note']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].widget = forms.Textarea(attrs={'rows': 3})
        self.fields['can_be_skipped'].widget = forms.CheckboxInput(attrs={'class': 'form-check-input'})
        self.fields['note'].widget = forms.Textarea(attrs={'rows': 3})

class StatusForm(forms.ModelForm):
    possible_next_statuses = forms.ModelMultipleChoiceField(
        queryset=Status.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Possible Next Statuses"
    )

    class Meta:
        model = Status
        fields = ['name', 'possible_next_statuses']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['possible_next_statuses'].initial = self.instance.possible_next_statuses.all()

    def save(self, commit=True):
        status = super().save(commit=False)
        if commit:
            status.save()
            self.save_m2m()
        return status

class StatusTaskForm(forms.ModelForm):
    class Meta:
        model = StatusTask
        fields = ['status', 'task']

class ProductTaskForm(forms.ModelForm):
    class Meta:
        model = ProductTask
        fields = ['product', 'task', 'is_completed']

class ProductForm(forms.ModelForm):
    rack = forms.ModelChoiceField(queryset=Rack.objects.all(), required=False)
    layer = forms.ModelChoiceField(queryset=Layer.objects.all(), required=False)
    space = forms.ModelChoiceField(queryset=Space.objects.all(), required=False)

    class Meta:
        model = Product
        fields = ['SN', 'category', 'priority_level', 'description', 'status', 'rack', 'layer', 'space']

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        rack = cleaned_data.get('rack')
        layer = cleaned_data.get('layer')
        space = cleaned_data.get('space')
        product = self.instance

        # Check if all required tasks are completed before changing the status
        if status != product.status:
            incomplete_tasks = product.tasks.filter(producttask__is_completed=False, task__can_be_skipped=False)
            if incomplete_tasks.exists():
                raise forms.ValidationError("All required tasks must be completed or removed before changing the status.")

        return cleaned_data

    def save(self, commit=True):
        product = super().save(commit=False)
        rack = self.cleaned_data.get('rack')
        layer = self.cleaned_data.get('layer')
        space = self.cleaned_data.get('space')

        if rack and layer and space:
            try:
                product.assign_location(rack, layer, space)
            except ValueError as e:
                self.add_error('space', str(e))

        if commit:
            product.save()
        return product
