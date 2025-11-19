from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class HasNgoFilter(admin.SimpleListFilter):
    title = _("Has NGO")
    parameter_name = "has_ngo"

    def lookups(self, request, model_admin):
        return ("yes", "Yes"), ("no", "No")

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(ngo=None)
        if self.value() == "no":
            return queryset.filter(ngo=None)

        return queryset
