from django import forms
from .models import Product, Position, Category, Rack, Layer, Status, Task, ProductTask, StatusTask

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
                for position_number in range(1, 21):  # Create 20 positions for each layer
                    Position.objects.create(layer=layer, position_number=position_number)
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
    new_position = forms.ModelChoiceField(queryset=Position.objects.all(), required=False)

    class Meta:
        model = Product
        fields = ['SN', 'category', 'is_hot', 'is_damaged', 'damage_description', 'status', 'position', 'new_position']

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        position = cleaned_data.get('position')
        new_position = cleaned_data.get('new_position')
        product = self.instance

        if status != product.status:
            # Ensure all non-skippable tasks are completed or skipped before allowing status change
            incomplete_tasks = product.tasks.filter(producttask__is_completed=False, task__can_be_skipped=False)
            if incomplete_tasks.exists():
                raise forms.ValidationError("All required tasks must be completed or removed before changing the status.")

        if status and status.name == 'RMA sorting' and new_position is None:
            raise forms.ValidationError("Position must be set during the 'RMA sorting' process.")

        return cleaned_data

class ProductTaskForm(forms.ModelForm):
    class Meta:
        model = ProductTask
        fields = ['product', 'task', 'is_completed', 'result']
        widgets = {
            'result': forms.Select(choices=[('no_detection', 'No Detection'), ('test_done', 'Test Done')]),
        }
