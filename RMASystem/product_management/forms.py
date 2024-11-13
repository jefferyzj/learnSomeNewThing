from django import forms
from .models import Product, Category, Rack, Layer, Space, Status, Task, ProductTask, StatusTask, Location

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']

class RackForm(forms.ModelForm):
    class Meta:
        model = Rack
        fields = ['name']

    def save(self, commit=True):
        rack = super().save(commit=commit)
        if commit:
            for layer_number in range(1, 7):  # Create 6 layers
                layer = Layer.objects.create(rack=rack, layer_number=layer_number)
                for space_number in range(1, 21):  # Create 20 spaces for each layer
                    Space.objects.create(layer=layer, space_number=space_number)
        return rack

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'description', 'can_be_skipped']

class StatusTaskForm(forms.ModelForm):
    class Meta:
        model = StatusTask
        fields = ['status', 'task']

class ProductForm(forms.ModelForm):
    rack = forms.ModelChoiceField(queryset=Rack.objects.all(), required=False)
    layer = forms.ModelChoiceField(queryset=Layer.objects.all(), required=False)
    space = forms.ModelChoiceField(queryset=Space.objects.all(), required=False)

    class Meta:
        model = Product
        fields = ['SN', 'category', 'is_hot', 'is_damaged', 'damage_description', 'status', 'rack', 'layer', 'space']

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

class ProductTaskForm(forms.ModelForm):
    class Meta:
        model = ProductTask
        fields = ['product', 'task', 'is_completed', 'result']
        widgets = {
            'result': forms.Select(choices=[('no_detection', 'No Detection'), ('test_done', 'Test Done')]),
        }
