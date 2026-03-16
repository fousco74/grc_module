import frappe
from grc_module.utils import is_grc_client, get_client_company, require_portal_access

no_cache = 1


def get_context(context):
	require_portal_access()

	context.base_template = "grc_module/templates/layout.html"
	context.show_sidebar = False
	context.no_cache = 1
	context.user_fullname = frappe.session.data.full_name or frappe.session.user
	context.is_client = is_grc_client()
	context.company = get_client_company() if context.is_client else None

	cf = {"entreprise": context.company} if context.company else {}

	context.traitements = frappe.db.get_list(
		"traitement_grc", filters=cf,
		fields=["name", "traitement", "service", "entreprise"],
		order_by="traitement asc",
	)

	# Enrich with service name
	for t in context.traitements:
		if t.get("service"):
			t["service_name"] = frappe.db.get_value("service_grc", t["service"], "name_service") or t["service"]
		else:
			t["service_name"] = "—"

	# Service list for filter
	context.services = frappe.db.get_list(
		"service_grc",
		filters={"departement": ["in", [
			d.name for d in frappe.db.get_list("department_grc", filters=cf, fields=["name"])
		]]} if context.company else {},
		fields=["name", "name_service"],
	)

	context.notif_count = frappe.db.count("Notification Log", {"for_user": frappe.session.user, "read": 0})
