from django.urls import path
from partner.views import *

app_name = "partner"

urlpatterns = [
    path("profile/", partner_profile, name="profile"),
    path("buses/", BusView.as_view(), name="buses"),
    path("bus_create/", CreateBusView.as_view(), name="bus_create"),
    path("future_trips/", FutureTripView.as_view(), name="future_trips"),
    path("past_trips/", PastTripView.as_view(), name="past_trips"),
    path("trip_create/", CreateTripView.as_view(), name="trip_create"),
    path("trip/<int:trip_pk>/update/", UpdateTripView.as_view(), name="trip_update"),
    path("registration/", partner_registration, name="registration"),
]
