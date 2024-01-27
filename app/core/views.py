from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import (
    JsonResponse,
    Http404,
    HttpResponseNotFound,
)
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import DeleteView

from core.forms import *
from core.models import *
from user.forms import RegisterClientForm
from .utils import *


class AjaxGetStationsView(View):
    """
    Ajax View for getting stations relatively to the selected city
    """

    def get(self, request):
        """
        Handle GET requests and return a JSON response with a list of stations.
        """
        city_id = request.GET.get("city_id")
        stations = Station.objects.filter(city_id=city_id)
        station_list = [
            {
                "id": station.id,
                "text": f"{station.station}, {station.street_type} {station.street}, {station.number}, {station.city.city}, {station.city.region} {_('область')}, {station.city.country}",
            }
            for station in stations
        ]
        return JsonResponse({"results": station_list})


def home_page(request):
    """
    View for the home page.
    Handles the logic for displaying and processing the city selection form to find available trips.
    """
    queryset = None
    context = {"title": "BusEnjoyer"}

    if request.method == "POST":
        form = CitySelectionForm(request.POST)
        if form.is_valid():
            start_point = form.cleaned_data["start_point"]
            end_point = form.cleaned_data["end_point"]
            date = form.cleaned_data["date"]
            passengers_quantity = form.cleaned_data["passengers_quantity"]
            request.session["passengers_quantity"] = passengers_quantity
            request.session["start_point"] = start_point.pk
            request.session["end_point"] = end_point.pk
            request.session["date"] = str(date)
            current_time = datetime.now().time()
            context.update(
                {
                    "start_point": start_point,
                    "end_point": end_point,
                    "date": date,
                    "title": _(f"{start_point.city} - {end_point.city}"),
                }
            )
            if date == datetime.now().date():
                queryset = Trip.objects.filter(
                    start_point=start_point,
                    end_point=end_point,
                    timedate_departure__date=date,
                    timedate_departure__time__gt=current_time,
                )
            else:
                queryset = Trip.objects.filter(
                    start_point=start_point,
                    end_point=end_point,
                    timedate_departure__date=date,
                )
            for trip in queryset:
                sold_tickets_count = Ticket.objects.filter(
                    trip=trip, returned=False
                ).count()
                remaining_seats = trip.bus.number_of_seats - sold_tickets_count
                trip.remaining_seats = remaining_seats
                trip.price = trip.price * passengers_quantity
            queryset = [
                trip for trip in queryset if trip.remaining_seats >= passengers_quantity
            ]
    else:
        passengers_quantity = request.session.get("passengers_quantity", None)
        start_point = request.session.get("start_point", None)
        end_point = request.session.get("end_point", None)
        date = (
            request.session.get("date")
            if request.session.get("date")
            and request.session.get("date") >= str(timezone.now().date())
            else str(timezone.now().date())
        )

        if passengers_quantity and start_point and end_point and date:
            form = CitySelectionForm(
                initial={
                    "date": date,
                    "passengers_quantity": passengers_quantity,
                    "start_point": start_point,
                    "end_point": end_point,
                }
            )
        else:
            form = CitySelectionForm()

    context.update(
        {
            "form": form,
            "queryset": queryset,
        }
    )

    return render(request, "core/index.html", context=context)


def checkout(request, trip_pk):
    """
    View for handling the checkout process.
    Handles the logic for processing ticket purchases, including user authentication if user is unauthenticated,
    form validation, and creating Ticket objects.
    """
    trip = Trip.objects.get(pk=trip_pk)
    passengers_quantity = request.session.get("passengers_quantity", 1)
    available_seats = (
        trip.bus.number_of_seats
        - Ticket.objects.filter(trip=trip, returned=False).count()
    )
    price = trip.price * passengers_quantity
    if trip.timedate_departure < timezone.now():
        return HttpResponseNotFound()

    if available_seats < passengers_quantity:
        raise PermissionDenied("Not enough available seats")

    if request.method == "POST":
        passenger_forms = [
            PassagerInfoForm(request.POST, prefix=f"passenger_{i}")
            for i in range(passengers_quantity)
        ]
        if not request.user.is_authenticated:
            buyer_form = RegisterClientForm(request.POST)
            if buyer_form.is_valid() and all(
                form.is_valid() for form in passenger_forms
            ):
                new_user = buyer_form.save()

                for i, form in enumerate(passenger_forms):
                    ticket_data = form.cleaned_data  # first_name, last_name
                    ticket_data["user"] = new_user
                    ticket_data["trip_id"] = trip_pk
                    Ticket.objects.create(**ticket_data)

                user = authenticate(
                    request,
                    username=new_user.phone,
                    password=buyer_form.cleaned_data["password1"],
                )
                login(request, user)

        else:
            if all(form.is_valid() for form in passenger_forms):
                for i, form in enumerate(passenger_forms):
                    ticket_data = form.cleaned_data  # first_name, last_name
                    ticket_data["user"] = request.user
                    ticket_data["trip_id"] = trip_pk
                    Ticket.objects.create(**ticket_data)

        return redirect("user:profile")

    else:
        if not request.user.is_authenticated:
            buyer_form = RegisterClientForm()
        else:
            buyer_form = None
        passenger_forms = [
            PassagerInfoForm(prefix=f"passenger_{i}")
            for i in range(passengers_quantity)
        ]

    return render(
        request,
        "checkout.html",
        context={
            "buyer_form": buyer_form,
            "passenger_forms": passenger_forms,
            "title": _("Сплата"),
            "trip": trip,
            "price": price,
        },
    )


def pageForbidden(request, exception):
    """
    View for handling forbidden (403) requests.
    """
    return render(request, "403.html", status=403)


def pageNotFound(request, exception):
    """
    View for handling not found (404) requests.
    """
    return render(request, "404.html", status=404)
