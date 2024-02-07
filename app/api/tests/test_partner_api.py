"""
Tests for the partner API.
"""
from django.core.checks import messages
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import transaction
from rest_framework import status
from rest_framework.test import APIClient
from core.models import *
from slugify import slugify
from phonenumber_field.phonenumber import PhoneNumber

CREATE_PARTNER_URL = reverse("api:partner-create")
TOKEN_URL = reverse("api:token")
PARTNER_ME_URL = reverse("api:partner-me")


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
class PublicUserApiTests(TestCase):
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
