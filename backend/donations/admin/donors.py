import logging

from django.contrib import admin, messages
from django.core.management import call_command
from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import TextFilter
from unfold.decorators import action

from donations.models.donors import Donor
from redirectioneaza.common.app_url import build_uri
from redirectioneaza.common.messaging import extend_email_context, send_email
from utils.common.admin import HasNgoFilter

logger = logging.getLogger(__name__)

REMOVE_DONATIONS_SUCCESS_FLAG = "success"
REMOVE_DONATIONS_FAILURE_FLAG = "failure"


def soft_delete_donor(donor_pk: int, notify: bool = False) -> str:
    logger.info(f"Deleting donor {donor_pk}")
    try:
        donor = Donor.available.get(pk=donor_pk)
        donor.remove()

        if notify:
            if donor.cause:
                mail_context = {
                    "cause_name": donor.cause.name,
                    "action_url": build_uri(reverse("twopercent", kwargs={"cause_slug": donor.cause.slug})),
                }
            else:
                mail_context = {
                    "cause_name": _("<Cause no longer available>"),
                    "action_url": build_uri(reverse("home")),
                }
            mail_context.update(extend_email_context())

            send_email(
                subject=_("Donation removal"),
                to_emails=[donor.email],
                text_template="emails/donor/removed-redirection-admin/main.txt",
                html_template="emails/donor/removed-redirection-admin/main.html",
                context=mail_context,
            )

        return REMOVE_DONATIONS_SUCCESS_FLAG
    except Exception as e:
        logger.error(f"Failed to delete donor {donor_pk}: {e}")
        return REMOVE_DONATIONS_FAILURE_FLAG


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
    list_display = ("id", "email", "l_name", "f_name", "ngo", "is_available", "has_signed", "date_created")
    list_display_links = ("id", "email", "l_name", "f_name")

    list_filter_submit = True
    list_filter = (
        "date_created",
        HasNgoFilter,
        "is_anonymous",
        "is_available",
        "has_signed",
        "two_years",
        "income_type",
        NgoIdNumericListFilter,
        CauseIdNumericListFilter,
    )

    date_hierarchy = "date_created"
    search_fields = ("email", "ngo__name")

    exclude = ("encrypted_cnp", "encrypted_address")

    readonly_fields = ("date_created", "get_form_url")
    autocomplete_fields = ("ngo",)

    fieldsets = (
        (
            _("Availability"),
            {"fields": ("is_available",)},
        ),
        (
            _("NGO"),
            {"fields": ("ngo", "cause")},
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

    actions = ("remove_donations_with_notification", "remove_donations_sans_notification")
    actions_list = ("run_redirections_stats_generator", "run_redirections_stats_generator_force")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=...):
        return False

    @admin.display(description=_("Form"))
    def get_form_url(self, obj: Donor):
        return obj.form_url

    @action(description=_("Remove donations and notify donors"), url_path="remove-donations")
    def remove_donations_with_notification(self, request, queryset: QuerySet[Donor]):
        self._remove_donations(request=request, queryset=queryset, notify=True)

    @action(description=_("Remove donations without notifying donors"), url_path="remove-donations-sans-notification")
    def remove_donations_sans_notification(self, request, queryset: QuerySet[Donor]):
        self._remove_donations(request=request, queryset=queryset, notify=False)

    def _remove_donations(self, *, request, queryset: QuerySet[Donor], notify: bool):
        task_results = {REMOVE_DONATIONS_SUCCESS_FLAG: 0, REMOVE_DONATIONS_FAILURE_FLAG: 0}

        queryset_size = queryset.count()
        for donor in queryset:
            task_result = soft_delete_donor(donor.pk, notify=notify)
            task_results[task_result] += 1

        part_1 = ngettext_lazy(
            singular="Out of %(queryset_size)d donor",
            plural="Out of %(queryset_size)d donors",
            number=queryset_size,
        ) % {"queryset_size": queryset_size}

        part_2 = ngettext_lazy(
            singular="%(success)d was deleted",
            plural="%(success)d were deleted",
            number=task_results[REMOVE_DONATIONS_SUCCESS_FLAG],
        ) % {"success": task_results[REMOVE_DONATIONS_SUCCESS_FLAG]}

        part_3 = ngettext_lazy(
            singular="%(failure)d was not deleted",
            plural="%(failure)d were not deleted",
            number=task_results[REMOVE_DONATIONS_FAILURE_FLAG],
        ) % {"failure": task_results[REMOVE_DONATIONS_FAILURE_FLAG]}

        self.message_user(request, ", ".join([part_1, part_2, part_3 + "."]))

    @action(description=_("Schedule redirections stats"), url_path="schedule-redirections-stats-generator")
    def run_redirections_stats_generator(self, request, queryset: QuerySet[Donor]):
        call_command("generate_redirections_stats")

    @action(description=_("Schedule redirections stats [FORCE]"), url_path="schedule-redirections-stats-generator-f")
    def run_redirections_stats_generator_force(self, request, queryset: QuerySet[Donor]):
        call_command("generate_redirections_stats", "--force")
