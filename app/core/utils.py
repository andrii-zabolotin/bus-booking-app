from django.contrib.auth.mixins import UserPassesTestMixin

from core.models import Ticket


def calculate_remaining_seats(trip):
    sold_tickets_count = Ticket.objects.filter(trip=trip).count()
    return trip.bus.number_of_seats - sold_tickets_count


class PartnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_partner
