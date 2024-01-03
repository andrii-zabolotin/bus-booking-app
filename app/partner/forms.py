from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from bootstrap_datepicker_plus.widgets import DateTimePickerInput

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


class CreateUpdateTripForm(forms.ModelForm):
    timedate_departure = forms.DateTimeField(
        label=_("Дата/Час відправки"),
        widget=DateTimePickerInput(
            attrs={
                "class": "form-control",
                "id": "floatingSelect",
            }
        ),
    )
    timedate_arrival = forms.DateTimeField(
        label=_("Дата/Час приїзду"),
        widget=DateTimePickerInput(
            attrs={
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
        fields = [
            "bus",
            "start_point",
            "departure_station",
            "timedate_departure",
            "end_point",
            "arrival_station",
            "timedate_arrival",
            "price",
        ]

    def __init__(self, user, *args, **kwargs):
        super(CreateUpdateTripForm, self).__init__(*args, **kwargs)
        self.fields["bus"].queryset = Bus.objects.select_related("company").filter(
            company__partner__user=user
        )
        self.fields["bus"].widget.attrs.update(
            {
                "class": "form-control",
                "id": "floatingSelect",
            }
        )

    def clean(self):
        cleaned_data = super().clean()
        timedate_departure = cleaned_data.get("timedate_departure")
        timedate_arrival = cleaned_data.get("timedate_arrival")
        departure_station = cleaned_data.get("departure_station")
        arrival_station = cleaned_data.get("arrival_station")
        end_point = cleaned_data.get("end_point")
        start_point = cleaned_data.get("start_point")
        price = cleaned_data.get("price")

        if timedate_departure >= timedate_arrival:
            raise ValidationError(
                _("Дата приїзду повинна бути більша ніж дата від'їзду")
            )

        if departure_station.city != start_point:
            raise ValidationError(
                _("Станція від'їзду повинна бути розташована в місті від'їзду")
            )

        if arrival_station.city != end_point:
            raise ValidationError(
                _("Станція приїзду повинна бути розташована в місті приїзду")
            )

        return cleaned_data
