from django.db import IntegrityError
from django.utils import timezone

from rest_framework import generics, authentication, permissions, viewsets
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.settings import api_settings

from core.models import *
from .permissions import IsPartner
from api.serializers import *


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""

    serializer_class = UserSerializer


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""

    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user


# class SearchUserView(generics.ListAPIView):
#     """List of the searched trips"""
#
#     serializer_class = TripSearchSerializer
#
#     def get_queryset(self):
#         start_point_str = self.request.query_params.get("start_point")
#         end_point_str = self.request.query_params.get("end_point")
#
#         start_point_data = {
#             "city": start_point_str.split(",")[0].strip(),
#             "region": start_point_str.split(",")[1].replace("область", "").strip(),
#             "country": start_point_str.split(",")[2].strip(),
#         }
#
#         end_point_data = {
#             "city": end_point_str.split(",")[0].strip(),
#             "region": end_point_str.split(",")[1].replace("область", "").strip(),
#             "country": end_point_str.split(",")[2].strip(),
#         }
#
#         start_point = City.objects.get(**start_point_data)
#         end_point = City.objects.get(**end_point_data)
#         date = self.request.query_params.get("date")
#         passengers_quantity = int(
#             self.request.query_params.get("passengers_quantity", 1)
#         )
#         print(start_point, end_point, passengers_quantity, date)
#         current_time = timezone.now().time()
#         if date == timezone.now().date():
#             queryset = Trip.objects.filter(
#                 start_point=start_point,
#                 end_point=end_point,
#                 timedate_departure__date=date,
#                 timedate_departure__time__gt=current_time,
#             )
#         else:
#             queryset = Trip.objects.filter(
#                 start_point=start_point,
#                 end_point=end_point,
#                 timedate_departure__date=date,
#             )
#
#         for trip in queryset:
#             sold_tickets_count = Ticket.objects.filter(
#                 trip=trip, returned=False
#             ).count()
#             remaining_seats = trip.bus.number_of_seats - sold_tickets_count
#             trip.remaining_seats = remaining_seats
#             trip.price = trip.price * passengers_quantity
#         queryset = [
#             trip for trip in queryset if trip.remaining_seats >= passengers_quantity
#         ]
#         return queryset


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user."""

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class CreatePartnerView(generics.CreateAPIView):
    """Create a new partner in the system."""

    serializer_class = PartnerSerializer


class ManagePartnerView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated partner."""

    serializer_class = PartnerSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsPartner]

    def get_object(self):
        """Retrieve and return the authenticated partner."""
        return Partner.objects.get(user=self.request.user)


class BusViewSet(viewsets.ModelViewSet):
    """ViewSet for company's buses."""

    serializer_class = BusSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsPartner]

    def get_queryset(self):
        """Retrieve and return company buses."""
        return Bus.objects.select_related("company").filter(
            company__partner__user=self.request.user
        )

    def destroy(self, request, *args, **kwargs):
        """Destroy a model instance."""
        try:
            return super().destroy(request, *args, **kwargs)
        except IntegrityError as e:
            # Handle IntegrityError when object is protected
            return Response(
                {"error": "The object cannot be deleted. It is used in other entries."},
                status=400,
            )


class ListCreateStationView(generics.ListCreateAPIView):
    """Create a new station in the system. Or retrieve a list of stations."""

    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsPartner]

    serializer_class = StationSerializer
    queryset = Station.objects.all()


class TripViewSet(viewsets.ModelViewSet):
    """ViewSet for company's trips."""

    serializer_class = TripSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsPartner]

    def get_queryset(self):
        """Retrieve and return company's trips"""
        return Trip.objects.select_related("bus__company").filter(
            bus__company__partner__user=self.request.user
        )

    def update(self, request, *args, **kwargs):
        """Update a model instance."""
        if Ticket.objects.filter(trip=self.get_object()).exists():
            return Response(
                {
                    "error": "The trip object cannot be updated. It is used in other ticket entries."
                },
                status=400,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Destroy a model instance."""
        if Ticket.objects.filter(trip=self.get_object()).exists():
            return Response(
                {
                    "error": "The trip object cannot be deleted. It is used in other ticket entries."
                },
                status=400,
            )
        return super().destroy(request, *args, **kwargs)
