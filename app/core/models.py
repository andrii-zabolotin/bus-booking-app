from django.db import models
from django.utils.translation import gettext as _

from user.models import User


class Company(models.Model):
    company_name = models.CharField(max_length=255, verbose_name=_("Назва компанії"))
    slug = models.SlugField(unique=True, db_index=True)


class Brand(models.Model):
    brand = models.CharField(max_length=255, verbose_name=_("Марка авто"))


class Station(models.Model):
    station = models.CharField(max_length=255, verbose_name=_("Станція"))


class City(models.Model):
    city = models.CharField(max_length=255, verbose_name=_("Місто"))
    region = models.CharField(max_length=255, verbose_name=_("Область"))
    country = models.CharField(max_length=255, verbose_name=_("Країна"))


class Partner(models.Model):
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, verbose_name=_("Компанія")
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_("Користувач")
    )


class Bus(models.Model):
    licence_plate = models.CharField(
        max_length=255, verbose_name=_("Реєстраційний номер")
    )
    number_of_seats = models.IntegerField(verbose_name=_("Кількість місць"))
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, verbose_name=_("Марка"))
    company = models.ForeignKey(
        Company, on_delete=models.PROTECT, verbose_name=_("Компанія")
    )


class Trip(models.Model):
    timedate_departure = models.TimeField(verbose_name=_("Час/Дата відправки"))
    timedate_arrival = models.TimeField(verbose_name=_("Час/Дата приїзду"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
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
        verbose_name="Город отправки",
        related_name="start_point_city",
    )
    end_point = models.ForeignKey(
        City,
        on_delete=models.PROTECT,
        verbose_name="Точка назначения",
        related_name="end_point_city",
    )


class Ticket(models.Model):
    first_name = models.CharField(max_length=255, blank=False, verbose_name=_("Ім'я"))
    last_name = models.CharField(max_length=255, blank=False, verbose_name=_("Фамілія"))
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_("Пользователь")
    )
    trip = models.ForeignKey(Trip, on_delete=models.PROTECT, verbose_name=_("Поездка"))
    purchase_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Дата покупки")
    )
