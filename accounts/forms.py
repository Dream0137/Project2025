from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    name = forms.CharField(max_length=255)

    class Meta:
        model = User
        fields = ('username', 'name', 'email', 'password1', 'password2')


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Username")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["name", "email"]
        labels = {
            "name": "ชื่อที่แสดง",
            "email": "อีเมล",
        }
