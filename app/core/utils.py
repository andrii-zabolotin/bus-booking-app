from core.models import Ticket


def calculate_remaining_seats(trip):
    sold_tickets_count = Ticket.objects.filter(trip=trip).count()
    return trip.bus.number_of_seats - sold_tickets_count
