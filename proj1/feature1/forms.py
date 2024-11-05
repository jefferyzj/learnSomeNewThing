from django import forms
from .models import Product, Position

class ProductForm(forms.ModelForm): 
    class Meta: 
        model = Product 
        fields = ['SN', 'category', 'is_hot', 'is_damaged', 'damage_description', 'process_status', 'position']

    def clean(self):
        cleaned_data = super().clean()
        process_status = cleaned_data.get('process_status')
        position = cleaned_data.get('position')

        if process_status != 'basic_check' and position is not None:
            raise forms.ValidationError("Position can only be set during the 'Under Basic Check' process.")
        
        return cleaned_data

class MoveProductForm(forms.ModelForm):
    new_position = forms.ModelChoiceField(queryset=Position.objects.all(), required=True)

    class Meta:
        model = Product
        fields = ['SN', 'category', 'is_hot', 'is_damaged', 'damage_description', 'process_status', 'position']

    def clean(self):
        cleaned_data = super().clean()
        process_status = cleaned_data.get('process_status')
        new_position = cleaned_data.get('new_position')

        if process_status == 'basic_check' and new_position is None:
            raise forms.ValidationError("Position must be set during the 'Under Basic Check' process.")
        
        return cleaned_data
