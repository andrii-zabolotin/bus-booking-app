from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import User


class RegisterClientForm(UserCreationForm):
    phone = forms.CharField(
        label=_("Телефон"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
            }
        ),
    )

    email = forms.EmailField(
        label=_("E-mail"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
            }
        ),
    )

    password1 = forms.CharField(
        label=_("Пароль"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
            }
        ),
    )

    password2 = forms.CharField(
        label=_("Повтор паролю"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
            }
        ),
    )

    class Meta:
        model = User
        fields = (
            "phone",
            "email",
            "password1",
            "password2",
        )


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


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Номер телефону",
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
            }
        ),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
            }
        ),
    )
