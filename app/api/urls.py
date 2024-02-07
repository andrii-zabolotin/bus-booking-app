from django.urls import path, include

from api.views import *

app_name = "api"

urlpatterns = [
    path("api/v1/user/create/", CreateUserView.as_view(), name="user-create"),
    path("api/v1/partner/create/", CreatePartnerView.as_view(), name="partner-create"),
    path("api/v1/token/", CreateTokenView.as_view(), name="token"),
    path("api/v1/user/me/", ManageUserView.as_view(), name="user-me"),
    path("api/v1/partner/me/", ManagePartnerView.as_view(), name="partner-me"),
]
