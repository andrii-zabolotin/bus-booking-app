from django.urls import path
from user.views import *

app_name = "user"

urlpatterns = [
    path("registration/", RegisterUser.as_view(), name="registration"),
    path("login/", LoginUser.as_view(), name="login"),
    path("trips/future/", user_profile, name="future"),
    path("contact/", user_contact, name="contact"),
    path("trips/history/", user_history, name="history"),
    path("ticket/<int:ticket_pk>/return/", ticket_return, name="ticket_return"),
    path("tickets/returned", user_returned_tickets, name="returned_tickets"),
    path("", logout_user, name="logout"),
]
