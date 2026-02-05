from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse

from orders.dashboard import orders_dashboard_stats


class CustomAdminSite(AdminSite):
    site_header = "Business Control Panel"
    site_title = "Control Panel"
    index_title = "Панель управления бизнесом"

    def index(self, request, extra_context=None):
        stats, funnel = orders_dashboard_stats()

        context = {
            **self.each_context(request),
            "stats": stats,
            "funnel": funnel,
        }
        return TemplateResponse(request, "admin/index.html", context)
