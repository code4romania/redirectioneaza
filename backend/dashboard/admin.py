from unfold.sites import UnfoldAdminSite
from django.utils.translation import gettext_lazy as _


class NgoDashboardSite(UnfoldAdminSite):
    index_title = _("Welcome")
    index_template = "dashboard/index.html"
    site_header = _("NGO Dashboard")
    site_title = _("NGO Dashboard")
    site_url = None

    def each_context(self, request):
        context = super().each_context(request)
        context.update(
            {
                "NGO_DASHBOARD": True,
            }
        )
        return context
    
    def has_permission(self, request):
        """
        Allow dashboard access for non-staff users too
        """
        return request.user.is_active


ngo_dashboard = NgoDashboardSite(name="dashboard")
