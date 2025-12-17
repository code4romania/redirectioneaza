import logging

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.contrib.filters.admin import SingleNumericFilter
from unfold.decorators import action
from unfold.widgets import UnfoldAdminSelectWidget

from donations.admin.common import CommonCauseFields, span_external, span_internal
from donations.models.ngos import Cause, Ngo
from donations.workers.update_organization import update_organization
from users.models import User

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class ChangeNgoOwnerForm(forms.Form):
    existing_user = forms.ModelChoiceField(
        queryset=User.objects.filter(
            is_active=True,
            is_staff=False,
            is_ngohub_user=False,
            ngo__isnull=True,
        ),
        label=_("Existing User"),
        help_text=_("Select the new owner of the NGO. You can only select active users that don't have an NGO."),
        widget=UnfoldAdminSelectWidget,
    )

    # TODO: create the flow to create a new user from the admin
    # new_user_email = forms.EmailField(
    #     label=_("New User Email"),
    #     help_text=_("Enter the email of the new owner of the NGO. The user will be created."),
    #     widget=UnfoldAdminEmailInputWidget,
    # )


class NgoCauseInline(StackedInline, CommonCauseFields):
    model = Cause
    extra = 0
    tab = True

    readonly_fields = (
        "ngo",
        "date_created",
        "date_updated",
        "link_to_cause",
    )

    fieldsets = (
        (
            None,
            {"fields": ("link_to_cause",)},
        ),
        CommonCauseFields.flags_fieldset,
        CommonCauseFields.form_data_fieldset,
        CommonCauseFields.data_fieldset,
    )

    @admin.display(description=_("Cause link"))
    def link_to_cause(self, obj: Cause):
        link_url = reverse("admin:donations_cause_change", args=(obj.pk,))
        return span_internal(href=link_url, content=obj.name)

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj=...):
        return False


class NgoPartnerInline(TabularInline):
    # noinspection PyUnresolvedReferences
    model = Ngo.partners.through
    extra = 1
    tab = True

    autocomplete_fields = ("partner",)


class NgoUserInline(StackedInline):
    # noinspection PyUnresolvedReferences
    model = User
    extra = 0
    tab = True

    readonly_fields = ("link_to_user", "email", "first_name", "last_name", "is_active", "is_staff", "is_superuser")

    fieldsets = (
        (
            _("User Link"),
            {"fields": ("link_to_user",)},
        ),
        (
            _("User Details"),
            {"fields": ("email", "first_name", "last_name")},
        ),
        (
            _("User Permissions"),
            {"fields": ("is_active", "is_staff", "is_superuser")},
        ),
    )

    def has_add_permission(self, request, obj):
        return False

    @admin.display(description=_("User"))
    def link_to_user(self, obj: User):
        link_url = reverse("admin:users_user_change", args=(obj.pk,))
        return span_internal(href=link_url, content=obj.email)


class HasNgoHubFilter(admin.SimpleListFilter):
    title = _("Has NGO Hub account")
    parameter_name = "has_ngohub"

    def lookups(self, request, model_admin):
        return (1, _("Yes")), (0, _("No"))

    def queryset(self, request, queryset):
        filter_value = None
        if self.value() == "1":
            filter_value = True
        elif self.value() == "0":
            filter_value = False

        if filter_value is not None:
            return queryset.filter(ngohub_org_id__isnull=not filter_value)

        return queryset


class HasOwnerFilter(admin.SimpleListFilter):
    title = _("Has owner")
    parameter_name = "has_owner"

    def lookups(self, request, model_admin):
        return (1, _("Yes")), (0, _("No"))

    def queryset(self, request, queryset):
        filter_value = None
        if self.value() == "1":
            filter_value = True
        elif self.value() == "0":
            filter_value = False

        if filter_value is not None:
            return queryset.filter(users__isnull=filter_value)

        return queryset


@admin.register(Ngo)
class NgoAdmin(ModelAdmin):
    list_filter_submit = True

    list_display = ("id", "get_ngohub_link", "get_cif", "name", "has_online_tax_account", "is_active")
    list_display_links = ("id", "get_cif", "name", "has_online_tax_account")
    list_editable = ("is_active",)

    list_filter = (
        "date_created",
        HasNgoHubFilter,
        ("ngohub_org_id", SingleNumericFilter),
        "is_verified",
        "is_active",
        "has_online_tax_account",
        "partners",
        HasOwnerFilter,
        "county",
        "registration_number_valid",
    )
    list_per_page = 30

    search_fields = ("name", "registration_number")

    inlines = (NgoCauseInline, NgoPartnerInline, NgoUserInline)

    readonly_fields = ("date_created", "date_updated", "get_donations_link")

    actions_detail = ("change_owner",)

    actions = (
        "update_from_ngohub_sync",
        "update_from_ngohub_async",
    )

    actions_list = ("remove_prefilled_forms",)

    fieldsets = (
        (
            _("Donations"),
            {"fields": ("get_donations_link",)},
        ),
        (
            _("NGO"),
            {
                "fields": (
                    "vat_id",
                    "registration_number",
                    "ngohub_org_id",
                    "name",
                )
            },
        ),
        (
            _("Activity"),
            {
                "fields": (
                    "is_verified",
                    "is_active",
                    "has_online_tax_account",
                    "is_social_service_viable",
                )
            },
        ),
        (
            _("Contact"),
            {
                "fields": (
                    "address",
                    "locality",
                    "county",
                    "active_region",
                    "email",
                    "display_email",
                    "phone",
                    "display_phone",
                    "website",
                )
            },
        ),
        (
            _("Date"),
            {
                "fields": (
                    "date_created",
                    "date_updated",
                )
            },
        ),
    )

    def get_actions(self, request):
        if request.user.is_superuser:
            return super().get_actions(request)

        return []

    def get_actions_detail(self, request, object_id):
        if request.user.is_superuser:
            return super().get_actions_detail(request, object_id)

        return []

    def get_inlines(self, request, obj):
        if request.user.is_superuser:
            return super().get_inlines(request, obj)

        return []

    def get_queryset(self, request):
        if request.user.is_superuser:
            return super().get_queryset(request)

        return Ngo.active.all()

    def get_list_display(self, request: HttpRequest):
        if request.user.is_superuser:
            return super().get_list_display(request)

        return [
            "slug",
            "registration_number",
            "name",
        ]

    def get_fieldsets(self, request: HttpRequest, obj=None):
        if request.user.is_superuser:
            return super().get_fieldsets(request, obj)

        fieldsets = (
            (
                _("NGO"),
                {
                    "fields": (
                        "name",
                        "registration_number",
                    )
                },
            ),
        )

        return fieldsets

    @admin.display(description=_("NGO Hub link"))
    def get_ngohub_link(self, obj: Ngo):
        if not obj.ngohub_org_id:
            return "-"

        link_text = obj.ngohub_org_id
        link_url = f"{settings.NGOHUB_APP_BASE}organizations/{obj.ngohub_org_id}/overview"

        return span_external(href=link_url, content=str(link_text))

    @admin.display(description=_("CIF"))
    def get_cif(self, obj: Ngo):
        return obj.vat_id + obj.registration_number

    @admin.display(description=_("Donations"))
    def get_donations_link(self, obj: Ngo):
        link_name = _("Open the NGO donor list")
        link_url = reverse("admin:donations_donor_changelist")
        return format_html(
            f'<a data-popup="yes" id="ngo_donor_list" class="related-widget-wrapper-link" href="{link_url}?ngo_id={obj.id}&_popup=1" target="_blank">{link_name}</a>'
        )

    @transaction.atomic
    def _change_owner(self, ngo: Ngo, new_owner: User):
        if new_owner.ngo:
            return {
                "status": "ERROR",
                "message": _("This user already has an NGO."),
            }

        if new_owner.is_staff or new_owner.is_superuser:
            return {
                "status": "ERROR",
                "message": _("This user is a staff member."),
            }

        if new_owner.is_ngohub_user:
            return {
                "status": "ERROR",
                "message": _("This user is an NGO Hub user."),
            }

        old_user = UserModel.objects.get(ngo=ngo)
        old_user.ngo = None
        new_owner.ngo = ngo

        old_user.save()
        new_owner.save()

        return {
            "status": "SUCCESS",
            "message": _("Owner changed successfully."),
        }

    @action(description=_("Change owner"))
    def change_owner(self, request: HttpRequest, object_id):
        ngo = Ngo.objects.get(id=object_id)

        if request.method == "POST":
            form = ChangeNgoOwnerForm(request.POST)

            if form.is_valid():
                new_owner = form.cleaned_data["existing_user"]

                result = self._change_owner(ngo, new_owner)

                self.message_user(request, result["message"], level=result["status"])

                if result["status"] == "SUCCESS":
                    return redirect(reverse_lazy("admin:app_model_change", args=[object_id]))
            else:
                self.message_user(request, _("The form is not valid."), level="ERROR")
        else:
            form = ChangeNgoOwnerForm()

        return render(
            request,
            "admin/forms/action.html",
            {
                "form": form,
                "object": ngo,
                "title": _("Change owner of NGO '%(name)s'") % {"name": ngo.name},
                **self.admin_site.each_context(request),
            },
        )

    @action(description=_("Update from NGO Hub synchronously"))
    def update_from_ngohub_sync(self, request, queryset: QuerySet[Ngo]):
        for ngo in queryset:
            update_organization(ngo.id, update_method="sync")

        self.message_user(request, _("NGOs updated from NGO Hub."))

    @action(description=_("Update from NGO Hub asynchronously"))
    def update_from_ngohub_async(self, request, queryset: QuerySet[Ngo]):
        for ngo in queryset:
            update_organization(ngo.id, update_method="async")

        self.message_user(request, _("NGOs are being updated from NGO Hub."))

    @action(description=_("Remove prefilled forms"), url_path="remove-forms", permissions=["remove_forms"])
    def remove_prefilled_forms(self, request: HttpRequest):
        causes = Cause.objects.exclude(prefilled_form="")

        removed_count = 0
        expected_count = causes.count()

        errors = []

        for cause in causes:
            try:
                cause.prefilled_form.delete()
                removed_count += 1
            except Exception as e:
                errors.append("Error removing `form_url` from cause {0}: {1}".format(cause.pk, e))

        result_message = f"Total of {removed_count}/{expected_count} prefilled forms removed."
        if errors:
            self.message_user(request, "\n".join([result_message] + errors), level="ERROR")
        else:
            self.message_user(request, result_message, level="SUCCESS")

        return redirect(reverse_lazy("admin:donations_ngo_changelist"))

    def has_remove_forms_permission(self, request: HttpRequest, object_id=None):
        return request.user.is_superuser
