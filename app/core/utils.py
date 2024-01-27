from django.contrib.auth.mixins import UserPassesTestMixin

from core.models import Ticket


def calculate_remaining_seats(trip):
    sold_tickets_count = Ticket.objects.filter(trip=trip).count()
    return trip.bus.number_of_seats - sold_tickets_count


class FormInvalidMixin:
    def form_invalid(self, form):
        for key, value in form.errors.items():
            if key != "__all__":
                form.fields[key].widget.attrs["class"] = "form-control is-invalid"
        return super().form_invalid(form)


class PartnerRequiredMixin(UserPassesTestMixin):
    login_url = "/user/login"

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_partner
