from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from user.models import User


class Company(models.Model):
    class Meta:
        verbose_name = _("Перевізник")
        verbose_name_plural = _("Перевізники")

    company_name = models.CharField(max_length=255, verbose_name=_("Назва компанії"))
    slug = models.SlugField(unique=True, db_index=True)

    def __str__(self):
        return self.company_name


class City(models.Model):
    class Meta:
        verbose_name = _("Місто")
        verbose_name_plural = _("Міста")

    city = models.CharField(max_length=255, verbose_name=_("Місто"))
    region = models.CharField(max_length=255, verbose_name=_("Область"))
    country = models.CharField(max_length=255, verbose_name=_("Країна"))

    def __str__(self):
        return f"{self.city}, {self.region} область, {self.country}"


class Station(models.Model):
    class Meta:
        verbose_name = _("Станція")
        verbose_name_plural = _("Станції")

    station = models.CharField(max_length=255, verbose_name=_("Станція"))
    street_type = models.CharField(
        max_length=255, verbose_name=_("Вулиця/Провулок...."), null=True
    )
    street = models.CharField(max_length=255, verbose_name=_("Назва"), null=True)
    number = models.CharField(null=True, max_length=255)
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, verbose_name=_("Місто"), null=True
    )

    def __str__(self):
        return f"{self.station}, {self.street_type} {self.street}, {self.number}, {self.city.city}, {self.city.region} {_('область')}, {self.city.country}"


class Buyer(models.Model):
    class Meta:
        verbose_name = _("Покупець")
        verbose_name_plural = _("Покупці")

    phone = PhoneNumberField(verbose_name=_("Номер телефону"))
    email = models.EmailField(max_length=255, verbose_name=_("E-mail"))


class Partner(models.Model):
    class Meta:
        verbose_name = _("Партнер")
        verbose_name_plural = _("Партнери")

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, verbose_name=_("Компанія")
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_("Користувач")
    )

    def __str__(self):
        return f"{self.company} {self.user.phone}"


class Bus(models.Model):
    class Meta:
        verbose_name = _("Автобус")
        verbose_name_plural = _("Автобуси")

    licence_plate = models.CharField(
        max_length=255, verbose_name=_("Реєстраційний номер"), unique=True
    )
    number_of_seats = models.IntegerField(verbose_name=_("Кількість місць"))
    brand = models.CharField(max_length=255, verbose_name=_("Опис"))
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, verbose_name=_("Компанія")
    )

    def __str__(self):
        return f"{self.licence_plate}, {self.company}, {self.brand}"


class Trip(models.Model):
    class Meta:
        verbose_name = _("Подорож")
        verbose_name_plural = _("Подорожі")

    timedate_departure = models.DateTimeField(verbose_name=_("Час/Дата відправки"))
    timedate_arrival = models.DateTimeField(verbose_name=_("Час/Дата приїзду"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    price = models.IntegerField(verbose_name=_("Ціна"))
    bus = models.ForeignKey(Bus, on_delete=models.PROTECT, verbose_name=_("Автобус"))
    departure_station = models.ForeignKey(
        Station,
        on_delete=models.PROTECT,
        related_name="departure_station",
        verbose_name=_("Станція відправки"),
    )
    arrival_station = models.ForeignKey(
        Station,
        on_delete=models.PROTECT,
        related_name="arrival_station",
        verbose_name=_("Станція приїзду"),
    )
    start_point = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        verbose_name=_("Місто відправки"),
        related_name="start_point_city",
    )
    end_point = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        verbose_name=_("Точка призначення"),
        related_name="end_point_city",
    )

    def __str__(self):
        return f"{self.timedate_departure.date()} {self.timedate_departure.time().strftime('%H:%M')} {self.bus} ({self.start_point} - {self.end_point})"

    def get_absolute_url(self):
        return reverse("partner:trip_update", kwargs={"trip_pk": self.pk})


class Ticket(models.Model):
    class Meta:
        verbose_name = _("Білет")
        verbose_name_plural = _("Білети")

    first_name = models.CharField(max_length=255, blank=False, verbose_name=_("Ім'я"))
    last_name = models.CharField(max_length=255, blank=False, verbose_name=_("Фамілія"))
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_("Користувач")
    )
    trip = models.ForeignKey(Trip, on_delete=models.PROTECT, verbose_name=_("Поездка"))
    purchase_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Дата покупки")
    )
    returned = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.user.phone}, {self.trip.start_point} - {self.trip.end_point}"
