from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, TemplateView, ListView
from django.utils.translation import gettext_lazy as _

from core.models import Ticket, Trip, City
from core.utils import FormInvalidMixin
from user.forms import *


class RegisterUser(FormInvalidMixin, CreateView):
    """
    View for user registration.

    Attributes:
        form_class (class): Form used for user registration.
        template_name (str): HTML template for rendering the registration form.

    Methods:
        form_valid(self, form): Handles the valid form submission, creates a new user,
                               logs in the user, and redirects to the home page.
        get_context_data(self, **kwargs): Adds additional context data for rendering the form.
    """

    form_class = RegisterClientForm
    template_name = "user/register.html"

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect("core:home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = _("Реєстрація")
        return context


class LoginUser(FormInvalidMixin, LoginView):
    """
    View for user login.

    Attributes:
        form_class (class): Form used for user login.
        template_name (str): HTML template for rendering the login form.

    Methods:
        get_success_url(self): Retrieves the URL to redirect after successful login.
        get_context_data(self, **kwargs): Adds additional context data for rendering the form.
    """

    form_class = CustomAuthenticationForm
    template_name = "user/login.html"

    def get_success_url(self):
        if not self.request.GET.get("next"):
            return reverse_lazy("core:home")
        return self.request.GET.get("next")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next"] = ""
        if self.request.GET:
            context["next"] = self.request.GET["next"]
        context["title"] = _("Авторизація")
        return context


def logout_user(request):
    """
    View for user logout.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Redirects to the home page after logout.
    """
    logout(request)
    return redirect("core:home")


def not_partner_required(view_func):
    """
    Decorator function to check that the user is not a partner before accessing a view.

    Args:
        view_func (function): The original view function.

    Returns:
        function: Wrapped view function with the additional check for non-partner status.
    """

    def wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_partner:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped_view


@login_required(login_url="/user/login")
@not_partner_required
def user_returned_tickets(request):
    """
    View for displaying returned tickets for the logged-in user.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered page with returned tickets information.
    """

    tickets = Ticket.objects.filter(user=request.user, returned=True)

    return render(
        request,
        "user/returned_tickets.html",
        context={
            "tickets": tickets,
            "active_tab": "returned_tickets",
            "title": _("Повернені квитки"),
        },
    )


@login_required(login_url="/user/login")
@not_partner_required
def user_profile(request):
    """
    View for displaying the user's future trips and associated tickets.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered page with future trips and associated tickets information.
    """

    future_user_trips = (
        Ticket.objects.filter(
            user=request.user,
            trip__timedate_departure__gt=timezone.now(),
            returned=False,
        )
        .values_list("trip", flat=True)
        .distinct()
    )

    trips_with_tickets = []
    for trip in future_user_trips:
        obj = Trip.objects.get(pk=trip)
        tickets = Ticket.objects.filter(user=request.user, trip=trip, returned=False)
        trips_with_tickets.append({"trip": obj, "tickets": tickets})

    return render(
        request,
        "user/profile.html",
        context={
            "future_trips_with_tickets": trips_with_tickets,
            "active_tab": "future",
            "href": "user:future",
            "title": _("Майбутні поїздки"),
        },
    )


@login_required(login_url="/user/login")
@not_partner_required
def user_contact(request):
    """
    View for handling user contact information.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered page for updating user contact information.
    """

    if request.method == "POST":
        form = AddEmailToUser(request.POST, instance=request.user)
        if form.is_valid():
            user = request.user
            user.email = form.cleaned_data["email"]
            user.save()
            return redirect("user:contact")
    else:
        form = AddEmailToUser(instance=request.user)

    return render(
        request,
        "user/contact.html",
        context={
            "form": form,
            "active_tab": "contact",
            "title": _("Контактна інформація"),
        },
    )


@login_required(login_url="/user/login")
@not_partner_required
def user_history(request):
    """
    View for displaying the user's past trips and associated tickets.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered page with past trips and associated tickets information.
    """

    trips_with_tickets = []
    sort_type = request.GET.get("sort_type", None)
    if sort_type:
        if sort_type == "ASC":
            sort = "trip__timedate_departure"
        else:
            sort = "-trip__timedate_departure"
        user_past_trips = (
            Ticket.objects.filter(
                user=request.user,
                trip__timedate_departure__lt=timezone.now(),
                returned=False,
            )
            .values_list("trip", flat=True)
            .distinct()
        ).order_by(sort)
    else:
        user_past_trips = (
            Ticket.objects.filter(
                user=request.user,
                trip__timedate_departure__lt=timezone.now(),
                returned=False,
            )
            .values_list("trip", flat=True)
            .distinct()
        )

    for trip in user_past_trips:
        obj = Trip.objects.get(pk=trip)
        tickets = Ticket.objects.filter(user=request.user, trip=trip, returned=False)
        trips_with_tickets.append({"trip": obj, "tickets": tickets})

    return render(
        request,
        "user/history.html",
        context={
            "past_trips_with_tickets": trips_with_tickets,
            "active_tab": "history",
            "href": "user:history",
            "sort_type": sort_type,
            "title": _("Минулі поїздки"),
        },
    )


@login_required(login_url="/user/login")
@not_partner_required
def ticket_return(request, ticket_pk):
    """
    View for handling the return of a user's ticket.

    Args:
        request (HttpRequest): The HTTP request object.
        ticket_pk (int): The primary key of the ticket to be returned.

    Returns:
        HttpResponse: Rendered page for ticket return confirmation or denial.
    """

    ticket = get_object_or_404(Ticket, pk=ticket_pk)
    if ticket.trip.timedate_departure < timezone.now():
        raise PermissionDenied()
    if request.method == "POST":
        if not ticket.returned:
            ticket.returned = True
            ticket.save()
            return render(
                request,
                "user/confirm_return.html",
                {
                    "ticket": ticket,
                    "title": _(f"Повернення білета №{ticket_pk}"),
                },
            )
        else:
            return render(
                request,
                "user/already_returned.html",
                {
                    "ticket": ticket,
                    "title": _(f"Повернення білета №{ticket_pk}"),
                },
            )

    return render(
        request,
        "user/ticket_return.html",
        context={
            "ticket_pk": ticket_pk,
            "ticket": ticket,
            "title": _(f"Повернення білета №{ticket_pk}"),
        },
    )
