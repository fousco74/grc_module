"""GRC Module – Whitelisted API endpoints for the client portal."""

import frappe
from frappe import _
from grc_module.utils import (
	get_client_company,
	is_grc_client,
	is_grc_internal_user,
	calculate_compliance_score,
)


def _require_grc_access():
	"""Raise PermissionError if user has no GRC access."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentification requise"), frappe.AuthenticationError)
	if not (is_grc_client() or is_grc_internal_user()):
		frappe.throw(_("Accès non autorisé"), frappe.PermissionError)


def _get_company_filter():
	"""Return filters dict scoped to the current user's company (or empty for managers)."""
	if is_grc_client():
		company = get_client_company()
		return {"entreprise": company} if company else None
	return {}


# ── Dashboard ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_dashboard_data():
	_require_grc_access()
	filters = _get_company_filter()
	if filters is None:
		return {"error": "no_company"}

	violations = frappe.db.get_list("violation_grc", filters=filters, fields=["statut", "gravite"])
	action_plans = frappe.db.get_list("action_plan_grc", filters=filters, fields=["statut"])
	make_rights = frappe.db.get_list("make_right_grc", filters=filters, fields=["statut"])
	traitements = frappe.db.get_list("traitement_grc", filters=filters, fields=["name"])

	company = filters.get("entreprise") if filters else None
	score = calculate_compliance_score(company) if company else 0

	return {
		"compliance_score": score,
		"total_violations": len(violations),
		"critical_violations": sum(1 for v in violations if v.get("gravite") == "Critique"),
		"open_violations": sum(1 for v in violations if v.get("statut") != "Terminer"),
		"open_action_plans": sum(1 for a in action_plans if a.get("statut") not in ["Terminer", "Terminé"]),
		"completed_action_plans": sum(1 for a in action_plans if a.get("statut") in ["Terminer", "Terminé"]),
		"pending_make_rights": sum(1 for m in make_rights if m.get("statut") in ["Reçue", "Vérifiée", "En cours"]),
		"total_traitements": len(traitements),
	}


# ── Notifications ────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_notifications(limit=10):
	_require_grc_access()
	notifs = frappe.db.get_list(
		"Notification Log",
		filters={"for_user": frappe.session.user},
		fields=["name", "subject", "email_content", "creation", "read", "document_type", "document_name"],
		order_by="creation desc",
		limit=int(limit),
	)
	return notifs


@frappe.whitelist()
def mark_notification_read(name):
	_require_grc_access()
	doc = frappe.get_doc("Notification Log", name)
	if doc.for_user != frappe.session.user:
		frappe.throw(_("Accès non autorisé"), frappe.PermissionError)
	frappe.db.set_value("Notification Log", name, "read", 1)
	return {"status": "ok"}


@frappe.whitelist()
def mark_all_notifications_read():
	_require_grc_access()
	frappe.db.set_value(
		"Notification Log",
		{"for_user": frappe.session.user, "read": 0},
		"read", 1,
	)
	return {"status": "ok"}


# ── Documents ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def create_grc_document(entreprise, titre, type_document=None, description=None, fichier=None):
	_require_grc_access()

	# Clients can only create documents for their own company
	if is_grc_client():
		company = get_client_company()
		if entreprise != company:
			frappe.throw(_("Vous ne pouvez créer des documents que pour votre entreprise."), frappe.PermissionError)

	doc = frappe.get_doc({
		"doctype": "grc_document",
		"entreprise": entreprise,
		"titre": titre,
		"type_document": type_document,
		"description": description,
		"fichier": fichier,
		"televerse_par": frappe.session.user,
		"visibilite": "Client" if is_grc_client() else "Interne",
	})
	doc.insert(ignore_permissions=False)
	return {"name": doc.name, "status": "created"}


@frappe.whitelist()
def get_grc_documents(entreprise=None, type_document=None):
	_require_grc_access()
	filters = {}

	if is_grc_client():
		company = get_client_company()
		if not company:
			return []
		filters["entreprise"] = company
		filters["visibilite"] = ["in", ["Client", "Public"]]
	elif entreprise:
		filters["entreprise"] = entreprise

	if type_document:
		filters["type_document"] = type_document

	return frappe.db.get_list(
		"grc_document",
		filters=filters,
		fields=["name", "titre", "type_document", "fichier", "televerse_par", "visibilite", "creation", "description"],
		order_by="creation desc",
	)


# ── Make Right (Access Rights Requests) ─────────────────────────────────────

@frappe.whitelist()
def create_make_right(entreprise, make_type, name_maker, email_maker, phone_maker=None, description=None):
	_require_grc_access()

	if is_grc_client():
		company = get_client_company()
		if entreprise != company:
			frappe.throw(_("Accès non autorisé"), frappe.PermissionError)

	doc = frappe.get_doc({
		"doctype": "make_right_grc",
		"entreprise": entreprise,
		"make_type": make_type,
		"name_maker": name_maker,
		"email_maker": email_maker,
		"phone_maker": phone_maker,
		"description": description,
		"statut": "Reçue",
	})
	doc.insert(ignore_permissions=False)
	return {"name": doc.name, "status": "created"}


# ── Violations ───────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_violations(statut=None, gravite=None, limit=50):
	_require_grc_access()
	filters = _get_company_filter()
	if filters is None:
		return []
	if statut:
		filters["statut"] = statut
	if gravite:
		filters["gravite"] = gravite
	return frappe.db.get_list(
		"violation_grc",
		filters=filters,
		fields=[
			"name", "titre", "description", "statut", "gravite",
			"type_violation", "responsable", "date_de_création", "date_de_fin",
		],
		order_by="gravite asc, date_de_création desc",
		limit=int(limit),
	)


# ── Action Plans ──────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_action_plans(statut=None, limit=50):
	_require_grc_access()
	filters = _get_company_filter()
	if filters is None:
		return []
	if statut:
		filters["statut"] = statut
	return frappe.db.get_list(
		"action_plan_grc",
		filters=filters,
		fields=[
			"name", "titre", "description", "statut", "avancement",
			"responsable", "date_debut", "délais_dexécution", "violation",
		],
		order_by="délais_dexécution asc",
		limit=int(limit),
	)


# ── Company info ─────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_company_info():
	_require_grc_access()
	if is_grc_client():
		company_name = get_client_company()
		if not company_name:
			return None
		company = frappe.db.get_value(
			"customer_grc", company_name,
			["name", "entreprise", "email_company", "statut", "compliance_score", "grc_manager", "onboarding_date"],
			as_dict=True,
		)
		if company and company.get("grc_manager"):
			company["grc_manager_name"] = frappe.db.get_value("User", company["grc_manager"], "full_name")
		return company
	return None
