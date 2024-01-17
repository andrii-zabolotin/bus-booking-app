from datetime import datetime

from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Sum, Min, Max, Prefetch
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from slugify import slugify
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, CreateView, UpdateView
from django.contrib.auth.decorators import login_required

from core.models import Company, Bus, Partner, Trip, Ticket
from core.utils import PartnerRequiredMixin
from partner.forms import CreateBusForm, CompanyForm, CreateUpdateTripForm
from user.forms import RegisterClientForm


@transaction.atomic
def partner_registration(request):
    """
    View for handling partner registration.
    Handles the registration process for partners, including creating a new user,
    associating them with a company, and logging them in.
    """
    if request.method == "POST":
        user_form = RegisterClientForm(request.POST)
        company_form = CompanyForm(request.POST)
        if user_form.is_valid() and company_form.is_valid():
            try:
                user = user_form.save(commit=False)
                user.is_partner = True
                user.save()
                company = company_form.save(commit=False)
                company.slug = slugify(company.company_name)
                company.save()
                Partner.objects.create(user=user, company=company)
                login(request, user)
                return redirect("partner:profile")
            except Exception as e:
                print(f"Error during registration: {e}")
                messages.error(
                    request, "An error occurred during registration. Please try again."
                )
                transaction.set_rollback(True)
    else:
        user_form = RegisterClientForm()
        company_form = CompanyForm()

    return render(
        request,
        "partner/registration.html",
        context={"user_form": user_form, "company_form": company_form},
    )


@transaction.atomic
def partner_subaccount_registration(request):
    """
    View for handling partner sub-account registration.
    Handles the registration process for partners, including creating a new user,
    associating them with a company, and logging them in.
    """
    if request.method == "POST":
        user_form = RegisterClientForm(request.POST)
        if user_form.is_valid():
            try:
                user = user_form.save(commit=False)
                user.is_partner = True
                user.is_sub_account = True
                user.save()
                Partner.objects.create(
                    user=user,
                    company=Company.objects.get(partner__user=request.user),
                )
                return redirect("partner:sub_accounts")
            except Exception as e:
                print(f"Error during registration: {e}")
                messages.error(
                    request, "An error occurred during registration. Please try again."
                )
                transaction.set_rollback(True)
    else:
        user_form = RegisterClientForm()

    return render(
        request,
        "partner/sub_account_registration.html",
        context={"user_form": user_form},
    )


class PartnerProfileView(PartnerRequiredMixin, View):
    """
    View for displaying the partner's profile information.
    This view requires the user to be logged in as a partner. It retrieves the associated
    company based on the logged-in user and renders the partner's profile page.
    """

    template_name = "partner/profile.html"

    def get(self, request):
        company = Company.objects.get(partner__user=request.user)
        return render(
            request,
            "partner/profile.html",
            context={
                "company": company,
                "active_tab": "profile",
                "title": _("Контактна інформація"),
            },
        )


class BusView(PartnerRequiredMixin, ListView):
    """
    View for displaying a list of buses along with additional statistics.
    This view requires the user to be logged in as a partner and provides information about each bus,
    including revenue, ticket prices, and trip counts.

    Methods:
        get_queryset(self): Retrieve the queryset of buses associated with the logged-in partner.
        get_context_data(self, **kwargs): Add additional context data to be used in the template.

        get_revenue_dict(self, bus_list): Calculate revenue for each bus in the provided list.
        add_revenue_to_bus(self, bus_list): Add revenue information to each bus in the list.

        get_ticket_price_dict(self, bus_list): Calculate ticket price statistics for each bus.
        add_ticket_price_to_bus(self, bus_list): Add ticket price information to each bus in the list.

        get_past_trip_count_dict(self, bus_list): Calculate past trip counts for each bus.
        get_future_trip_count_dict(self, bus_list): Calculate future trip counts for each bus.
        add_trip_counts_to_bus(self, bus_list): Add trip count information to each bus in the list.
    """

    model = Bus
    template_name = "partner/bus.html"
    context_object_name = "bus_list"

    def get_queryset(self):
        return Bus.objects.select_related("company").filter(
            company__partner__user=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "bus"

        bus_list = context["bus_list"]
        self.add_trip_counts_to_bus(bus_list)
        self.add_ticket_price_to_bus(bus_list)
        self.add_revenue_to_bus(bus_list)

        return context

    def get_revenue_dict(self, bus_list):
        """
        Calculate revenue for each bus in the provided list.
        Returns dictionary with bus primary key as key and revenue as value
        """
        return {
            bus.pk: Ticket.objects.filter(
                trip__bus=bus, trip__timedate_departure__lt=timezone.now()
            ).aggregate(Sum("trip__price"))["trip__price__sum"]
            or 0
            for bus in bus_list
        }

    def add_revenue_to_bus(self, bus_list):
        """
        Add revenue information to each bus in the list.
        """
        revenue_dict = self.get_revenue_dict(bus_list)

        for bus in bus_list:
            bus.revenue = revenue_dict[bus.pk]

    def get_ticket_price_dict(self, bus_list):
        """
        Method returns dictionary with information about ticket prices statistics for each bus

        .values - tells Django to only retrieve certain fields from the model.
        .annotate - method allows to aggregate data based on the values in each group.

        Trip.objects.filter... returns a QuerySet containing all the company's buses
        """
        return {
            bus["bus"]: {
                "ticket_price_sum": bus["ticket_price_sum"],
                "trip_count": bus["trip_count"],
                "min_ticket_price": bus["min_ticket_price"],
                "max_ticket_price": bus["max_ticket_price"],
            }
            for bus in Trip.objects.filter(
                bus__in=bus_list, timedate_departure__lt=datetime.now()
            )
            .values("bus")
            .annotate(
                ticket_price_sum=Sum("price"),
                trip_count=Count("id"),
                min_ticket_price=Min("price"),
                max_ticket_price=Max("price"),
            )
        }

    def add_ticket_price_to_bus(self, bus_list):
        """
        Add ticket price information to each bus in the list.
        """
        ticket_price_dict = self.get_ticket_price_dict(bus_list)

        for bus in bus_list:
            money_info = ticket_price_dict.get(bus.id, {})
            bus.average_ticket_price = money_info.get(
                "ticket_price_sum", 0
            ) / money_info.get("trip_count", 1)
            bus.min_ticket_price = money_info.get("min_ticket_price", 0)
            bus.max_ticket_price = money_info.get("max_ticket_price", 0)

    def get_past_trip_count_dict(self, bus_list):
        return {
            past_trip_counts["bus"]: past_trip_counts["trip_count"]
            for past_trip_counts in Trip.objects.filter(
                bus__in=bus_list, timedate_departure__lt=datetime.now()
            )
            .values("bus")
            .annotate(trip_count=Count("id"))
        }

    def get_future_trip_count_dict(self, bus_list):
        return {
            future_trip_counts["bus"]: future_trip_counts["trip_count"]
            for future_trip_counts in Trip.objects.filter(
                bus__in=bus_list, timedate_departure__gt=datetime.now()
            )
            .values("bus")
            .annotate(trip_count=Count("id"))
        }

    def add_trip_counts_to_bus(self, bus_list):
        past_trip_count_dict = self.get_past_trip_count_dict(bus_list)
        future_trip_count_dict = self.get_future_trip_count_dict(bus_list)

        for bus in bus_list:
            bus.trip_count = past_trip_count_dict.get(
                bus.id, 0
            ) + future_trip_count_dict.get(bus.id, 0)
            bus.future_trip_count = future_trip_count_dict.get(bus.id, 0)
            bus.past_trip_count = past_trip_count_dict.get(bus.id, 0)


class CreateBusView(PartnerRequiredMixin, CreateView):
    """
    View for creating a new bus.
    """

    form_class = CreateBusForm
    template_name = "bus_create.html"
    success_url = "/partner/buses/"

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.company = Company.objects.get(partner__user=self.request.user)
        obj.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "bus"
        return context


class TripBaseView(PartnerRequiredMixin, ListView):
    """
    Base view for displaying a list of trips with associated tickets.
    """

    model = Trip
    context_object_name = "trips_list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "trips"
        for trip in context["trips_list"]:
            trip.tickets = trip.ticket_set.filter(
                returned=False
            )  # reverse relationship
        return context


class FutureTripView(TripBaseView):
    """
    View for displaying a list of future trips.
    """

    template_name = "partner/future_trips.html"

    def get_queryset(self):
        return (
            Trip.objects.select_related("bus__company")
            .filter(
                bus__company__partner__user=self.request.user,
                timedate_departure__gt=datetime.now(),
            )
            .order_by("timedate_departure")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["edit"] = True
        return context


class PastTripView(TripBaseView):
    """
    View for displaying a list of past trips.
    """

    template_name = "partner/past_trips.html"

    def get_queryset(self):
        return (
            Trip.objects.select_related("bus__company")
            .filter(
                bus__company__partner__user=self.request.user,
                timedate_departure__lt=datetime.now(),
            )
            .order_by("-timedate_departure")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["edit"] = False
        return context


class CreateTripView(PartnerRequiredMixin, CreateView):
    """
    View for creating a new trip.
    """

    form_class = CreateUpdateTripForm
    template_name = "trip_create.html"
    success_url = "/partner/future_trips/"

    def form_invalid(self, form):
        # Выводим данные, переданные в форму, в консоль или логи
        print(form.data)
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "trips"
        return context


class UpdateTripView(PartnerRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating a trip.
    """

    model = Trip
    template_name = "partner/trip_update.html"
    form_class = CreateUpdateTripForm
    success_url = "/partner/future_trips/"
    pk_url_kwarg = "trip_pk"

    def test_func(self):
        trip = self.get_object()
        return (
            Company.objects.get(partner__user=self.request.user) == trip.bus.company
            and trip.timedate_departure > timezone.now()
        )

    def get_form_kwargs(self):
        """
        Pass arguments to the form's constructor
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class SubAccountsView(PartnerRequiredMixin, ListView):
    model = Partner
    template_name = "partner/sub_accounts.html"
    context_object_name = "sub_accounts"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_sub_account:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Partner.objects.filter(
            company=Company.objects.get(partner__user=self.request.user),
            user__is_sub_account=True,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "sub_accounts"
        return context
