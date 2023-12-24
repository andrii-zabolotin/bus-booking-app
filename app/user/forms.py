from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import User


class RegisterClientForm(UserCreationForm):
    class Meta:
        model = User
        fields = (
            "phone",
            "email",
            "password1",
            "password2",
        )

    password1 = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Повтор пароля", widget=forms.PasswordInput)


class AddEmailToUser(forms.ModelForm):
    class Meta:
        model = User
        fields = ["email"]
        widgets = {
            "email": forms.TextInput(
                attrs={"placeholder": "E-mail", "class": "form-control"}
            )
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email):
            raise ValidationError("Этот адрес электронной почты уже используется")
        return email
