MAIN_ADMIN = "main admin"
RESTRICTED_ADMIN = "restricted admin"

USER_GROUPS = {
    MAIN_ADMIN: {
        "is_superuser": True,
        "permissions": "*",
    },
    RESTRICTED_ADMIN: {
        "is_superuser": False,
        "permissions": (
            "donations.delete_donor",
            "donations.view_donor",
            "donations.add_job",
            "donations.change_job",
            "donations.view_job",
            "donations.add_ngo",
            "donations.change_ngo",
            "donations.view_ngo",
            "partners.add_partner",
            "partners.change_partner",
            "partners.delete_partner",
            "partners.view_partner",
            "users.can_view_old_dashboard",
        ),
    },
}
