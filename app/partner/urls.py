from django.urls import path
from partner.views import *

app_name = "partner"

urlpatterns = [
    path("profile/", partner_profile, name="profile"),
    path("buses/", BusView.as_view(), name="buses"),
    path("bus_create/", CreateBusView.as_view(), name="bus_create"),
    path("trips/", TripView.as_view(), name="trips"),
    path("trip_create/", CreateTripView.as_view(), name="trip_create"),
    path("registration/", partner_registration, name="registration"),
]
