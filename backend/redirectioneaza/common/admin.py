from django.contrib import admin


class HasNgoFilter(admin.SimpleListFilter):
    title = "Has NGO"
    parameter_name = "has_ngo"

    def lookups(self, request, model_admin):
        return ("yes", "Yes"), ("no", "No")

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(ngo=None)
        if self.value() == "no":
            return queryset.filter(ngo=None)
