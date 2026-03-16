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

	context.controls = frappe.db.get_list(
		"Point_de_controle", filters=cf,
		fields=["name", "titre", "description", "statut", "priorite", "service"],
		order_by="priorite asc, titre asc",
	)

	# Summary counts
	statuts = [c.statut for c in context.controls]
	context.audit_summary = {
		"total": len(statuts),
		"conforme": statuts.count("Conforme"),
		"partiel": statuts.count("Partiel"),
		"non_conforme": statuts.count("Non conforme"),
		"non_evalue": statuts.count("Non évalué"),
	}
	total = context.audit_summary["total"]
	context.audit_summary["score_pct"] = (
		round((context.audit_summary["conforme"] + context.audit_summary["partiel"] * 0.5) / total * 100)
		if total else 0
	)

	context.notif_count = frappe.db.count("Notification Log", {"for_user": frappe.session.user, "read": 0})
