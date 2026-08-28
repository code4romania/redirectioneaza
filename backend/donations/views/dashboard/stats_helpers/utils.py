from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _


def format_yearly_stats(statistics) -> list[dict[str, int | list[dict]]]:
    return [
        {
            "year": statistic["year"],
            "stats": [
                {
                    "title": _("Donations"),
                    "icon": "edit_document",
                    "metric": statistic["donations"],
                    "label": statistic.get("donations_difference"),
                    "footer": format_stat_link(
                        url=f"{reverse('admin:donations_donor_changelist')}?date_created__year={statistic['year']}",
                        text=_("View all"),
                    ),
                    "timestamp": statistic["timestamp"],
                },
                {
                    "title": _("NGOs registered"),
                    "icon": "foundation",
                    "metric": statistic["ngos_registered"],
                    "label": statistic.get("ngos_registered_difference"),
                    "footer": format_stat_link(
                        url=f"{reverse('admin:donations_ngo_changelist')}?date_created__year={statistic['year']}",
                        text=_("View all"),
                    ),
                    "timestamp": statistic["timestamp"],
                },
                {
                    "title": _("NGOs with forms"),
                    "icon": "foundation",
                    "metric": statistic["ngos_with_forms"],
                    "label": statistic.get("ngos_with_forms_difference"),
                    "footer": format_stat_link(
                        url=f"{reverse('admin:donations_ngo_changelist')}?has_forms=1&date_created__year={statistic['year']}",
                        text=_("View all"),
                    ),
                    "timestamp": statistic["timestamp"],
                },
            ],
        }
        for statistic in statistics
    ]


def format_stat_link(url: str, text) -> str:
    # IDEs may wrongly display a deprecation warning; in this case, the usage is deprecated without *args or **kwargs.
    # noinspection PyDeprecation
    return format_html(
        '<a href="{url}" class="text-orange-700 font-semibold">{text}</a>',
        url=url,
        text=text,
    )
