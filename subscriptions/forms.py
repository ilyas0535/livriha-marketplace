from django import forms

class PaymentForm(forms.Form):
    binance_user = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Binance username'
        })
    )
    binance_email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Binance email'
        })
    )
    payment_confirmed = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='I confirm that I have sent the payment via Binance Pay'
    )