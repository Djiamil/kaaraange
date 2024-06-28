from django import forms
from django import forms
from django.contrib.auth.forms import UserCreationForm
from api.models import *


class LoginForm(forms.Form):
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'})
    )

class AdminCreationForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    phone_number = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'})
    )
    prenom = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    nom = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control-file'})
    )

    class Meta:
        model = User
        fields = ['email', 'phone_number', 'prenom', 'nom', 'password1', 'password2', 'avatar']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.user_type = 'ADMIN'
        user.is_staff = True
        if self.cleaned_data['avatar']:
            user.avatar = self.cleaned_data['avatar']
        if commit:
            user.save()
        return user