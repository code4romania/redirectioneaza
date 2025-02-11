MAIN_ADMIN = "main admin"
RESTRICTED_ADMIN = "restricted admin"
NGO_ADMIN = "ngo admin"
NGO_MEMBER = "ngo member"
PARTNER_MANAGER = "partner manager"

USER_GROUPS = {
    MAIN_ADMIN: {
        "is_superuser": True,
        "is_staff": True,
        "permissions": "*",
    },
    RESTRICTED_ADMIN: {
        "is_superuser": False,
        "is_staff": True,
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
    NGO_ADMIN: {
        "is_superuser": False,
        "is_staff": False,
        "permissions": (
            "donations.delete_donor",
            "donations.view_donor",
            "donations.add_job",
            "donations.change_job",
            "donations.view_job",
            "partners.delete_partner",
            "partners.view_partner",
        ),
    },
    NGO_MEMBER: {
        "is_superuser": False,
        "is_staff": False,
        "permissions": (
            "donations.view_donor",
            "donations.view_job",
            "partners.view_partner",
        ),
    },
    PARTNER_MANAGER: {
        "is_superuser": False,
        "is_staff": True,
        "permissions": (
            "partners.change_partner",
            "partners.view_partner",
            "partners.add_partnerngo",
            "partners.change_partnerngo",
            "partners.delete_partnerngo",
            "partners.view_partnerngo",
            "donations.view_ngo",
        ),
    },
}
