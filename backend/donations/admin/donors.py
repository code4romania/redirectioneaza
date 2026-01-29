import logging
from datetime import datetime, timedelta

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
from unfold.contrib.filters.admin import RangeDateFilter, TextFilter
from unfold.dataclasses import UnfoldAction
from unfold.decorators import action

from donations.models.donors import Donor
from redirectioneaza.common.app_url import build_uri
from redirectioneaza.common.async_wrapper import async_wrapper
from redirectioneaza.common.messaging import extend_email_context, send_email
from utils.common.admin import HasNgoFilter
from utils.constants.time import YEAR_IN_DAYS

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


def soft_delete_donor(donor_pk: int, notify: bool = False) -> str:
    logger.info(f"Deleting donor {donor_pk}")
    try:
        donor: Donor = Donor.available.get(pk=donor_pk)
        donor.disable()

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

        return TASK_SUCCESS_FLAG
    except Exception as e:
        logger.error(f"Failed to delete donor {donor_pk}: {e}")
        return TASK_FAILURE_FLAG


def remove_donor_data(donor: Donor) -> str:
    logger.info(f"Anonymizing donor {donor.pk}")

    try:
        donor.personal_data_removal_started_at = timezone.now()
        donor.save(update_fields=["personal_data_removal_started_at"])

        result = async_wrapper(donor.remove_personal_data, async_flag=settings.USER_ANONYMIZATION_METHOD)

        return TASK_SUCCESS_FLAG if result is None else TASK_SCHEDULED_FLAG
    except Exception as e:
        logger.error(f"Failed to anonymize donor {donor.pk}: {e}")
        return TASK_FAILURE_FLAG


def anonymize_old_donations():
    def remove_personal_data_in_bulk(selected_donors: QuerySet[Donor]):
        # run the remove_personal_data async for each donor in the selected_donors queryset
        for donor in selected_donors.iterator(chunk_size=500):
            remove_donor_data(donor)

    now: datetime = timezone.now()
    one_year_ago_date: datetime = now - timedelta(days=1 * YEAR_IN_DAYS)
    two_years_ago_date: datetime = now - timedelta(days=2 * YEAR_IN_DAYS)

    base_donor_qs: QuerySet[Donor] = Donor.objects.filter(personal_data_removal_started_at__isnull=True)

    remove_personal_data_in_bulk(base_donor_qs.filter(date_created__date__lte=two_years_ago_date))
    remove_personal_data_in_bulk(base_donor_qs.filter(two_years=False, date_created__lte=one_year_ago_date))


class HasPersonalDataFilter(admin.SimpleListFilter):
    title = _("Has personal data")
    parameter_name = "has_personal_data"
    horizontal = True

    def lookups(self, request, model_admin):
        return ("yes", "Yes"), ("no", "No")

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.exclude(personal_data_removed__isnull=False)
        if self.value() == "no":
            return queryset.filter(personal_data_removed__isnull=False)

        return queryset


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
    list_display = (
        "id",
        "email",
        "l_name",
        "f_name",
        "ngo",
        "is_available",
        "has_signed",
        "date_created",
    )
    list_display_links = ("id", "email", "l_name", "f_name")

    list_filter_submit = True
    list_filter = (
        ("date_created", RangeDateFilter),
        HasNgoFilter,
        HasPersonalDataFilter,
        "is_anonymous",
        "is_available",
        "has_signed",
        "two_years",
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

    actions = (
        "remove_donations_with_notification",
        "remove_donations_sans_notification",
        "anonymize_bulk_donations",
    )
    actions_list = (
        "run_redirections_stats_generator",
        "run_redirections_stats_generator_force",
        "run_anonymize_old_donations",
    )
    actions_detail = ("anonymize_single_donation",)

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=...):
        return False

    def get_actions_list(self, request: HttpRequest) -> list[UnfoldAction]:
        if not settings.ENABLE_BULK_ANONYMIZATION:
            self.actions_list = tuple(
                action_item for action_item in self.actions_list if action_item != "run_anonymize_old_donations"
            )

        return super().get_actions_list(request)

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
        task_results = {TASK_SUCCESS_FLAG: 0, TASK_FAILURE_FLAG: 0}

        queryset_size: int = queryset.count()
        for donor in queryset:
            task_result = soft_delete_donor(donor.pk, notify=notify)
            task_results[task_result] += 1

        message: str = _print_task_result(
            process="removal",
            task_results=task_results,
            queryset_size=queryset_size,
        )

        self.message_user(request, message)

    @action(description=_("Anonymize personal data of donations"), url_path="anonymize-donations")
    def anonymize_bulk_donations(self, request, queryset: QuerySet[Donor]):
        task_results = {TASK_SUCCESS_FLAG: 0, TASK_FAILURE_FLAG: 0, TASK_SCHEDULED_FLAG: 0}

        queryset_size: int = queryset.count()
        if queryset_size > 100:
            self.message_user(
                request,
                message=_(
                    "Anonymizing a large number of redirections is not allowed via bulk action. "
                    "This action should be done through a scheduled task or specific actions."
                ),
                level=messages.ERROR,
            )
            return

        for donor in queryset:
            task_result: str = remove_donor_data(donor)
            task_results[task_result] += 1

        message: str = _print_task_result(
            process="anonymization",
            task_results=task_results,
            queryset_size=queryset_size,
        )

        self.message_user(request, message)

    @action(description=_("Anonymize personal data of the donation"), url_path="anonymize-donation")
    def anonymize_single_donation(self, request: HttpRequest, object_id: int):
        def run_anonymize_donation_task(selected_donor: Donor) -> dict[str, str]:
            task_result: str = remove_donor_data(selected_donor)

            if task_result == TASK_SUCCESS_FLAG:
                message = _("The donor was successfully anonymized.")
            elif task_result == TASK_SCHEDULED_FLAG:
                message = _("The donor anonymization was scheduled for processing.")
            else:
                message = _("Failed to anonymize the donor. Check the logs for more details.")

            return {"status": task_result, "message": message}

        try:
            donor = Donor.objects.get(pk=object_id)
        except Donor.DoesNotExist:
            self.message_user(request, _("Donor not found."), level=messages.ERROR)
            return redirect(reverse_lazy("admin:donations_donor_changelist"))

        if request.method == "POST":
            form = AnonymizeDonorForm(request.POST)
            if form.is_valid():
                result: dict = run_anonymize_donation_task(donor)

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

    @action(description=_("Anonymize old donations"), url_path="anonymize-old-donations")
    def run_anonymize_old_donations(self, request):
        async_wrapper(anonymize_old_donations, async_flag=settings.USER_ANONYMIZATION_METHOD)

        self.message_user(request, _("Succesfully scheduled"))

        return redirect(reverse("admin:donations_donor_changelist"))
