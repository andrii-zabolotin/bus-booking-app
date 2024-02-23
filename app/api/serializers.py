from django.utils import timezone
from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from django.utils.translation import gettext as _
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers
from slugify import slugify

from core.models import Company, Partner, Bus, Station, Trip, City, Ticket


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object"""

    class Meta:
        model = get_user_model()
        fields = ("phone", "email", "password")
        extra_kwargs = {
            "password": {
                "write_only": True,
                "min_length": 5,
            }
        }

    def create(self, validated_data):
        """Create and return a user with encrypted password"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update and return user."""
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth token."""

    phone = PhoneNumberField()
    password = serializers.CharField(
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        """Validate and authenticate the user."""
        phone = attrs.get("phone")
        password = attrs.get("password")
        user = authenticate(
            request=self.context.get("request"),
            username=phone,
            password=password,
        )
        if not user:
            msg = _("Unable to authenticate with provided credentials.")
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs


class CompanySerializer(serializers.ModelSerializer):
    """Serializer for the company object"""

    class Meta:
        model = Company
        fields = ("company_name",)

    def create(self, validated_data):
        company = Company.objects.create(**validated_data)
        slug = slugify(validated_data["company_name"])
        if Company.objects.filter(slug=slug).exists():
            raise serializers.ValidationError(
                {"company_name": [_("Компанія з такою назвою вже існує.")]}
            )
        company.slug = slug
        company.save()
        return company


class PartnerSerializer(serializers.Serializer):
    """Serializer for the Partner object"""

    company = CompanySerializer()
    user = UserSerializer()

    @transaction.atomic
    def create(self, validated_data):
        company_data = validated_data.pop("company")
        user_data = validated_data.pop("user")
        # Using UserSerializer and CompanySerializer to create users and companies.
        user_serializer = UserSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save(is_partner=True)
        else:
            raise serializers.ValidationError(user_serializer.errors)

        company_serializer = CompanySerializer(data=company_data)
        if company_serializer.is_valid():
            company = company_serializer.save()
        else:
            # Rolling back the transaction in case of an error.
            transaction.set_rollback(True)
            raise serializers.ValidationError(company_serializer.errors)

        # Creating a partner.
        partner = Partner.objects.create(user=user, company=company)
        return partner

    @transaction.atomic
    def update(self, instance, validated_data):
        company_data = validated_data.pop("company", {})
        user_data = validated_data.pop("user", {})

        # Assuming you have a related name 'partner' in your User model
        user_instance = instance.user
        user_serializer = UserSerializer(
            instance=user_instance, data=user_data, partial=True
        )
        if user_serializer.is_valid():
            user = user_serializer.save()
        else:
            raise serializers.ValidationError(user_serializer.errors)

        company_instance = instance.company
        company_serializer = CompanySerializer(
            instance=company_instance, data=company_data, partial=True
        )
        if company_serializer.is_valid():
            company = company_serializer.save()
        else:
            transaction.set_rollback(True)
            raise serializers.ValidationError(company_serializer.errors)

        instance.user = user
        instance.company = company
        instance.save()
        return instance


class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = ("id", "licence_plate", "number_of_seats", "brand")

    def create(self, validated_data):
        bus = Bus.objects.create(
            **validated_data,
            company=Company.objects.get(partner__user=self.context["request"].user)
        )
        return bus


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = "__all__"


class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = "__all__"


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = "__all__"


class TicketSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = ("returned",)


class ManageTicketSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Ticket
        fields = "__all__"
        read_only_fields = ("trip",)
