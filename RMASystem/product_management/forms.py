from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Product, Category, Rack, Layer, Space, Status, Task, ProductTask, StatusTask

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class RackForm(forms.ModelForm):
    num_layers = forms.IntegerField(required=False, min_value=1, label="Number of Layers")
    num_spaces_per_layer = forms.IntegerField(required=False, min_value=1, label="Number of Spaces per Layer")

    class Meta:
        model = Rack
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class SpaceForm(forms.ModelForm):
    class Meta:
        model = Space
        fields = ['layer', 'space_number']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class StatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['action', 'description', 'can_be_skipped', 'result', 'note']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class ProductTaskForm(forms.ModelForm):
    class Meta:
        model = ProductTask
        fields = ['product', 'task', 'is_completed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class StatusTaskForm(forms.ModelForm):
    class Meta:
        model = StatusTask
        fields = ['status', 'task']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

class ProductForm(forms.ModelForm):
    rack = forms.ModelChoiceField(queryset=Rack.objects.all(), required=False)
    layer = forms.ModelChoiceField(queryset=Layer.objects.all(), required=False)
    space = forms.ModelChoiceField(queryset=Space.objects.all(), required=False)

    class Meta:
        model = Product
        fields = ['SN', 'category', 'priority_level', 'description', 'status', 'rack', 'layer', 'space']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

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
        if commit:
            product.save()
            self.save_m2m()
        return product