from django import forms
from .models import Product, Position, Category, Rack, Layer

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

class ProductForm(forms.ModelForm):
    new_position = forms.ModelChoiceField(queryset=Position.objects.all(), required=False)

    class Meta:
        model = Product
        fields = ['SN', 'category', 'is_hot', 'is_damaged', 'damage_description', 'process_status', 'position', 'new_position']

    def clean(self):
        cleaned_data = super().clean()
        process_status = cleaned_data.get('process_status')
        position = cleaned_data.get('position')
        new_position = cleaned_data.get('new_position')

        if process_status == 'basic_check' and new_position is None:
            raise forms.ValidationError("Position must be set during the 'Under Basic Check' process.")
        
        if process_status != 'basic_check' and new_position is not None:
            raise forms.ValidationError("Position can only be set during the 'Under Basic Check' process.")
        
        return cleaned_data
