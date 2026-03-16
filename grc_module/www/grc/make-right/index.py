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
	context.csrf_token = frappe.sessions.get_csrf_token()

	cf = {"entreprise": context.company} if context.company else {}

	context.make_rights = frappe.db.get_list(
		"make_right_grc", filters=cf,
		fields=["name", "make_type", "name_maker", "email_maker", "phone_maker", "statut", "description", "updated_at"],
		order_by="modified desc",
	)

	statuts = [m.statut for m in context.make_rights]
	context.mr_summary = {
		"total": len(statuts),
		"recue": statuts.count("Reçue"),
		"en_cours": sum(1 for s in statuts if s in ["En cours", "Vérifiée"]),
		"terminee": statuts.count("Terminée"),
		"rejetee": statuts.count("rejetée"),
	}

	# Company list for new request form (clients pre-filled, managers get dropdown)
	if context.company:
		co = frappe.db.get_value("customer_grc", context.company, ["name", "entreprise"], as_dict=True)
		context.companies = [co] if co else []
	else:
		context.companies = frappe.db.get_list("customer_grc", fields=["name", "entreprise"], limit=100)

	context.notif_count = frappe.db.count("Notification Log", {"for_user": frappe.session.user, "read": 0})
