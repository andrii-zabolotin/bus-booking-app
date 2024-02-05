from datetime import datetime

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, Sum, Min, Max
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from slugify import slugify
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, CreateView, UpdateView

from core.models import Company, Bus, Partner, Trip, Ticket, Station
from core.utils import PartnerRequiredMixin, FormInvalidMixin
from partner.forms import (
    CreateBusForm,
    CompanyForm,
    CreateUpdateTripForm,
    StationCreateFrom,
    TripSearchForm,
)
from user.forms import RegisterClientForm


@transaction.atomic
def partner_registration(request):
    """
    View for handling partner registration.

    This view processes the registration of a partner, which includes creating a new user,
    associating them with a company, and logging them in.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object.

    Raises:
        Exception: An error occurred during registration.

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
            for key, value in user_form.errors.items():
                if key != "__all__":
                    user_form.fields[key].widget.attrs[
                        "class"
                    ] = "form-control is-invalid"
            for key, value in company_form.errors.items():
                if key != "__all__":
                    company_form.fields[key].widget.attrs[
                        "class"
                    ] = "form-control is-invalid"

    else:
        user_form = RegisterClientForm()
        company_form = CompanyForm()

    return render(
        request,
        "partner/registration.html",
        context={
            "user_form": user_form,
            "company_form": company_form,
            "title": _("Реєстрація"),
        },
    )


@transaction.atomic
def partner_subaccount_registration(request):
    """
    View for handling partner sub-account registration.

    This view processes the registration of a partner sub-account, creating a new user
    associated with the same company as the logged-in partner.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The HTTP response object.

    Raises:
        Exception: An error occurred during registration.

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
            for key, value in user_form.errors.items():
                if key != "__all__":
                    user_form.fields[key].widget.attrs[
                        "class"
                    ] = "form-control is-invalid"
    else:
        user_form = RegisterClientForm()

    return render(
        request,
        "partner/sub_account_registration.html",
        context={"user_form": user_form, "title": _("Реєстрація")},
    )


class PartnerProfileView(PartnerRequiredMixin, View):
    """
    View for displaying the partner's profile information.

    This view requires the user to be logged in as a partner. It retrieves the associated
    company based on the logged-in user and renders the partner's profile page.

    Attributes:
        template_name (str): The template name for rendering the profile page.

    Methods:
        get(self, request): Handles GET requests to display the partner's profile page.

    """

    template_name = "partner/profile.html"

    def get(self, request):
        """
        Handles GET requests to display the partner's profile page.

        Args:
            request (HttpRequest): The HTTP request object.

        Returns:
            HttpResponse: The HTTP response object containing the partner's profile page.

        """
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

    Attributes:
        model (Model): The model associated with this view.
        template_name (str): The template name for rendering the bus list page.
        context_object_name (str): The context variable name for the list of buses.

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
        get_future_trip_dict(self, bus_list): Retrieve future trips for each bus in the provided list.
        add_future_trip_to_bus(self, bus_list): Add future trip information to each bus in the list.
        get_past_trip_dict(self, bus_list): Retrieve past trips for each bus in the provided list.
        add_past_trip_to_bus(self, bus_list): Add past trip information to each bus in the list.

    """

    model = Bus
    template_name = "partner/bus_list.html"
    context_object_name = "bus_list"

    def get_queryset(self):
        """
        Retrieve the queryset of buses associated with the logged-in partner.

        Returns:
            QuerySet: The queryset of buses associated with the logged-in partner.

        """
        licence_plate = self.request.GET.get("licence_plate", "")

        if licence_plate:
            return Bus.objects.select_related("company").filter(
                company__partner__user=self.request.user, licence_plate=licence_plate
            )
        return Bus.objects.select_related("company").filter(
            company__partner__user=self.request.user
        )

    def get_context_data(self, **kwargs):
        """
        Add additional context data to be used in the template.

        Returns:
            dict: Additional context data.
        """
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "bus"
        context["licence_plate_value"] = self.request.GET.get("licence_plate", "")
        context["title"] = _("Автобуси")

        bus_list = context["bus_list"]
        self.add_trip_counts_to_bus(bus_list)
        self.add_ticket_price_to_bus(bus_list)
        self.add_revenue_to_bus(bus_list)
        self.add_future_trip_to_bus(bus_list)
        self.add_past_trip_to_bus(bus_list)

        return context

    def get_future_trip_dict(self, bus_list):
        return {
            bus.pk: Trip.objects.filter(
                bus=bus, timedate_departure__gt=timezone.now()
            ).order_by("timedate_departure")
            for bus in bus_list
        }

    def add_future_trip_to_bus(self, bus_list):
        future_trip_dict = self.get_future_trip_dict(bus_list)

        for bus in bus_list:
            for trip in future_trip_dict[bus.pk]:
                bought_seats = Ticket.objects.filter(trip=trip, returned=False).count()
                trip.bought_seats = bought_seats
            bus.future_trips = future_trip_dict[bus.pk]

    def get_past_trip_dict(self, bus_list):
        return {
            bus.pk: Trip.objects.filter(
                bus=bus, timedate_departure__lt=timezone.now()
            ).order_by("-timedate_departure")
            for bus in bus_list
        }

    def add_past_trip_to_bus(self, bus_list):
        past_trip_dict = self.get_past_trip_dict(bus_list)

        for bus in bus_list:
            for trip in past_trip_dict[bus.pk]:
                bought_seats = Ticket.objects.filter(trip=trip, returned=False).count()
                trip.bought_seats = bought_seats
            bus.past_trips = past_trip_dict[bus.pk]

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
            bus.average_ticket_price = round(
                money_info.get("ticket_price_sum", 0) / money_info.get("trip_count", 1),
                2,
            )
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


class CreateBusView(PartnerRequiredMixin, FormInvalidMixin, CreateView):
    """
    View for creating a new bus.

    This view allows partners to create a new bus associated with their company.

    Attributes:
        form_class (Form): The form class used for creating a new bus.
        template_name (str): The template name for rendering the bus creation page.
        success_url (str): The URL to redirect to after successful bus creation.

    Methods:
        form_valid(self, form): Process the form submission when it is valid.
        get_context_data(self, **kwargs): Add additional context data to be used in the template.

    """

    form_class = CreateBusForm
    template_name = "bus_create.html"
    success_url = "/partner/bus/list/"

    def form_valid(self, form):
        """
        Process the form submission when it is valid.

        Args:
            form (Form): The form instance containing the submitted data.

        Returns:
            HttpResponse: The HTTP response object after successful form submission.

        """
        obj = form.save(commit=False)
        obj.company = Company.objects.get(partner__user=self.request.user)
        obj.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        Add additional context data to be used in the template.

        Returns:
            dict: Additional context data.

        """
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "bus"
        context["title"] = _("Створити автобус")
        return context


class TripView(PartnerRequiredMixin, ListView):
    """
    View for displaying a list of trips along with additional filtering options.

    This view requires the user to be logged in as a partner and provides information about each trip,
    including details like start point, end point, date, and allows filtering based on various criteria.

    Attributes:
        model (Model): The model associated with this view.
        context_object_name (str): The context variable name for the list of trips.
        paginate_by (int): The number of trips to display per page.
        template_name (str): The template name for rendering the trips list page.

    Methods:
        get_queryset(self): Retrieve the queryset of trips based on filter criteria.
        get_context_data(self, **kwargs): Add additional context data to be used in the template.

    """

    model = Trip
    context_object_name = "trips_list"
    paginate_by = 5
    template_name = "partner/trips_list.html"

    def get_context_data(self, **kwargs):
        """
        Add additional context data to be used in the template.

        Returns:
            dict: Additional context data.

        """
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET
        form_params = {
            "id": query_params.get("id", None),
            "start_point": query_params.get("start_point", None),
            "end_point": query_params.get("end_point", None),
            "date": query_params.get("date", None),
        }
        context["form"] = TripSearchForm(**form_params)

        context["active_tab"] = "trips"
        type = query_params.get("type", None)
        if type == "future":
            context["title"] = "Майбутні рейси"
        elif type == "past":
            context["title"] = "Минулі рейси"
        else:
            context["title"] = "Рейси"
        context["href"] = "partner:trips"
        context["sort_type"] = self.request.GET.get("sort_type", None)

        trips = context["trips_list"]
        for trip in trips:
            if (
                trip.timedate_departure < timezone.now()
                or Ticket.objects.filter(trip=trip).exists()
            ):
                trip.edit = False
            else:
                trip.edit = True
        for trip in context["trips_list"]:
            trip.tickets = trip.ticket_set.filter(
                returned=False
            )  # reverse relationship

        return context

    def get_queryset(self):
        """
        Retrieve the queryset of trips based on filter criteria.

        Returns:
            QuerySet: The queryset of trips based on filter criteria.

        """
        type = self.request.GET.get("type", None)
        sort_type = self.request.GET.get("sort_type", None)
        id = self.request.GET.get("id", None)
        start_point = self.request.GET.get("start_point", None)
        end_point = self.request.GET.get("end_point", None)
        date = self.request.GET.get("date", None)
        sort_params = {}

        if id:
            sort_params["id"] = id

        if start_point:
            sort_params["start_point"] = start_point

        if end_point:
            sort_params["end_point"] = end_point

        if date:
            sort_params["timedate_departure__date"] = date

        if type == "future":
            sort_params["timedate_departure__gt"] = datetime.now()
        elif type == "past":
            sort_params["timedate_departure__lt"] = datetime.now()

        if sort_type:
            if sort_type == "ASC":
                sort = "timedate_departure"
            else:
                sort = "-timedate_departure"
            return (
                Trip.objects.select_related("bus__company")
                .filter(bus__company__partner__user=self.request.user, **sort_params)
                .order_by(sort)
            )
        else:
            return Trip.objects.select_related("bus__company").filter(
                bus__company__partner__user=self.request.user, **sort_params
            )


class CreateTripView(PartnerRequiredMixin, FormInvalidMixin, CreateView):
    """
    View for creating a new trip.

    This view allows partners to create a new trip associated with their company.

    Attributes:
        form_class (Form): The form class used for creating a new trip.
        template_name (str): The template name for rendering the trip creation page.
        success_url (str): The URL to redirect to after successful trip creation.

    Methods:
        get_form_kwargs(self): Get the keyword arguments to instantiate the form.
        get_context_data(self, **kwargs): Add additional context data to be used in the template.

    """

    form_class = CreateUpdateTripForm
    template_name = "trip_create.html"
    success_url = "/partner/trips?type=future"

    def get_form_kwargs(self):
        """
        Pass arguments to the form's constructor
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        """
        Add additional context data to be used in the template.

        Returns:
            dict: Additional context data.

        """
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "trips"
        context["title"] = _("Створити подорож")
        return context


class UpdateTripView(PartnerRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating a trip.

    This view allows partners to update details of an existing trip associated with their company,
    given that the trip has not started yet and no tickets have been sold.

    Attributes:
        model (Model): The model associated with this view.
        template_name (str): The template name for rendering the trip update page.
        form_class (Form): The form class used for updating the trip.
        success_url (str): The URL to redirect to after successful trip update.
        pk_url_kwarg (str): The URL keyword argument for the trip primary key.

    Methods:
        test_func(self): Test if the user has permission to update the trip.
        get_form_kwargs(self): Get the keyword arguments to instantiate the form.

    """

    model = Trip
    template_name = "partner/trip_update.html"
    form_class = CreateUpdateTripForm
    success_url = "/partner/trips?type=future"
    pk_url_kwarg = "trip_pk"

    def test_func(self):
        """
        Test if the user has permission to update the trip.

        Returns:
            bool: True if the user has permission, False otherwise.

        """
        trip = self.get_object()
        return (
            Company.objects.get(partner__user=self.request.user) == trip.bus.company
            and trip.timedate_departure > timezone.now()
            and not Ticket.objects.filter(trip=trip).exists()
        )

    def get_form_kwargs(self):
        """
        Pass arguments to the form's constructor
        """
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


class SubAccountsView(PartnerRequiredMixin, ListView):
    """
    View for displaying a list of sub-accounts associated with the partner's company.

    This view requires the user to be logged in as a partner and provides a list of sub-accounts
    (users associated with the partner's company marked as sub-accounts).

    Attributes:
        model (Model): The model associated with this view.
        template_name (str): The template name for rendering the sub-accounts list page.
        context_object_name (str): The context variable name for the list of sub-accounts.

    Methods:
        dispatch(self, request, *args, **kwargs): Override the dispatch method to check authentication.
        get_queryset(self): Retrieve the queryset of sub-accounts associated with the logged-in partner.
        get_context_data(self, **kwargs): Add additional context data to be used in the template.

    """

    model = Partner
    template_name = "partner/sub_accounts.html"
    context_object_name = "sub_accounts"

    def dispatch(self, request, *args, **kwargs):
        """
        Override the dispatch method to check authentication.

        If the logged-in user is a sub-account, raise PermissionDenied.

        Returns:
            HttpResponse: The HTTP response object.

        """
        if request.user.is_authenticated and request.user.is_sub_account:
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Retrieve the queryset of sub-accounts associated with the logged-in partner.

        Returns:
            QuerySet: The queryset of sub-accounts associated with the logged-in partner.

        """
        return Partner.objects.filter(
            company=Company.objects.get(partner__user=self.request.user),
            user__is_sub_account=True,
        )

    def get_context_data(self, **kwargs):
        """
        Add additional context data to be used in the template.

        Returns:
            dict: Additional context data.

        """
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "sub_accounts"
        context["title"] = _("Субаккаунти")
        return context


class StationCreateView(PartnerRequiredMixin, FormInvalidMixin, CreateView):
    """
    View for creating a new station.

    This view allows partners to create a new station associated with their company.

    Attributes:
        form_class (Form): The form class used for creating a new station.
        template_name (str): The template name for rendering the station creation page.
        success_url (str): The URL to redirect to after successful station creation.

    Methods:
        get_context_data(self, **kwargs): Add additional context data to be used in the template.

    """

    form_class = StationCreateFrom
    template_name = "station_create.html"
    success_url = "/partner/station/list/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Створити станцію")

        return context


class StationListView(PartnerRequiredMixin, ListView):
    """
    View for displaying a list of stations with filtering options.

    This view requires the user to be logged in as a partner and provides a list of stations
    associated with the partner's company, along with filtering options.

    Attributes:
        model (Model): The model associated with this view.
        template_name (str): The template name for rendering the station list page.
        context_object_name (str): The context variable name for the list of stations.
        paginate_by (int): The number of stations to display per page.

    Methods:
        get_context_data(self, **kwargs): Add additional context data to be used in the template.
        get_queryset(self): Retrieve the queryset of stations based on filter criteria.

    """

    model = Station
    template_name = "station_list.html"
    context_object_name = "stations"
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context["form"] = StationCreateFrom()
        context["title"] = "Станції"

        query_params = self.request.GET
        form_params = {
            "station": query_params.get("station", None),
            "street_type": query_params.get("street_type", None),
            "street": query_params.get("street", None),
            "number": query_params.get("number", None),
            "city": query_params.get("city", None),
        }
        context["form"] = StationCreateFrom(**form_params)

        return context

    def get_queryset(self):
        """
        Retrieve the queryset of stations based on filter criteria.

        Returns:
            QuerySet: The queryset of stations based on filter criteria.

        """
        station = self.request.GET.get("station", None)
        street_type = self.request.GET.get("street_type", None)
        street = self.request.GET.get("street", None)
        number = self.request.GET.get("number", None)
        city = self.request.GET.get("city", None)

        sort_params = {}

        if station:
            sort_params["station"] = station

        if street_type:
            sort_params["street_type"] = street_type

        if street:
            sort_params["street"] = street

        if number:
            sort_params["number"] = number

        if city:
            sort_params["city"] = city

        return Station.objects.filter(**sort_params)
