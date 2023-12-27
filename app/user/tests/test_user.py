# from django.contrib.auth import get_user_model
# from django.core.exceptions import ValidationError
# from django.test import TestCase
# from django.urls import reverse
# from phonenumber_field.phonenumber import PhoneNumber
# from phonenumbers.phonenumberutil import NumberParseException
#
#
# def create_user(**params):
#     """Create and return a new user."""
#     return get_user_model().objects.create_user(**params)
#
#
# class PublicUserTests(TestCase):
#     """Test the public features of the user."""
#
#     def test_create_user_successful(self):
#         """Test creating user is successful."""
#         phone_numbers = [
#             "+380669057271",
#             "+48884057630",
#             "+33745745831",
#         ]
#         for phone_number in phone_numbers:
#             user_details = {
#                 "phone": PhoneNumber.from_string(phone_number),
#                 "first_name": "John",
#                 "email": "email@example.com",
#                 "last_name": "Smith",
#                 "password": "testpassword",
#             }
#
#             with self.subTest():
#                 create_user(**user_details).full_clean()
#
#     def test_invalid_phone_number(self):
#         """The error returned if user phone is invalid."""
#         invalid_phone_numbers = [
#             "+38066905101",
#             "+380669051",
#             "+4888405763",
#         ]
#
#         for invalid_phone in invalid_phone_numbers:
#             user_details = {
#                 "phone": PhoneNumber.from_string(invalid_phone),
#                 "first_name": "John",
#                 "email": "email@example.com",
#                 "last_name": "Smith",
#                 "password": "testpassword",
#             }
#
#             with self.subTest():
#                 with self.assertRaises(ValidationError):
#                     create_user(**user_details).full_clean()
#
#     # def test_user_with_email_exists_error(self):
#     #     """Test error returned if user with email exists."""
#     #     user_details = {
#     #         "phone": PhoneNumber.from_string("+380669057172"),
#     #         "first_name": "John",
#     #         "email": "email@example.com",
#     #         "last_name": "Smith",
#     #         "password": "testpassword",
#     #     }
#     #     create_user(**user_details)
#     #
#     #     another_user_details = {
#     #         "phone": PhoneNumber.from_string("+380669057171"),
#     #         "first_name": "John",
#     #         "email": "email@example.com",
#     #         "last_name": "Smith",
#     #         "password": "testpassword",
#     #     }
#     #
#     #     self.assertRaises(ValidationError, create_user(**another_user_details))
