from django.shortcuts import render, redirect
from core.forms import *
from core.models import *
from .utils import *


def home_page(request):
    queryset = None
    context = {}

    if request.method == "POST":
        form = CitySelectionForm(request.POST)
        if form.is_valid():
            start_point = form.cleaned_data["start_point"]
            end_point = form.cleaned_data["end_point"]
            date = form.cleaned_data["date"]
            passengers_quantity = form.cleaned_data["passengers_quantity"]
            request.session["passengers_quantity"] = passengers_quantity
            current_time = datetime.now().time()
            context.update(
                {
                    "start_point": start_point,
                    "end_point": end_point,
                    "date": date,
                }
            )
            if date == datetime.now().date():
                queryset = Trip.objects.filter(
                    start_point=start_point,
                    end_point=end_point,
                    timedate_departure__date=date,
                    timedate_departure__time__gt=current_time,
                )
            else:
                queryset = Trip.objects.filter(
                    start_point=start_point,
                    end_point=end_point,
                    timedate_departure__date=date,
                )
            for trip in queryset:
                sold_tickets_count = Ticket.objects.filter(trip=trip).count()
                remaining_seats = trip.bus.number_of_seats - sold_tickets_count
                trip.remaining_seats = remaining_seats
                trip.price = trip.price * passengers_quantity
            queryset = [
                trip for trip in queryset if trip.remaining_seats >= passengers_quantity
            ]
    else:
        form = CitySelectionForm()

    context.update(
        {
            "form": form,
            "queryset": queryset,
        }
    )

    return render(request, "core/index.html", context=context)


# class TripPage(DetailView, FormMixin):
#     model = Trip
#     template_name = "booking/trip.html"
#     context_object_name = "trip"
#     form_class = TicketPurchase
#     pk_url_kwarg = "trip_pk"
#     success_url = reverse_lazy('user_app:profile')
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["title"] = context["trip"].timedate_departure.date()
#         context["passengers_quantity_range"] = range(self.request.session.get('passengers_quantity', 1))
#         return context
#
#     def post(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         form = self.get_form()
#         if form.is_valid():
#             return self.form_valid(form)
#         else:
#             return self.form_invalid(form)
#
#     def form_valid(self, form):
#         # Здесь вы можете добавить логику для сохранения данных формы
#         # например, создание объекта Ticket и сохранение его в базе данных
#         ticket = form.save(commit=False)
#         ticket.trip = self.object
#         ticket.user = self.request.user
#         ticket.save()
#         return super().form_valid(form)
#
#     def form_invalid(self, form):
#         # Здесь вы можете добавить логику для случая, когда форма недействительна
#         return self.render_to_response(self.get_context_data(form=form))


def checkout(request, trip_pk):
    trip = Trip.objects.get(pk=trip_pk)
    price = trip.price * request.session.get("passengers_quantity", 1)
    if request.method == "POST":
        buyer_form = BuyerInfoForm(request.POST)
        passenger_forms = [
            PassagerInfoForm(request.POST, prefix=f"passenger_{i}")
            for i in range(request.session.get("passengers_quantity", 1))
        ]

        if buyer_form.is_valid() and all(form.is_valid() for form in passenger_forms):
            # Создание объекта BuyerInfo
            buyer_data = buyer_form.cleaned_data
            if Buyer.objects.filter(
                email=buyer_data["email"], phone=buyer_data["phone"]
            ).exists():
                buyer = Buyer.objects.get(
                    email=buyer_data["email"], phone=buyer_data["phone"]
                )
            else:
                buyer = Buyer.objects.create(**buyer_data)

            for i, form in enumerate(passenger_forms):
                ticket_data = form.cleaned_data  # first_name, last_name
                ticket_data["user"] = request.user
                ticket_data["buyer_id"] = buyer.pk
                ticket_data["trip_id"] = trip_pk
                Ticket.objects.create(**ticket_data)

            return redirect("user:profile")  # Замените на свой URL успеха

    else:
        buyer_form = BuyerInfoForm()
        passenger_forms = [
            PassagerInfoForm(prefix=f"passenger_{i}")
            for i in range(request.session.get("passengers_quantity", 1))
        ]

    return render(
        request,
        "checkout.html",
        context={
            "buyer_form": buyer_form,
            "passenger_forms": passenger_forms,
            "trip": trip,
            "price": price,
        },
    )
