from django.contrib import admin
from .models import *


class CompanyAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("company_name",)}


class TripAdmin(admin.ModelAdmin):
    autocomplete_fields = (
        "departure_station",
        "arrival_station",
        "start_point",
        "end_point",
    )


class StationAdmin(admin.ModelAdmin):
    search_fields = ("station",)


class CityAdmin(admin.ModelAdmin):
    search_fields = ("city", "region", "country")


admin.site.register(Company, CompanyAdmin)
admin.site.register(Station, StationAdmin)
admin.site.register(City, CityAdmin)
admin.site.register(Partner)
admin.site.register(Bus)
admin.site.register(Trip, TripAdmin)
admin.site.register(Ticket)
