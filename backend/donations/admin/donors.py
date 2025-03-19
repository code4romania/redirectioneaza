import logging

from django.contrib import admin, messages
from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from django_q.tasks import async_task, result
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import TextFilter
from unfold.decorators import action

from donations.models.donors import Donor
from redirectioneaza.common.admin import HasNgoFilter
from redirectioneaza.common.app_url import build_uri
from redirectioneaza.common.messaging import send_email

logger = logging.getLogger(__name__)

REMOVE_DONATIONS_GROUP_NAME = "REMOVE_DONATIONS"
REMOVE_DONATIONS_SUCCESS_MESSAGE = "success"
REMOVE_DONATIONS_FAILURE_MESSAGE = "failure"


def delete_donor(donor_pk: int):
    logger.info(f"Deleting donor {donor_pk}")
    try:
        donor = Donor.objects.get(pk=donor_pk)

        donor_email = donor.email
        cause = donor.cause

        donor.delete()

        send_email(
            subject=_("Donation removal"),
            to_emails=[donor_email],
            text_template="emails/donor/removed-redirection/main.txt",
            html_template="emails/donor/removed-redirection/main.html",
            context={
                "cause_name": cause.name,
                "action_url": build_uri(reverse("twopercent", kwargs={"ngo_url": cause.slug})),
            },
        )
        return REMOVE_DONATIONS_SUCCESS_MESSAGE
    except Exception as e:
        logger.error(f"Failed to delete donor {donor_pk}: {e}")
        return REMOVE_DONATIONS_FAILURE_MESSAGE


class CommonNumericFilter(TextFilter):
    def queryset(self, request: HttpRequest, queryset: QuerySet):
        if (filter_value := self.value()) not in EMPTY_VALUES:
            try:
                filter_int = int(filter_value)
                queryset_filter = {self.parameter_name: filter_int}
                return queryset.filter(**queryset_filter)
            except ValueError:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _("Invalid value for the %(title)s filter.") % {"title": self.title},
                )
                return redirect(reverse("admin:donations_donor_changelist"))

        return queryset


class NgoIdNumericListFilter(CommonNumericFilter):
    parameter_name = "ngo_id"
    title = _("NGO ID")


class CauseIdNumericListFilter(CommonNumericFilter):
    parameter_name = "cause_id"
    title = _("Cause ID")


@admin.register(Donor)
class DonorAdmin(ModelAdmin):
    list_display = ("id", "email", "l_name", "f_name", "ngo", "cause", "has_signed", "date_created")
    list_display_links = ("id", "email", "l_name", "f_name")

    list_filter_submit = True
    list_filter = (
        "date_created",
        HasNgoFilter,
        "is_anonymous",
        "has_signed",
        "two_years",
        "income_type",
        NgoIdNumericListFilter,
        CauseIdNumericListFilter,
    )

    date_hierarchy = "date_created"
    search_fields = ("email", "ngo__name", "ngo__slug")

    exclude = ("encrypted_cnp", "encrypted_address")

    readonly_fields = ("date_created", "get_form_url")
    autocomplete_fields = ("ngo",)

    fieldsets = (
        (
            _("NGO"),
            {"fields": ("ngo",)},
        ),
        (
            _("Identity"),
            {
                "fields": (
                    "l_name",
                    "f_name",
                    "initial",
                    "county",
                    "city",
                    "email",
                    "phone",
                )
            },
        ),
        (
            _("Info"),
            {"fields": ("is_anonymous", "income_type", "two_years")},
        ),
        (
            _("File"),
            {"fields": ("has_signed", "pdf_file", "get_form_url")},
        ),
        (
            _("Date"),
            {"fields": ("date_created", "geoip")},
        ),
    )

    actions = ("remove_donations",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=...):
        return False

    @admin.display(description=_("Form"))
    def get_form_url(self, obj: Donor):
        return obj.form_url

    @action(description=_("Remove donations and notify donors"), url_path="remove-donations")
    def remove_donations(self, request, queryset: QuerySet[Donor]):
        task_ids = []
        task_results = {
            "success": 0,
            "failure": 0,
        }

        queryset_size = queryset.count()
        for donor in queryset:
            task_id = async_task(delete_donor, donor.pk, group=REMOVE_DONATIONS_GROUP_NAME)
            task_ids.append(task_id)

        for task_id in task_ids:
            if task_id is None:
                task_results["failure"] += 1
                continue

            task_result = result(task_id)
            if task_result == REMOVE_DONATIONS_SUCCESS_MESSAGE:
                task_results["success"] += 1
            else:
                task_results["failure"] += 1

        part_1 = ngettext_lazy(
            singular="Out of %(queryset_size)d donor",
            plural="Out of %(queryset_size)d donors",
            number=queryset_size,
        ) % {"queryset_size": queryset_size}

        part_2 = ngettext_lazy(
            singular="%(success)d was deleted",
            plural="%(success)d were deleted",
            number=task_results["success"],
        ) % {"success": task_results["success"]}

        part_3 = ngettext_lazy(
            singular="%(failure)d was not deleted",
            plural="%(failure)d were not deleted",
            number=task_results["failure"],
        ) % {"failure": task_results["failure"]}

        self.message_user(request, ", ".join([part_1, part_2, part_3 + "."]))
