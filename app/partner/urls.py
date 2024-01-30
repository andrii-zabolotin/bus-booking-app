from django.urls import path
from partner.views import *

app_name = "partner"

urlpatterns = [
    path("profile/", PartnerProfileView.as_view(), name="profile"),
    path("bus/list/", BusView.as_view(), name="buses"),
    path("bus/create/", CreateBusView.as_view(), name="bus_create"),
    path("trips/", TripView.as_view(), name="trips"),
    path("trips/future/", FutureTripView.as_view(), name="future_trips"),
    path("trips/past/", PastTripView.as_view(), name="past_trips"),
    path("trip/create/", CreateTripView.as_view(), name="trip_create"),
    path("trip/<int:trip_pk>/update/", UpdateTripView.as_view(), name="trip_update"),
    path("registration/", partner_registration, name="registration"),
    path("sub_accounts/", SubAccountsView.as_view(), name="sub_accounts"),
    path(
        "sub_account_create/",
        partner_subaccount_registration,
        name="sub_account_create",
    ),
    path("station/create/", StationCreateView.as_view(), name="station_create"),
    path("station/list/", StationListView.as_view(), name="station_list"),
]
