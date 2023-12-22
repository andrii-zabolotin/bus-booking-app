from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from user.models import User


class UserAdmin(BaseUserAdmin):
    list_display = (
        "phone",
        "email",
        "is_active",
        "is_staff",
        "is_partner",
    )
    search_fields = ("phone", "email")
    readonly_fields = ("date_joined", "last_login")

    fieldsets = (
        (None, {"fields": ("phone", "password")}),
        (_("Персональна інформація"), {"fields": ("email",)}),
        (
            _("Дозволи"),
            {"fields": ("is_active", "is_staff", "is_superuser", "is_partner")},
        ),
        (_("Важливі дати"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("phone", "email", "password1", "password2"),
            },
        ),
    )
    ordering = ("phone",)


admin.site.register(User, UserAdmin)
