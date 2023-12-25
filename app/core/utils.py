from core.models import Ticket


def calculate_remaining_seats(trip):
    sold_tickets_count = Ticket.objects.filter(trip=trip).count()
    return trip.bus.number_of_seats - sold_tickets_count


class DataMixin:
    # paginate_by = 2

    def get_user_context(self, **kwargs):
        context = kwargs
        cats = Category.objects.annotate(Count("women"))

        user_menu = menu.copy()
        if not self.request.user.is_authenticated:
            user_menu.pop(1)

        context["menu"] = user_menu

        context["cats"] = cats
        if "cat_selected" not in context:
            context["cat_selected"] = 0
        return context
