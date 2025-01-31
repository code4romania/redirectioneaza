import logging
from typing import Dict, List

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.http import HttpRequest
from django.template.loader import get_template, render_to_string
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from django_q.tasks import async_task

from redirectioneaza.common.app_url import build_uri

logger = logging.getLogger(__name__)


def extend_email_context(request: HttpRequest = None) -> Dict:
    return {
        "logo_code4romania": build_uri(static("images/code4romania.png"), request),
        "logo_instagram": build_uri(static("images/social-icons/instagram.png"), request),
        "logo_facebook": build_uri(static("images/social-icons/facebook.png"), request),
        "logo_github": build_uri(static("images/social-icons/github.png"), request),
        "logo_redirect": build_uri(static("images/logo.png"), request),
    }


def send_email(subject: str, to_emails: List[str], text_template: str, html_template: str, context: Dict):
    if settings.EMAIL_SEND_METHOD == "async":
        async_send_email(
            subject,
            to_emails,
            text_template,
            html_template,
            context,
        )
    elif settings.EMAIL_SEND_METHOD == "sync":
        send_emails(
            to_emails,
            subject,
            text_template,
            html_template,
            context,
        )
    else:
        raise ValueError(_("Invalid email send method. Must be 'async' or 'sync'."))


def async_send_email(
    subject: str,
    to_emails: List[str],
    text_template: str,
    html_template: str,
    html_context: Dict,
):
    logger.info(f"Asynchronously sending {len(to_emails)} emails with subject: {subject}.")

    async_task(
        send_emails,
        to_emails,
        subject,
        text_template,
        html_template,
        html_context,
    )


def send_emails(
    user_emails: List[str],
    subject: str,
    text_template: str,
    html_template: str,
    html_context: Dict,
):
    logger.info(f"Sending emails to {len(user_emails)} users.")

    for email in user_emails:
        text_body = render_to_string(text_template, context=html_context)

        html = get_template(html_template)
        html_content = html.render(html_context)

        from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, "DEFAULT_FROM_EMAIL") else settings.NO_REPLY_EMAIL

        msg = EmailMultiAlternatives(subject, text_body, from_email, [email])
        msg.attach_alternative(html_content, "text/html")

        msg.send(fail_silently=False)
