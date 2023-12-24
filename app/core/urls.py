from django.urls import path
from .views import *

app_name = "core"

urlpatterns = [
    # path('', HomePage.as_view(), name="home"),
    path("", home_page, name="home"),
    # path('trip/<int:trip_pk>', TripPage.as_view(), name="trip"),
    path("checkout/<int:trip_pk>", checkout, name="checkout"),
]
