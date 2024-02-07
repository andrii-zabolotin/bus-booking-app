from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings
from .permissions import IsPartner
from api.serializers import UserSerializer, AuthTokenSerializer, PartnerSerializer


class CreateUserView(generics.CreateAPIView):
    """Create a new user in the system"""

    serializer_class = UserSerializer


class CreateTokenView(ObtainAuthToken):
    """Create a new auth token for user."""

    serializer_class = AuthTokenSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES


class ManageUserView(generics.RetrieveUpdateAPIView):
    """Manage the authenticated user."""

    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user


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
        return self.request.user
