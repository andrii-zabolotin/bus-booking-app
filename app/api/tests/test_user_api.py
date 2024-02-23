"""
Tests for the user API.
"""
from datetime import datetime

from django.test import TestCase

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from rest_framework.test import APIClient

from phonenumber_field.phonenumber import PhoneNumber

from core.models import *

CREATE_USER_URL = reverse("api:user-create")
TOKEN_URL = reverse("api:token")
ME_URL = reverse("api:user-me")
TRIP_URL = reverse("api:user-trip")
TICKET_URL = reverse("api:ticket-list")


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


# Public tests - Unauthenticated requests
class PublicUserApiTests(TestCase):
    def setUp(self):
        """Creates an API client that can be utilized for testing purposes."""
        self.client = APIClient()

        self.user = create_user(
            phone=PhoneNumber.from_string("+380559057777"),
            email="test2@example.com",
            password="testpass123",
            is_partner=True,
        )
        company = Company.objects.create(company_name="Ajilik")
        partner = Partner.objects.create(user=self.user, company=company)

        self.bus = Bus.objects.create(
            licence_plate="test", number_of_seats=1, brand="asldf", company=company
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
            "price": 200,
            "bus": self.bus,
            "departure_station": self.departure_station,
            "arrival_station": self.arrival_station,
            "start_point": self.start_city,
            "end_point": self.end_city,
        }
        self.trip = Trip.objects.create(
            timedate_departure=datetime.strptime(
                f"{timezone.now().date()} 23:59:59", "%Y-%m-%d %H:%M:%S"
            ),
            timedate_arrival=datetime.strptime(
                f"{timezone.now().date()} 23:59:59", "%Y-%m-%d %H:%M:%S"
            ),
            **payload,
        )

    def test_create_user_success(self):
        """Test creating a user is successful."""
        payload = {
            "phone": PhoneNumber.from_string("+380669057777"),
            "email": "test@gmail.com",
            "password": "testpass123",
        }

        res = self.client.post(CREATE_USER_URL, payload)

        # Checking whether the object was successfully created in the database.
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Retrieving a user from the database after verifying the success.
        user = get_user_model().objects.get(phone=payload["phone"])
        # Verification of the correctness of the password.
        self.assertTrue(user.check_password(payload["password"]))
        # Indicating that the password should not be included in the response.
        self.assertNotIn("password", res.data)

    def test_user_with_phone_exists_error(self):
        """Test error returned if user with email exists."""
        payload = {
            "phone": PhoneNumber.from_string("+380669057777"),
            "email": "test@gmail.com",
            "password": "testpass123",
        }

        # Creating a user to trigger an error.
        create_user(**payload)
        # POST request to create a user with the same phone.
        res = self.client.post(CREATE_USER_URL, payload)

        # Expecting a negative response, as the phone number is already registered.
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_phone_is_short(self):
        """Test error returned if user phone is short."""
        payload = {
            "phone": PhoneNumber.from_string("+38066905777"),
            "email": "test@gmail.com",
            "password": "testpass123",
        }
        # Making a POST request to a URL with data transmission and recording the result.
        res = self.client.post(CREATE_USER_URL, payload)

        # Expecting a negative response.
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_phone_country_code_invalid(self):
        """Test error returned if user phone country code is invalid."""
        payload = {
            "phone": PhoneNumber.from_string("+5669057777"),
            "email": "test@gmail.com",
            "password": "testpass123",
        }
        # Making a POST request to a URL with data transmission and recording the result.
        res = self.client.post(CREATE_USER_URL, payload)

        # Expecting a negative response.
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        """Test an error is returned if password less than 5 chars."""
        payload = {
            "phone": PhoneNumber.from_string("+380669057777"),
            "email": "test@gmail.com",
            "password": "pw",
        }
        # Making a POST request to a URL with data transmission and recording the result.
        res = self.client.post(CREATE_USER_URL, payload)

        # Expecting a negative response.
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # Retrieving users with the specified phone parameter (true/false).
        user_exists = get_user_model().objects.filter(phone=payload["phone"]).exists()
        # Expecting that the user will not be created, as the password is too short.
        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Test generates token for valid credentials."""
        user_details = {
            "phone": PhoneNumber.from_string("+380669057777"),
            "email": "test5@example.com",
            "password": "test-user-password123",
        }

        create_user(**user_details)

        payload = {
            "phone": user_details["phone"],
            "password": user_details["password"],
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        """Test returns error if credentials invalid."""
        create_user(
            phone=PhoneNumber.from_string("+380669057777"),
            email="test@example.com",
            password="goodpass",
        )

        payload = {
            "phone": PhoneNumber.from_string("+380669057777"),
            "password": "badpass",
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_phone_not_found(self):
        """Test error returned if user not found for given phone."""
        payload = {
            "phone": PhoneNumber.from_string("+380669057777"),
            "password": "pass123",
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {"phone": PhoneNumber.from_string("+380669057777"), "password": ""}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test authentication is required for users."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_trip_queryparam_date_validation_error(self):
        """Test validation error of query param date is returned."""
        dates = ["05-01-2021", "2024", "2024-18-01"]
        for date in dates:
            res = self.client.get(TRIP_URL, {"date": date})
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_date_required_for_trip_retrieve(self):
        """Test that date is required error returned."""
        res = self.client.get(TRIP_URL, {"end_city_id": "1", "start_city_id": "2"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_city_required_for_trip_retrieve(self):
        """Test that cities is required error returned."""
        cities = [
            {"end_city_id": "1", "date": "2024-02-15"},
            {"start_city_id": "2", "date": "2024-02-15"},
        ]
        for city in cities:
            res = self.client.get(TRIP_URL, city)
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_trip_queryparam_city_id_validation_error(self):
        """Test validation error of query param city id is returned."""
        query_params = [{"end_city_id": "asf"}, {"start_city_id": "boba"}]
        for param in query_params:
            res = self.client.get(TRIP_URL, param)
            self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_trip_success(self):
        """Test retrieve trip is success."""
        query_params = [
            {"end_city_id": "1", "start_city_id": "2", "date": datetime.now().date()},
            {"end_city_id": "1", "start_city_id": "2", "date": datetime.now().date()},
        ]
        for param in query_params:
            res = self.client.get(TRIP_URL, param)
            self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_trip_error(self):
        """Test that retrieve trip with past date return error."""
        res = self.client.get(
            TRIP_URL, {"end_city_id": "1", "start_city_id": "2", "date": "2024-02-18"}
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_not_retrieve_full_trip(self):
        """Test that trip not returned if there is no seats left."""
        res = self.client.get(
            TRIP_URL,
            {
                "end_city_id": self.trip.end_point.pk,
                "start_city_id": self.trip.start_point.pk,
                "date": datetime.strptime(
                    f"{timezone.now().date()} 23:59:59", "%Y-%m-%d %H:%M:%S"
                ).date(),
            },
        )

        self.assertNotEqual([], res.data)

        payload = {
            "first_name": "Grande",
            "last_name": "Polish",
            "returned": False,
            "user": self.user,
            "trip": self.trip,
        }
        Ticket.objects.create(**payload)

        res = self.client.get(
            TRIP_URL,
            {
                "end_city_id": self.trip.end_point.pk,
                "start_city_id": self.trip.start_point.pk,
                "date": datetime.strptime(
                    f"{timezone.now().date()} 23:59:59", "%Y-%m-%d %H:%M:%S"
                ).date(),
            },
        )

        self.assertEqual([], res.data)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(
            phone=PhoneNumber.from_string("+380669057777"),
            email="test@example.com",
            password="testpass123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        user = create_user(
            phone=PhoneNumber.from_string("+380559057777"),
            email="test2@example.com",
            password="testpass123",
            is_partner=True,
        )
        company = Company.objects.create(company_name="Ajilik")
        partner = Partner.objects.create(user=user, company=company)

        self.bus = Bus.objects.create(
            licence_plate="test", number_of_seats=1, brand="asldf", company=company
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
            "price": 200,
            "bus": self.bus,
            "departure_station": self.departure_station,
            "arrival_station": self.arrival_station,
            "start_point": self.start_city,
            "end_point": self.end_city,
        }
        self.trip = Trip.objects.create(
            timedate_departure=datetime.strptime(
                f"{timezone.now().date()} 23:59:59", "%Y-%m-%d %H:%M:%S"
            ),
            timedate_arrival=datetime.strptime(
                f"{timezone.now().date()} 23:59:59", "%Y-%m-%d %H:%M:%S"
            ),
            **payload,
        )
        self.past_trip = Trip.objects.create(
            timedate_departure=datetime.strptime(
                "2024-02-02 10:00:00", "%Y-%m-%d %H:%M:%S"
            ),
            timedate_arrival=datetime.strptime(
                "2024-02-02 12:00:00", "%Y-%m-%d %H:%M:%S"
            ),
            **payload,
        )

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user."""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            {
                "phone": self.user.phone,
                "email": self.user.email,
            },
        )

    def test_post_me_not_allowed(self):
        """Test POST is not allowed for the me endpoint."""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for the authenticated user."""
        payload = {"email": "updated@gmail.com", "password": "newpassword123"}

        res = self.client.patch(ME_URL, payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, payload["email"])
        self.assertTrue(self.user.check_password(payload["password"]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_tickets_success(self):
        """Test retrieving tickets list is successful."""
        res = self.client.get(TICKET_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_ticket_create_success(self):
        """Test creating a new ticket is successful."""
        res = self.client.post(
            TICKET_URL,
            {
                "first_name": "Grande",
                "last_name": "Polish",
                "returned": False,
                "trip": self.trip.pk,
            },
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_ticket_update_success(self):
        """Test updating an existing ticket is successful."""
        payload = {
            "first_name": "Grande",
            "last_name": "Polish",
            "returned": False,
            "user": self.user,
            "trip": self.trip,
        }
        ticket = Ticket.objects.create(**payload)
        res = self.client.patch(
            reverse("api:ticket-detail", kwargs={"pk": ticket.pk}),
            data={"first_name": "updated"},
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["first_name"], "updated")

    def test_return_ticket_success(self):
        """Test ticket return is successful."""
        payload = {
            "first_name": "Grande",
            "last_name": "Polish",
            "returned": False,
            "user": self.user,
            "trip": self.trip,
        }
        ticket = Ticket.objects.create(**payload)
        res = self.client.patch(
            reverse("api:ticket-detail", kwargs={"pk": ticket.pk}),
            data={"returned": "True"},
            format="json",
        )

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["returned"], True)

    def test_ticket_past_trip_error(self):
        """Test error returned when trying to create a new ticket with past trip."""
        res = self.client.post(
            TICKET_URL,
            {
                "first_name": "Andrii",
                "last_name": "Obiz",
                "trip": self.past_trip.pk,
                "returned": False,
            },
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)

    def test_ticket_not_enough_seats_error(self):
        """Test error returned when there is no free seats in the bus."""
        payload = {
            "first_name": "Grande",
            "last_name": "Polish",
            "returned": False,
            "user": self.user,
            "trip": self.trip,
        }
        Ticket.objects.create(**payload)
        res = self.client.post(
            TICKET_URL,
            {
                "first_name": "Grande",
                "last_name": "Polish",
                "returned": False,
                "user": self.user,
                "trip": self.trip.pk,
            },
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", res.data)
