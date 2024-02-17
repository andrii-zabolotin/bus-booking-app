from django.urls import path, include
from rest_framework import routers

from api.views import *

app_name = "api"

bus_router = routers.DefaultRouter()
bus_router.register(r"bus", BusViewSet, basename="bus")
trip_router = routers.DefaultRouter()
trip_router.register(r"trip", TripViewSet, basename="trip")

urlpatterns = [
    path("api/v1/user/create/", CreateUserView.as_view(), name="user-create"),
    path("api/v1/partner/create/", CreatePartnerView.as_view(), name="partner-create"),
    # path("api/v1/user/search/", SearchUserView.as_view(), name="user-search"),
    path("api/v1/token/", CreateTokenView.as_view(), name="token"),
    path("api/v1/user/me/", ManageUserView.as_view(), name="user-me"),
    path("api/v1/partner/me/", ManagePartnerView.as_view(), name="partner-me"),
    path("api/v1/", include(bus_router.urls)),
    path("api/v1/", include(trip_router.urls)),
    path("api/v1/station/", ListCreateStationView.as_view(), name="station"),
]
