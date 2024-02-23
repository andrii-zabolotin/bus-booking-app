from datetime import datetime

from django.db import IntegrityError
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter

from rest_framework import generics, authentication, permissions, viewsets, mixins
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.viewsets import GenericViewSet

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


@extend_schema_view(
    get=extend_schema(
        parameters=[
            OpenApiParameter(
                "start_city_id",
                OpenApiTypes.NUMBER,
                description="Departure city id",
            ),
            OpenApiParameter(
                "end_city_id",
                OpenApiTypes.NUMBER,
                description="Arrival city id",
            ),
            OpenApiParameter(
                "date",
                OpenApiTypes.DATE,
                description="Trip date [YYYY-MM-DD]",
            ),
        ]
    )
)
class TripUserView(generics.ListAPIView):
    """Retrieve a list of available trips for user."""

    serializer_class = TripSerializer

    def get(self, request, *args, **kwargs):
        self.date = self.request.GET.get("date", None)
        self.end_point = self.request.GET.get("end_city_id", None)
        self.start_point = self.request.GET.get("start_city_id", None)

        if self.date:
            try:
                datetime.fromisoformat(self.date)
            except ValueError:
                return Response(
                    {"error": "Incorrect data format, should be YYYY-MM-DD."},
                    status=400,
                )
            if datetime.strptime(self.date, "%Y-%m-%d").date() < datetime.now().date():
                return Response(
                    {"error": "Date shouldn't be less than today."}, status=400
                )
        else:
            return Response(
                {"error": "Date is required."},
                status=400,
            )

        if self.end_point:
            for char in self.end_point:
                if ord(char) < 48 or ord(char) > 57:
                    return Response(
                        {"error": "Incorrect arrival city format, should be id"},
                        status=400,
                    )
        else:
            return Response(
                {"error": "Arrival city is required."},
                status=400,
            )

        if self.start_point:
            for char in self.start_point:
                if ord(char) < 48 or ord(char) > 57:
                    return Response(
                        {"error": "Incorrect departure city format, should be id"},
                        status=400,
                    )
        else:
            return Response(
                {"error": "Departure city is required."},
                status=400,
            )

        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Trip.objects.filter(
            end_point=self.end_point,
            start_point=self.start_point,
            timedate_departure__date=self.date,
        )

        for trip in queryset:
            sold_tickets_count = Ticket.objects.filter(
                trip=trip, returned=False
            ).count()
            remaining_seats = trip.bus.number_of_seats - sold_tickets_count
            trip.remaining_seats = remaining_seats
        queryset = [trip for trip in queryset if trip.remaining_seats >= 1]
        return queryset


@extend_schema_view(
    get=extend_schema(
        parameters=[
            OpenApiParameter(
                "type",
                OpenApiTypes.STR,
                description="Type of retrieving trips [future/past]",
            ),
            OpenApiParameter(
                "sort_type",
                OpenApiTypes.STR,
                description="Type of sorting [ask/desk]",
            ),
            OpenApiParameter(
                "returned",
                OpenApiTypes.STR,
                description="Returned tickets [true/false]",
            ),
        ]
    )
)
class ListCreateTicketUserView(generics.ListCreateAPIView):
    """List / Create user tickets."""

    serializer_class = TicketSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        type = self.request.GET.get("type", None)
        sort_type = self.request.GET.get("sort_type", None)
        returned = self.request.GET.get("returned", None)
        params = {}
        if type == "future":
            params["trip__timedate_departure__gt"] = datetime.now()
        elif type == "past":
            params["trip__timedate_departure__lt"] = datetime.now()

        if returned == "true":
            params["returned"] = True
        elif returned == "false":
            params["returned"] = False

        if sort_type:
            if sort_type == "ask":
                sort = "trip__timedate_departure"
            else:
                sort = "-trip__timedate_departure"
            return Ticket.objects.filter(user=self.request.user, **params).order_by(
                sort
            )
        else:
            return Ticket.objects.filter(user=self.request.user, **params)

    def create(self, request, *args, **kwargs):
        trip = Trip.objects.get(pk=request.data["trip"])
        occupied_seats = Ticket.objects.filter(trip=trip.pk, returned=False)
        available_seats = trip.bus.number_of_seats - len(occupied_seats)
        if trip.timedate_departure < timezone.now():
            return Response({"error": "This is a past trip."}, status=400)
        elif available_seats <= 0:
            return Response(
                {"error": "There is no available seats in this trip."}, status=400
            )
        else:
            return super().create(request, *args, **kwargs)


class RetrieveUpdateTicketUserView(generics.RetrieveUpdateAPIView):
    """Manage user tickets."""

    serializer_class = ManageTicketSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Ticket.objects.filter(user=self.request.user)


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


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                "type",
                OpenApiTypes.STR,
                description="Type of retrieving trips [future/past]",
            ),
            OpenApiParameter(
                "sort_type",
                OpenApiTypes.STR,
                description="Type of sorting [ask/desk]",
            ),
        ]
    )
)
class TripPartnerViewSet(viewsets.ModelViewSet):
    """ViewSet for company's trips."""

    serializer_class = TripSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated, IsPartner]

    def get_queryset(self):
        """Retrieve and return company's trips"""
        type = self.request.GET.get("type", None)
        sort_type = self.request.GET.get("sort_type", None)
        params = {}
        if type == "future":
            params["timedate_departure__gt"] = datetime.now()
        elif type == "past":
            params["timedate_departure__lt"] = datetime.now()

        if sort_type:
            if sort_type == "ask":
                sort = "timedate_departure"
            else:
                sort = "-timedate_departure"
            return (
                Trip.objects.select_related("bus__company")
                .filter(bus__company__partner__user=self.request.user, **params)
                .order_by(sort)
            )
        else:
            return Trip.objects.select_related("bus__company").filter(
                bus__company__partner__user=self.request.user, **params
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


class CityView(generics.ListAPIView):
    """List all cities."""

    serializer_class = CitySerializer
    queryset = City.objects.all()
