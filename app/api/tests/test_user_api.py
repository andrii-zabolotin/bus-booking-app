"""
Tests for the user API.
"""
from django.test import TestCase

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from rest_framework.test import APIClient

from phonenumber_field.phonenumber import PhoneNumber

CREATE_USER_URL = reverse("api:user-create")
TOKEN_URL = reverse("api:token")
ME_URL = reverse("api:user-me")
TRIP_URL = reverse("api:user-trip")


def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)


# Public tests - Unauthenticated requests
class PublicUserApiTests(TestCase):
    def setUp(self):
        """Creates an API client that can be utilized for testing purposes."""
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating a user is successful."""
        payload = {
            "phone": PhoneNumber.from_string("+380669057079"),
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
            "phone": PhoneNumber.from_string("+380669057079"),
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
            "phone": PhoneNumber.from_string("+38066905707"),
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
            "phone": PhoneNumber.from_string("+5669057079"),
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
            "phone": PhoneNumber.from_string("+380669057079"),
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
            "phone": PhoneNumber.from_string("+380669057099"),
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
            phone=PhoneNumber.from_string("+380669057079"),
            email="test@example.com",
            password="goodpass",
        )

        payload = {
            "phone": PhoneNumber.from_string("+380669057079"),
            "password": "badpass",
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_phone_not_found(self):
        """Test error returned if user not found for given phone."""
        payload = {
            "phone": PhoneNumber.from_string("+380669057079"),
            "password": "pass123",
        }
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn("token", res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        """Test posting a blank password returns an error."""
        payload = {"phone": PhoneNumber.from_string("+380669057079"), "password": ""}
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
            {"end_city_id": "1", "start_city_id": "2", "date": "2024-02-18"},
            {"end_city_id": "1", "start_city_id": "2", "date": "2024-02-18"},
        ]
        for param in query_params:
            res = self.client.get(TRIP_URL, param)
            self.assertEqual(res.status_code, status.HTTP_200_OK)


class PrivateUserApiTests(TestCase):
    """Test API requests that require authentication."""

    def setUp(self):
        self.user = create_user(
            phone=PhoneNumber.from_string("+380669057079"),
            email="test@example.com",
            password="testpass123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

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
