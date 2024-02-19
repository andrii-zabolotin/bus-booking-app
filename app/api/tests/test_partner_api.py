"""
Tests for the partner API.
"""
from django.core.checks import messages
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from core.models import *
from slugify import slugify
from phonenumber_field.phonenumber import PhoneNumber

CREATE_PARTNER_URL = reverse("api:partner-create")
TOKEN_URL = reverse("api:token")
PARTNER_ME_URL = reverse("api:partner-me")
CREATE_BUS_URL = reverse("api:bus-list")
LIST_BUS_URL = reverse("api:bus-list")
STATION_URL = reverse("api:station")
TRIP_URL = reverse("api:trip-list")
CITY_URL = reverse("api:city")


@transaction.atomic
def create_partner(**params):
    """Create and return a new partner."""
    try:
        user = create_user_partner(**params)
        company = create_company(**params)
        return Partner.objects.create(user=user, company=company)
    except Exception as e:
        print(f"Error during registration: {e}")
        messages.error("An error occurred during registration. Please try again.")
        transaction.set_rollback(True)


def create_user_partner(**params):
    return get_user_model().objects.create_user(
        phone=params["user"]["phone"],
        email=params["user"]["email"],
        password=params["user"]["password"],
        is_partner=True,
    )


def create_company(**params):
    """Create and return a new company."""
    company = Company.objects.create(company_name=params["company"]["company_name"])
    company.slug = slugify(company.company_name)
    company.save()
    return company


# Public tests - Unauthenticated requests
class PublicPartnerApiTests(TestCase):
    def setUp(self):
        """Creates an API client that can be utilized for testing purposes."""
        self.client = APIClient()

    def test_create_partner_success(self):
        """Test creating a user is successful."""
        payload = {
            "company": {
                "company_name": "Partner Company",
            },
            "user": {
                "phone": "+380669057079",
                "email": "test@gmail.com",
                "password": "testpass123",
            },
        }

        res = self.client.post(CREATE_PARTNER_URL, payload, format="json")

        # Checking whether the object was successfully created in the database.
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Retrieving a user from the database after verifying the success.
        user = get_user_model().objects.get(phone=payload["user"]["phone"])
        # Verification of the correctness of the password.
        self.assertTrue(user.check_password(payload["user"]["password"]))
        # Checking whether the company object was successfully created in the database.
        company = Company.objects.filter(
            company_name=payload["company"]["company_name"]
        )
        self.assertTrue(company.exists())
        # Checking whether the partner object was successfully created in the database.
        partner = Partner.objects.filter(company=company[0], user=user).exists()
        self.assertTrue(partner)
        # Indicating that the password should not be included in the response.
        self.assertNotIn("password", res.data)

    def test_company_exists_error(self):
        """Test error returned if company exists."""
        payload = {
            "company": {
                "company_name": "Partner Company",
            },
            "user": {
                "phone": "+380669057079",
                "email": "test@gmail.com",
                "password": "testpass123",
            },
        }
        payload2 = {
            "company": {
                "company_name": "Partner Company",
            },
            "user": {
                "phone": "+380936057079",
                "email": "test5@gmail.com",
                "password": "testpass1234",
            },
        }
        # Creating a partner to trigger an error.
        create_partner(**payload2)
        # POST request to create a partner with the same company name.
        res = self.client.post(CREATE_PARTNER_URL, payload, format="json")

        # Expecting a negative response, as the phone number is already registered.
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_is_partner(self):
        """Test user is partner"""
        payload = {
            "company": {
                "company_name": "Partner Company",
            },
            "user": {
                "phone": "+380669057079",
                "email": "test@gmail.com",
                "password": "testpass123",
            },
        }

        res = self.client.post(CREATE_PARTNER_URL, payload, format="json")

        self.assertTrue(
            get_user_model().objects.get(phone=payload["user"]["phone"]).is_partner
        )

    def test_retrieve_city_list(self):
        """Test retrieving cities is successful."""
        res = self.client.get(CITY_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        payload = {
            "company": {
                "company_name": "Partner Company",
            },
            "user": {
                "phone": "+380669057079",
                "email": "test@gmail.com",
                "password": "testpass123",
            },
        }
        self.partner = create_partner(**payload)
        self.client = APIClient()
        self.client.force_authenticate(user=self.partner.user)
        self.bus = Bus.objects.create(
            licence_plate="BB2108TA",
            number_of_seats=19,
            brand="MiniBus",
            company=self.partner.company,
        )
        self.start_city = City.objects.create(
            city="Київ", region="Київська", country="Україна"
        )
        self.end_city = City.objects.create(
            city="Прилуки", region="Київська", country="Україна"
        )
        self.departure_station = Station.objects.create(
            station="Гулька",
            street_type="Вулиця",
            street="Котляра",
            number=12,
            city=self.start_city,
        )
        self.arrival_station = Station.objects.create(
            station="Школа",
            street_type="Вулиця",
            street="Шевченка",
            number=12 - 13,
            city=self.end_city,
        )
        payload = {
            "timedate_departure": "2024-02-16 16:00:00",
            "timedate_arrival": "2024-02-16 18:00:00",
            "price": 200,
            "bus": self.bus,
            "departure_station": self.departure_station,
            "arrival_station": self.arrival_station,
            "start_point": self.start_city,
            "end_point": self.end_city,
        }
        self.trip = Trip.objects.create(**payload)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(PARTNER_ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            {
                "company": {"company_name": self.partner.company.company_name},
                "user": {
                    "phone": self.partner.user.phone,
                    "email": self.partner.user.email,
                },
            },
        )

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the me endpoint."""
        res = self.client.post(PARTNER_ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the partner profile for the authenticated partner."""
        payload = {"user": {"email": "updated@gmail.com", "phone": "+380937772204"}}

        res = self.client.patch(PARTNER_ME_URL, payload, format="json")

        self.partner.user.refresh_from_db()
        self.assertEqual(self.partner.user.email, payload["user"]["email"])
        self.assertTrue(self.partner.user.phone, payload["user"]["phone"])
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_bus_success(self):
        """Test creating bus is successful."""
        payload = {
            "licence_plate": "AA5555CD",
            "number_of_seats": 20,
            "brand": "Mercedes",
        }

        res = self.client.post(CREATE_BUS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_retrieve_bus_success(self):
        """Test retrieving bus list is successful."""

        res = self.client.get(LIST_BUS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_update_bus_success(self):
        """Test updating bus is successful."""
        old_brand = self.bus.brand
        res = self.client.patch(
            reverse("api:bus-detail", kwargs={"pk": self.bus.pk}),
            {"brand": "Mercedes"},
            format="json",
        )

        self.bus.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(old_brand == self.bus.brand)

    def test_delete_bus_success(self):
        """Test deleting bus is successful."""
        payload = {
            "licence_plate": "BB2108DA",
            "number_of_seats": 19,
            "brand": "MiniBus",
        }
        self.client.post(CREATE_BUS_URL, payload)

        res = self.client.delete(
            reverse(
                "api:bus-detail",
                kwargs={
                    "pk": Bus.objects.get(licence_plate=payload["licence_plate"]).pk
                },
            )
        )

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_bus_with_trips_error(self):
        """Test delete error returned if bus has trips."""
        payload_trip = {
            "timedate_departure": "2024-02-16 16:00:00",
            "timedate_arrival": "2024-02-16 18:00:00",
            "price": 200,
            "bus": self.bus,
            "departure_station": self.departure_station,
            "arrival_station": self.arrival_station,
            "start_point": self.start_city,
            "end_point": self.end_city,
        }

        Trip.objects.create(**payload_trip)
        res = self.client.delete(reverse("api:bus-detail", kwargs={"pk": self.bus.pk}))

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_station_retrieve_success(self):
        """Test retrieve station is successful."""
        res = self.client.get(STATION_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_station_create_seccess(self):
        """Test creating station is successful."""
        payload = {
            "station": "Школа",
            "street_type": "Вулиця",
            "street": "Шевченка",
            "number": "7",
            "city": self.start_city.pk,
        }

        res = self.client.post(STATION_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_trip_create_success(self):
        """Test creating trip is successful."""
        payload = {
            "timedate_departure": "2024-02-16 16:00:00",
            "timedate_arrival": "2024-02-16 18:00:00",
            "price": 200,
            "bus": self.bus.pk,
            "departure_station": self.departure_station.pk,
            "arrival_station": self.arrival_station.pk,
            "start_point": self.start_city.pk,
            "end_point": self.end_city.pk,
        }

        res = self.client.post(TRIP_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_retrieve_trips(self):
        """Test retrieving trips list."""
        res = self.client.get(TRIP_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete_trip_success(self):
        """Test deleting trip is successful."""
        res = self.client.delete(
            reverse("api:trip-detail", kwargs={"pk": self.trip.pk})
        )

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_update_trip(self):
        """Test updating trip."""
        old_price = self.trip.price
        res = self.client.patch(
            reverse("api:trip-detail", kwargs={"pk": self.trip.pk}), {"price": 350}
        )

        self.trip.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(old_price == self.trip.price)

    def test_update_or_delete_trip_with_tickets_error(self):
        """Test error returned if trip has tickets while trying to update/delete."""
        Ticket.objects.create(
            first_name="John", last_name="Doe", user=self.partner.user, trip=self.trip
        )

        res_upd = self.client.patch(
            reverse("api:trip-detail", kwargs={"pk": self.trip.pk}), {"price": 400}
        )
        res_del = self.client.delete(
            reverse("api:trip-detail", kwargs={"pk": self.trip.pk})
        )

        self.trip.refresh_from_db()
        self.assertEqual(res_upd.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_del.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tickets_list(self):
        """Test retrieving is successful."""
        pass
