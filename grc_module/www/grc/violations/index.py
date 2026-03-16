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

	context.violations = frappe.db.get_list(
		"violation_grc", filters=cf,
		fields=[
			"name", "titre", "description", "statut", "gravite",
			"type_violation", "responsable", "date_de_création",
			"date_de_fin", "observation", "notes_resolution",
		],
		order_by="gravite asc, date_de_création desc",
	)

	# Summary
	gravites = [v.get("gravite") or "Faible" for v in context.violations]
	statuts = [v.get("statut") or "A faire" for v in context.violations]
	context.viol_summary = {
		"total": len(context.violations),
		"critique": gravites.count("Critique"),
		"haute": gravites.count("Haute"),
		"moyenne": gravites.count("Moyenne"),
		"faible": gravites.count("Faible"),
		"open": sum(1 for s in statuts if s not in ["Terminer", "Terminé"]),
		"closed": sum(1 for s in statuts if s in ["Terminer", "Terminé"]),
	}

	# Type distribution
	types = {}
	for v in context.violations:
		t = v.get("type_violation") or "Non défini"
		types[t] = types.get(t, 0) + 1
	context.type_distribution = types

	context.notif_count = frappe.db.count("Notification Log", {"for_user": frappe.session.user, "read": 0})
