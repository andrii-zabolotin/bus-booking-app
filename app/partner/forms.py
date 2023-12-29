from django import forms
from django.utils.translation import gettext_lazy as _

from core.models import Bus, Company, Trip, Station, City


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ("company_name",)


class CreateBusForm(forms.ModelForm):
    brand = forms.CharField(
        max_length=255,
        label=_("Опис"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "floatingSelect",
            }
        ),
    )
    number_of_seats = forms.IntegerField(
        label=_("Кількість місць"),
        min_value=1,
        max_value=100,
        initial=1,
        widget=forms.NumberInput(
            attrs={
                "type": "number",
                "class": "form-control number-input",
                "id": "floatingSelect",
            }
        ),
    )
    licence_plate = forms.CharField(
        label=_("Реєстраційний номер"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "id": "floatingSelect",
            }
        ),
    )

    class Meta:
        model = Bus
        fields = ("licence_plate", "number_of_seats", "brand")


class CreateTripForm(forms.ModelForm):
    timedate_departure = forms.DateTimeField(
        label=_("Дата/Час відправки"),
        widget=forms.DateInput(
            attrs={
                "type": "datetime-local",
                "class": "form-control",
                "id": "floatingSelect",
            }
        ),
    )
    timedate_arrival = forms.DateTimeField(
        label=_("Дата/Час приїзду"),
        widget=forms.DateInput(
            attrs={
                "type": "datetime-local",
                "class": "form-control",
                "id": "floatingSelect",
            }
        ),
    )
    price = forms.IntegerField(
        label=_("Ціна"),
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "id": "floatingSelect",
            }
        ),
    )
    departure_station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        label=_("Станція відправки"),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "floatingSelect",
            }
        ),
    )
    arrival_station = forms.ModelChoiceField(
        queryset=Station.objects.all(),
        label=_("Станція прибуття"),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "floatingSelect",
            }
        ),
    )
    start_point = forms.ModelChoiceField(
        queryset=City.objects.all(),
        label=_("Місто відправки"),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "floatingSelect",
            }
        ),
    )
    end_point = forms.ModelChoiceField(
        queryset=City.objects.all(),
        label=_("Місто прибуття"),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "floatingSelect",
            }
        ),
    )

    class Meta:
        model = Trip
        fields = "__all__"

    def __init__(self, user, *args, **kwargs):
        super(CreateTripForm, self).__init__(*args, **kwargs)
        self.fields["bus"].queryset = Bus.objects.select_related("company").filter(
            company__partner__user=user
        )
        self.fields["bus"].widget.attrs.update(
            {
                "class": "form-control",
                "id": "floatingSelect",
            }
        )
