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

	context.action_plans = frappe.db.get_list(
		"action_plan_grc", filters=cf,
		fields=[
			"name", "titre", "description", "statut", "avancement",
			"responsable", "date_debut", "delais_dexecution", "date_de_fin",
			"principe_directeur", "violation",
		],
		order_by="delais_dexecution asc",
		ignore_permissions=True,
	)

	today = frappe.utils.today()
	statuts = [a.statut for a in context.action_plans]
	context.ap_summary = {
		"total": len(statuts),
		"a_faire": statuts.count("A faire"),
		"en_cours": statuts.count("En cours"),
		"terminer": statuts.count("Terminer"),
		"overdue": sum(
			1 for a in context.action_plans
			if a.get("delais_dexecution") and str(a.get("delais_dexecution")) < today
			and a.get("statut") != "Terminer"
		),
	}

	context.notif_count = frappe.db.count("Notification Log", {"for_user": frappe.session.user, "read": 0})
