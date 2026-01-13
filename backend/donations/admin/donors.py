import logging
from datetime import timedelta

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.contrib.messages import DEFAULT_LEVELS
from django.core.management import CommandError, call_command
from django.core.validators import EMPTY_VALUES
from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import TextFilter
from unfold.decorators import action

from donations.models.donors import Donor
from redirectioneaza.common.app_url import build_uri
from redirectioneaza.common.async_wrapper import async_wrapper
from redirectioneaza.common.messaging import extend_email_context, send_email
from utils.common.admin import HasNgoFilter
from utils.constants.time import YEAR

logger = logging.getLogger(__name__)

TASK_SUCCESS_FLAG = "SUCCESS"
TASK_FAILURE_FLAG = "ERROR"
TASK_SCHEDULED_FLAG = "SCHEDULED"


class AnonymizeDonorForm(forms.Form):
    confirmation = forms.MultipleChoiceField(
        label=_("Please confirm"),
        help_text=_(
            "This action will PERMANENTLY anonymize the selected donor's personal data, "
            "removing any personally identifiable information and the form itself. "
            "THIS ACTION CANNOT BE UNDONE."
        ),
        choices=[("yes", _("Yes, I want to anonymize this donor"))],
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )


def _print_task_result(process: str, task_results: dict[str, int], queryset_size: int) -> str:
    message_parts: list[str] = [
        ngettext_lazy(
            singular="Out of %(queryset_size)d donor, the %(process)s results were:",
            plural="Out of %(queryset_size)d donors, the %(process)s results were:",
            number=queryset_size,
        )
        % {
            "queryset_size": queryset_size,
            "process": process.upper(),
        }
    ]

    if task_results.get(TASK_SUCCESS_FLAG):
        message_parts.append(
            ngettext_lazy(
                singular="%(success)d was processed",
                plural="%(success)d were processed",
                number=task_results[TASK_SUCCESS_FLAG],
            )
            % {"success": task_results[TASK_SUCCESS_FLAG]}
        )

    if task_results.get(TASK_FAILURE_FLAG):
        message_parts.append(
            ngettext_lazy(
                singular="%(failure)d was not processed",
                plural="%(failure)d were not processed",
                number=task_results[TASK_FAILURE_FLAG],
            )
            % {"failure": task_results[TASK_FAILURE_FLAG]}
        )

    if task_results.get(TASK_SCHEDULED_FLAG):
        message_parts.append(
            ngettext_lazy(
                singular="%(scheduled)d was scheduled for processing",
                plural="%(scheduled)d were scheduled for processing",
                number=task_results[TASK_SCHEDULED_FLAG],
            )
            % {"scheduled": task_results[TASK_SCHEDULED_FLAG]}
        )

    message_parts[-1] += "."

    return ", ".join(message_parts)


def soft_delete_donor(donor_pk: int):
    logger.info(f"Deleting donor {donor_pk}")
    try:
        donor = Donor.available.get(pk=donor_pk)
        donor.remove()

        mail_context = {
            "cause_name": donor.cause.name,
            "action_url": build_uri(reverse("twopercent", kwargs={"cause_slug": donor.cause.slug})),
        }
        mail_context.update(extend_email_context())

        send_email(
            subject=_("Donation removal"),
            to_emails=[donor.email],
            text_template="emails/donor/removed-redirection/main.txt",
            html_template="emails/donor/removed-redirection/main.html",
            context=mail_context,
        )
        return TASK_SUCCESS_FLAG
    except Exception as e:
        logger.error(f"Failed to delete donor {donor_pk}: {e}")
        return TASK_FAILURE_FLAG


def anonymize_donor(donor: Donor):
    logger.info(f"Anonymizing donor {donor.pk}")

    try:
        if settings.USER_ANONIMIZATION_METHOD == "async":
            async_wrapper(donor.anonymize)
            return TASK_SCHEDULED_FLAG

        donor.anonymize()
    except Exception as e:
        logger.error(f"Failed to anonymize donor {donor.pk}: {e}")
        return TASK_FAILURE_FLAG

    return TASK_SUCCESS_FLAG


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

    actions = ("remove_donations", "anonymize_donations")
    actions_list = (
        "run_redirections_stats_generator",
        "run_redirections_stats_generator_force",
        "anonymize_old_donations",
    )
    actions_detail = ("anonymize_donation",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=...):
        return False

    @admin.display(description=_("Form"))
    def get_form_url(self, obj: Donor):
        return obj.form_url

    @action(description=_("Remove donations and notify donors"), url_path="remove-donations")
    def remove_donations(self, request, queryset: QuerySet[Donor]):
        task_results = {TASK_SUCCESS_FLAG: 0, TASK_FAILURE_FLAG: 0}

        queryset_size = queryset.count()
        for donor in queryset:
            task_result = soft_delete_donor(donor.pk)
            task_results[task_result] += 1

        message: str = _print_task_result(
            process="removal",
            task_results=task_results,
            queryset_size=queryset_size,
        )

        self.message_user(request, message)

    @action(description=_("Anonymize public data of donations"), url_path="anonymize-donations")
    def anonymize_donations(self, request, queryset: QuerySet[Donor]):
        task_results = {TASK_SUCCESS_FLAG: 0, TASK_FAILURE_FLAG: 0, TASK_SCHEDULED_FLAG: 0}

        queryset_size = queryset.count()
        for donor in queryset:
            task_result = anonymize_donor(donor)
            task_results[task_result] += 1

        message: str = _print_task_result(
            process="anonymization",
            task_results=task_results,
            queryset_size=queryset_size,
        )

        self.message_user(request, message)

    def _anonymize_donation(self, donor: Donor) -> dict[str, str]:
        task_result = anonymize_donor(donor)

        if task_result == TASK_SUCCESS_FLAG:
            message = _("The donor was successfully anonymized.")
        elif task_result == TASK_SCHEDULED_FLAG:
            message = _("The donor anonymization was scheduled for processing.")
        else:
            message = _("Failed to anonymize the donor. Check the logs for more details.")

        return {"status": task_result, "message": message}

    @action(description=_("Anonymize public data of the donation"), url_path="anonymize-donation")
    def anonymize_donation(self, request: HttpRequest, object_id: int):
        donor = Donor.objects.get(pk=object_id)

        if request.method == "POST":
            form = AnonymizeDonorForm(request.POST)
            if form.is_valid():
                result: dict = self._anonymize_donation(donor)

                self.message_user(request, result["message"], level=DEFAULT_LEVELS.get(result["status"], messages.INFO))

                return redirect(reverse_lazy("admin:donations_donor_change", args=[donor.pk]))
            else:
                messages.error(request, _("Please confirm the anonymization by checking the box."))
        else:
            form = AnonymizeDonorForm()

        return render(
            request,
            "admin/forms/action.html",
            context={
                "form": form,
                "object": donor,
                "title": _("Anonymize donor"),
                **self.admin_site.each_context(request),
            },
        )

        return redirect(reverse_lazy("admin:donations_donor_change", args=[donor.pk]))

    @action(description=_("Schedule redirections stats"), url_path="schedule-redirections-stats-generator")
    def run_redirections_stats_generator(self, request):
        try:
            call_command("generate_redirections_stats")
        except CommandError:
            self.message_user(request, _("Error calling the command"))

        self.message_user(request, _("Succesfully scheduled"))

    @action(description=_("Schedule redirections stats [FORCE]"), url_path="schedule-redirections-stats-generator-f")
    def run_redirections_stats_generator_force(self, request):
        try:
            call_command("generate_redirections_stats", "--force")
        except CommandError:
            self.message_user(request, _("Error calling the command"))

        self.message_user(request, _("Succesfully scheduled"))

    def _anonymize_old_donations(self):
        try:
            now = timezone.now()
            one_year_ago_date = now - timedelta(days=YEAR)
            two_years_ago_date = now - timedelta(days=2 * YEAR)

            base_donor_qs = Donor.objects.exclude(
                l_name="",
                f_name="",
            )

            one_year_donations_qs: QuerySet[Donor] = base_donor_qs.filter(
                two_years=False,
                date_created__lte=one_year_ago_date,
            )
            two_year_donations_qs: QuerySet[Donor] = base_donor_qs.filter(
                date_created__lte=two_years_ago_date,
            )

            for donor in two_year_donations_qs:
                anonymize_donor(donor)
            for donor in one_year_donations_qs:
                anonymize_donor(donor)

        except CommandError:
            logger.error("Error calling the anonymize_old_donations command")
            raise

    @action(description=_("Anonymize old donations"), url_path="anonymize-old-donations")
    def anonymize_old_donations(self, request):
        try:
            self._anonymize_old_donations()
        except CommandError:
            self.message_user(request, _("Error calling the command"))

        self.message_user(request, _("Succesfully scheduled"))
