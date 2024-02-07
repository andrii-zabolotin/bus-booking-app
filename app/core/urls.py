from django.urls import path
from .views import *

app_name = "core"

urlpatterns = [
    path("", home_page, name="home"),
    path("checkout/<int:trip_pk>", checkout, name="checkout"),
]
