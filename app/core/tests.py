from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from core.models import *
from core.views import checkout


class CheckoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Создаем тестового пользователя
        self.user = get_user_model().objects.create_user(
            phone="+1234567890", email="test@example.com", password="testpassword"
        )


        # Создаем тестовую поездку
        self.trip = Trip.objects.create(
            timedate_departure="2023-01-01 12:00:00",
            timedate_arrival="2023-01-01 18:00:00",
            price=100,
            # ... Добавьте остальные обязательные поля здесь
        )

        # Устанавливаем количество пассажиров в сессии
        self.client.session["passengers_quantity"] = 2
        self.client.session.save()

    def test_checkout_authenticated_user(self):
        user = User.objects.create_user(
            phone="+380669077079", email="test@example.cpm", password="testpassword"
        )
        self.client.force_login(user)

    #
    #     request = self.factory.get(reverse("checkout", args=[self.trip.pk]))
    #     response = checkout(request, self.trip.pk)
    #
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, "checkout.html")
    #
    # def test_checkout_unauthenticated_user(self):
    #     request = self.factory.get(reverse("checkout", args=[self.trip.pk]))
    #     response = checkout(request, self.trip.pk)
    #
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTemplateUsed(response, "checkout.html")
    #
    # def test_checkout_post_authenticated_user(self):
    #     user = User.objects.create(username="testuser", password="testpassword")
    #     self.client.force_login(user)
    #
    #     request_data = {
    #         "passenger_0-first_name": "John",
    #         "passenger_0-last_name": "Doe",
    #     }
    #
    #     request = self.factory.post(
    #         reverse("checkout", args=[self.trip.pk]), data=request_data
    #     )
    #     response = checkout(request, self.trip.pk)
    #
    #     self.assertEqual(response.status_code, 302)  # Redirect status code
    #     self.assertEqual(response.url, reverse("user:profile"))
    #
    #     ticket_count = Ticket.objects.filter(user=user, trip=self.trip).count()
    #     self.assertEqual(ticket_count, 1)
    #
    # def test_checkout_post_unauthenticated_user(self):
    #     request_data = {
    #         "passenger_0-first_name": "John",
    #         "passenger_0-last_name": "Doe",
    #         # Add other required fields for RegisterClientForm
    #     }
    #
    #     request = self.factory.post(
    #         reverse("checkout", args=[self.trip.pk]), data=request_data
    #     )
    #     response = checkout(request, self.trip.pk)
    #
    #     self.assertEqual(response.status_code, 302)  # Redirect status code
    #     self.assertEqual(response.url, reverse("user:profile"))
    #
    #     ticket_count = Ticket.objects.filter(user__isnull=True, trip=self.trip).count()
    #     self.assertEqual(ticket_count, 1)
