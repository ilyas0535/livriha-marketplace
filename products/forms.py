from django import forms
from .models import Product, ProductImage

class ProductForm(forms.ModelForm):
    images = forms.FileField(
        widget=forms.FileInput(attrs={'multiple': True}),
        required=False,
        help_text='Select multiple images for your product'
    )
    
    class Meta:
        model = Product
        fields = ['name', 'description', 'category', 'price', 'old_price', 'quantity', 'low_stock_threshold']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'old_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'low_stock_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']