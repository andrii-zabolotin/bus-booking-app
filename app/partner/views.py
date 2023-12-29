from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count
from django.shortcuts import render, redirect
from slugify import slugify
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView, CreateView
from django.contrib.auth.decorators import login_required

from core.models import Company, Bus, Partner, Trip
from core.utils import PartnerRequiredMixin
from partner.forms import CreateBusForm, CompanyForm, CreateTripForm
from user.forms import RegisterClientForm


@transaction.atomic
def partner_registration(request):
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


@login_required(login_url="/user/login")
def partner_profile(request):
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
        trip_counts = (
            Trip.objects.filter(bus__in=bus_list)
            .values("bus")
            .annotate(trip_count=Count("id"))
        )
        trip_count_dict = {
            trip_count["bus"]: trip_count["trip_count"] for trip_count in trip_counts
        }
        for bus in bus_list:
            bus.trip_count = trip_count_dict.get(bus.id, 0)

        return context


class TripView(PartnerRequiredMixin, ListView):
    model = Trip
    template_name = "partner/trips.html"
    context_object_name = "trips_list"

    def get_queryset(self):
        return Trip.objects.select_related("bus__company").filter(
            bus__company__partner__user=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "trips"
        return context


class CreateBusView(PartnerRequiredMixin, CreateView):
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


class CreateTripView(PartnerRequiredMixin, CreateView):
    form_class = CreateTripForm
    template_name = "trip_create.html"
    success_url = "/partner/trips/"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["active_tab"] = "trips"
        return context
