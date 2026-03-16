import frappe
from grc_module.utils import is_grc_client, get_client_company, calculate_compliance_score, require_portal_access

no_cache = 1


def get_context(context):
	require_portal_access()

	context.base_template = "grc_module/templates/layout.html"
	context.show_sidebar = False
	context.no_cache = 1
	context.user_fullname = frappe.session.data.full_name or frappe.session.user
	context.user_email = frappe.session.user
	context.is_client = is_grc_client()

	context.company = get_client_company() if context.is_client else None
	cf = {"entreprise": context.company} if context.company else {}

	# Company info
	if context.company:
		co = frappe.db.get_value(
			"customer_grc", context.company,
			["entreprise", "email_company", "statut", "compliance_score", "grc_manager", "etape_avancement"],
			as_dict=True,
		) or {}
		if co.get("grc_manager"):
			co["grc_manager_name"] = frappe.db.get_value("User", co["grc_manager"], "full_name") or co["grc_manager"]
		context.company_info = co
	else:
		context.company_info = {}

	# Score
	if context.company:
		context.compliance_score = calculate_compliance_score(context.company)
	else:
		scores = [s.compliance_score for s in frappe.db.get_list("customer_grc", fields=["compliance_score"]) if s.compliance_score]
		context.compliance_score = round(sum(scores) / len(scores), 1) if scores else 0

	# Raw data for KPIs
	violations = frappe.db.get_list("violation_grc", filters=cf, fields=["statut", "gravite"])
	action_plans = frappe.db.get_list("action_plan_grc", filters=cf, fields=["statut"])
	make_rights = frappe.db.get_list("make_right_grc", filters=cf, fields=["statut"])
	traitements = frappe.db.get_list("traitement_grc", filters=cf, fields=["name"])

	context.kpi = {
		"total_violations": len(violations),
		"critical_violations": sum(1 for v in violations if v.get("gravite") == "Critique"),
		"open_violations": sum(1 for v in violations if v.get("statut") != "Terminer"),
		"total_action_plans": len(action_plans),
		"open_action_plans": sum(1 for a in action_plans if a.get("statut") != "Terminer"),
		"completed_action_plans": sum(1 for a in action_plans if a.get("statut") == "Terminer"),
		"total_make_rights": len(make_rights),
		"pending_make_rights": sum(1 for m in make_rights if m.get("statut") in ["Reçue", "En cours", "Vérifiée"]),
		"total_traitements": len(traitements),
	}

	# Recent lists
	context.recent_violations = frappe.db.get_list(
		"violation_grc", filters=cf,
		fields=["name", "titre", "description", "statut", "gravite", "date_de_création"],
		order_by="date_de_création desc", limit=5,
	)
	context.recent_action_plans = frappe.db.get_list(
		"action_plan_grc", filters=cf,
		fields=["name", "titre", "description", "statut", "avancement", "délais_dexécution", "responsable"],
		order_by="modified desc", limit=5,
	)

	# Chart data
	sev = {"Critique": 0, "Haute": 0, "Moyenne": 0, "Faible": 0}
	for v in violations:
		g = v.get("gravite") or "Faible"
		if g in sev:
			sev[g] += 1
	context.severity_chart = sev

	ap_st = {"A faire": 0, "En cours": 0, "Terminer": 0}
	for a in action_plans:
		s = a.get("statut") or "A faire"
		if s in ap_st:
			ap_st[s] += 1
	context.ap_status_chart = ap_st

	context.notif_count = frappe.db.count("Notification Log", {"for_user": frappe.session.user, "read": 0})
