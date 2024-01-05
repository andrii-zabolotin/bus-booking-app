from datetime import datetime, date
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import *
from phonenumber_field.formfields import PhoneNumberField


class BuyerInfoForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        widget=forms.TextInput(attrs={"placeholder": ("email@gmail.com")}),
    )
    phone = PhoneNumberField(
        label=_("Телефон"),
        widget=forms.TextInput(attrs={"placeholder": ("+380 __ ___ __ __")}),
    )


class PassagerInfoForm(forms.Form):
    first_name = forms.CharField(label=_("Ім'я"))
    last_name = forms.CharField(label=_("Фамілія"))


class CitySelectionForm(forms.Form):
    start_point = forms.ModelChoiceField(
        queryset=City.objects.all(),
        label=_("Звідки"),
        empty_label=_("Виберіть місто"),
        widget=forms.Select(attrs={"class": "form-select", "id": "floatingSelect"}),
    )
    end_point = forms.ModelChoiceField(
        queryset=City.objects.all(),
        label=_("Куди"),
        empty_label=_("Виберіть місто"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    date = forms.DateField(
        label=_("Дата поїздки"),
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control datepicker",
                "id": "floatingInputGrid",
                "min": datetime.now().date(),
                "value": datetime.now().strftime("%Y-%m-%d"),
            }
        ),
    )
    passengers_quantity = forms.IntegerField(
        label=_("Кількість пасажирів"),
        min_value=0,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "type": "number",
                "class": "form-control number-input",
                "id": "floatingInputGrid",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        start_point = cleaned_data.get("start_point")
        end_point = cleaned_data.get("end_point")

        if start_point == end_point:
            raise ValidationError(
                _("Початковий та кінцевий пункти мають бути різними.")
            )

        return cleaned_data


# class TicketPurchase(forms.ModelForm):
#     class Meta:
#         model = Ticket
#         fields = ("first_name", "last_name", "email", "phone")
