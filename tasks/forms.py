from django import forms
from django.forms import ModelForm
from .models import Task
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from user.models import User

class createTaskForm(ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description']

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password1', 'password2']

class UserUpdateForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'dependencia']