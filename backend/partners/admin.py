from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.forms import Form
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action
from unfold.widgets import UnfoldAdminEmailInputWidget, UnfoldAdminTextInputWidget

from redirectioneaza.common.messaging import extend_email_context, send_email
from users.groups_management import PARTNER_MANAGER

from .models import Partner

UserModel = get_user_model()


class AddNewCausePartnerManagerForm(Form):
    first_name = forms.CharField(
        label=_("First Name"),
        help_text=_("The first name of the user who will be the administering the Partner."),
        required=True,
        widget=UnfoldAdminTextInputWidget,
    )
    last_name = forms.CharField(
        label=_("Last Name"),
        help_text=_("The last name of the user who will be the administering the Partner."),
        required=True,
        widget=UnfoldAdminTextInputWidget,
    )

    user_email = forms.EmailField(
        label=_("User Email"),
        help_text=_("The email address of the user who will be the administering the Partner."),
        required=True,
        widget=UnfoldAdminEmailInputWidget,
    )


class CausePartnerInline(TabularInline):
    model = Partner.causes.through
    extra = 1
    tab = True

    verbose_name = _("Cause")
    verbose_name_plural = _("Causes")

    autocomplete_fields = ("cause",)


@admin.register(Partner)
class PartnerAdmin(ModelAdmin):
    list_display = (
        "subdomain",
        "name",
        "is_active",
    )
    list_filter = (
        "is_active",
        "date_updated",
        "custom_cta",
    )
    search_fields = (
        "subdomain",
        "name",
    )

    inlines = (CausePartnerInline,)
    readonly_fields = (
        "date_created",
        "date_updated",
    )

    fieldsets = (
        (
            _("Partner"),
            {
                "fields": (
                    "subdomain",
                    "name",
                )
            },
        ),
        (
            _("Options"),
            {
                "fields": (
                    "is_active",
                    "custom_cta",
                    "display_ordering",
                )
            },
        ),
        (
            _("Metadata"),
            {
                "fields": (
                    "date_created",
                    "date_updated",
                )
            },
        ),
    )

    actions_detail = ("invite_new_owner",)

    def _invite_new_owner(self, request: HttpRequest, form: AddNewCausePartnerManagerForm, partner: Partner):
        first_name = form.cleaned_data["first_name"]
        last_name = form.cleaned_data["last_name"]
        user_email = form.cleaned_data["user_email"]

        try:
            new_user = UserModel.objects.create(
                email=user_email,
                first_name=first_name,
                last_name=last_name,
                partner=partner,
                is_staff=True,
            )
            new_user.set_unusable_password()
            new_user.save()
        except Exception as e:
            return {
                "status": "ERROR",
                "message": _("An error occurred while creating the user: %(error)s") % {"error": str(e)},
            }

        user_group_name = PARTNER_MANAGER
        user_group = Group.objects.get(name=user_group_name)
        new_user.groups.add(user_group)

        new_password_url = request.build_absolute_uri(
            reverse(
                "verification",
                kwargs={
                    "verification_type": "p",
                    "user_id": new_user.id,
                    "signup_token": new_user.refresh_token(),
                },
            )
        )
        template_context = {
            "first_name": new_user.first_name,
            "action_url": new_password_url,
            "contact_email": settings.CONTACT_EMAIL_ADDRESS,
        }
        template_context.update(extend_email_context(request))

        send_email(
            subject=_("Join redirectioneaza.ro"),
            to_emails=[new_user.email],
            text_template="emails/account/invite-partner/main.txt",
            html_template="emails/account/invite-partner/main.html",
            context=template_context,
        )

        return {
            "status": "SUCCESS",
            "message": _("The user has been successfully invited."),
        }

    @action(description=_("Invite new manager"))
    def invite_new_owner(self, request: HttpRequest, object_id):
        partner = self.get_object(request, object_id)

        if request.method == "POST":
            form = AddNewCausePartnerManagerForm(request.POST)
            if form.is_valid():
                result = self._invite_new_owner(request, form, partner)

                self.message_user(request, result["message"], level=result["status"])

                if result["status"] == "SUCCESS":
                    return redirect(reverse_lazy("admin:partners_partner_change", args=[object_id]))
            else:
                self.message_user(request, _("The form is not valid."), level="ERROR")
        else:
            form = AddNewCausePartnerManagerForm()

        return render(
            request,
            "admin/forms/action.html",
            {
                "form": form,
                "object": partner,
                "title": _("Invite new manager"),
                **self.admin_site.each_context(request),
            },
        )

    def has_view_permission(self, request, obj=...):
        return request.user.is_superuser or request.user.partner == obj

    def has_change_permission(self, request, obj=...):
        return request.user.is_superuser or request.user.partner == obj

    def has_delete_permission(self, request, obj=...):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser
