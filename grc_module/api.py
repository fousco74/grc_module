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
	"""Raise PermissionError if user is not a GRC client (portal APIs)."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentification requise"), frappe.AuthenticationError)
	if not is_grc_client():
		frappe.throw(_("Accès non autorisé"), frappe.PermissionError)


def _require_grc_internal_access():
	"""Raise PermissionError if user is not a GRC internal user (desk APIs)."""
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentification requise"), frappe.AuthenticationError)
	if not is_grc_internal_user():
		frappe.throw(_("Accès réservé aux gestionnaires GRC"), frappe.PermissionError)


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
			"type_violation", "responsable", "date_de_creation", "date_de_fin",
		],
		order_by="gravite asc, date_de_creation desc",
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
			"responsable", "date_debut", "delais_dexecution", "violation",
		],
		order_by="delais_dexecution asc",
		limit=int(limit),
	)


# ── Company info ─────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_violations_stats():
	"""Return violation counts grouped by gravite and statut for charts."""
	_require_grc_access()
	filters = _get_company_filter()
	if filters is None:
		return {}
	violations = frappe.db.get_list("violation_grc", filters=filters, fields=["statut", "gravite"])
	by_gravity = {}
	by_status = {}
	for v in violations:
		g = v.get("gravite") or "Inconnu"
		s = v.get("statut") or "Inconnu"
		by_gravity[g] = by_gravity.get(g, 0) + 1
		by_status[s] = by_status.get(s, 0) + 1
	return {"by_gravity": by_gravity, "by_status": by_status}


# ── Discussions ───────────────────────────────────────────────────────────────

_ALLOWED_DISCUSSION_DOCTYPES = {
	"violation_grc", "action_plan_grc", "make_right_grc", "grc_document",
}


def _check_doc_access(doctype, docname):
	"""Raise PermissionError if the current user cannot access this document."""
	if doctype not in _ALLOWED_DISCUSSION_DOCTYPES:
		frappe.throw(_("Type de document non autorisé"), frappe.PermissionError)
	if not frappe.has_permission(doctype, doc=docname):
		frappe.throw(_("Accès non autorisé"), frappe.PermissionError)


@frappe.whitelist()
def get_comments(doctype, docname):
	_require_grc_access()
	_check_doc_access(doctype, docname)
	comments = frappe.db.get_list(
		"Comment",
		filters={
			"reference_doctype": doctype,
			"reference_name": docname,
			"comment_type": "Comment",
		},
		fields=["name", "comment_by", "comment_by_fullname", "content", "creation"],
		order_by="creation asc",
		limit=100,
	)
	return comments


@frappe.whitelist()
def post_comment(doctype, docname, content):
	_require_grc_access()
	_check_doc_access(doctype, docname)
	content = (content or "").strip()
	if not content:
		frappe.throw(_("Le commentaire ne peut pas être vide."))
	doc = frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Comment",
		"reference_doctype": doctype,
		"reference_name": docname,
		"content": frappe.utils.escape_html(content),
		"comment_by": frappe.session.user,
	})
	doc.insert(ignore_permissions=True)
	return {
		"name": doc.name,
		"comment_by": doc.comment_by,
		"comment_by_fullname": frappe.db.get_value("User", doc.comment_by, "full_name") or doc.comment_by,
		"content": doc.content,
		"creation": str(doc.creation),
	}


@frappe.whitelist()
def get_company_info():
	_require_grc_access()
	if is_grc_client():
		company_name = get_client_company()
		if not company_name:
			return None
		company = frappe.db.get_value(
			"customer_grc", company_name,
			["name", "entreprise", "email_company", "statut", "compliance_score", "grc_manager", "onboarding_date", "etape_avancement"],
			as_dict=True,
		)
		if company and company.get("grc_manager"):
			company["grc_manager_name"] = frappe.db.get_value("User", company["grc_manager"], "full_name")
		return company
	return None


# ── Company Stats (for GRC Manager form dashboard) ───────────────────────────

def _count_by(items, field):
	result = {}
	for item in items:
		k = item.get(field) or "Inconnu"
		result[k] = result.get(k, 0) + 1
	return result


@frappe.whitelist()
def get_company_stats(company):
	"""Return detailed stats for a specific company — GRC Manager only."""
	_require_grc_internal_access()

	f = {"entreprise": company}
	today = frappe.utils.today()

	violations = frappe.db.get_list("violation_grc", filters=f, fields=["statut", "gravite"], ignore_permissions=True)
	action_plans = frappe.db.get_list("action_plan_grc", filters=f, fields=["statut", "delais_dexecution"], ignore_permissions=True)
	make_rights = frappe.db.get_list("make_right_grc", filters=f, fields=["statut"], ignore_permissions=True)
	documents = frappe.db.get_list("grc_document", filters=f, fields=["name"], ignore_permissions=True)
	controls = frappe.db.get_list("Point_de_controle", filters=f, fields=["statut"], ignore_permissions=True)
	traitements = frappe.db.get_list("traitement_grc", filters=f, fields=["name"], ignore_permissions=True)

	return {
		"compliance_score": frappe.db.get_value("customer_grc", company, "compliance_score") or 0,
		"violations": {
			"total": len(violations),
			"open": sum(1 for v in violations if v.get("statut") != "Terminer"),
			"critical": sum(1 for v in violations if v.get("gravite") == "Critique"),
			"by_gravity": _count_by(violations, "gravite"),
		},
		"action_plans": {
			"total": len(action_plans),
			"open": sum(1 for a in action_plans if a.get("statut") not in ["Terminer", "Terminé"]),
			"completed": sum(1 for a in action_plans if a.get("statut") in ["Terminer", "Terminé"]),
			"overdue": sum(
				1 for a in action_plans
				if a.get("delais_dexecution") and str(a.get("delais_dexecution")) < today
				and a.get("statut") not in ["Terminer", "Terminé"]
			),
			"by_status": _count_by(action_plans, "statut"),
		},
		"make_rights": {
			"total": len(make_rights),
			"pending": sum(1 for m in make_rights if m.get("statut") in ["Reçue", "Vérifiée", "En cours"]),
		},
		"documents": {"total": len(documents)},
		"controls": {
			"total": len(controls),
			"conforme": sum(1 for c in controls if c.get("statut") == "Conforme"),
			"non_conforme": sum(1 for c in controls if c.get("statut") == "Non conforme"),
			"by_status": _count_by(controls, "statut"),
		},
		"traitements": {"total": len(traitements)},
	}
