"""GRC Module – Security helpers, data access, event hooks."""

import frappe
from frappe import _


# ── Portal access guard ──────────────────────────────────────────────────────

def require_portal_access():
	"""Redirect to /login for guests, to / for non-GRC authenticated users."""
	if frappe.session.user == "Guest":
		frappe.local.flags.redirect_location = "/login"
		raise frappe.Redirect
	if not (is_grc_client() or is_grc_internal_user()):
		frappe.local.flags.redirect_location = "/"
		raise frappe.Redirect

# ── Role helpers ────────────────────────────────────────────────────────────

def is_grc_internal_user(user=None):
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return (
		frappe.has_role("GRC Manager", user)
		or frappe.has_role("GRC Analyst", user)
		or frappe.has_role("System Manager", user)
	)


def is_grc_client(user=None):
	user = user or frappe.session.user
	return frappe.has_role("GRC Client", user) or frappe.has_role("customer grc", user)


# ── Company resolution ───────────────────────────────────────────────────────

def get_client_company(user=None):
	"""Return the customer_grc record name linked to a portal user."""
	user = user or frappe.session.user
	company = frappe.db.get_value("customer_grc", {"portal_user": user}, "name")
	if company:
		return company
	user_email = frappe.db.get_value("User", user, "email")
	if user_email:
		company = frappe.db.get_value("customer_grc", {"email_company": user_email}, "name")
	return company


# ── Compliance score ─────────────────────────────────────────────────────────

_QS_FIELDS = [
	"formation", "registre", "conservation", "legislative",
	"principe_securite", "analyse_impact", "donnee_autorise_artci",
	"clause", "donnee_hors_cedeao", "site_conforme", "correspondant",
	"finalite", "proportionnalite", "securite_locaux", "procedure_remonte",
	"privacy", "habilitation", "charte", "droit_personne", "violationn",
]

_SEVERITY_PENALTY = {"Critique": 12, "Haute": 6, "Moyenne": 3, "Faible": 1}


def calculate_compliance_score(company):
	"""Return a 0-100 compliance score for a company."""
	if not company:
		return 0

	qs = frappe.db.get_value("question_score", {"entreprise": company}, _QS_FIELDS, as_dict=True)
	if qs:
		values = [v for v in qs.values() if v and v != "Non/applicable"]
		if values:
			points = sum(1.0 if v == "Oui" else 0.5 if v == "Partiel" else 0.0 for v in values)
			base = (points / len(values)) * 100
		else:
			base = 50.0
	else:
		base = 50.0

	open_violations = frappe.db.get_list(
		"violation_grc",
		filters={"entreprise": company, "statut": ["not in", ["Terminer", "Terminé"]]},
		fields=["gravite"],
	)
	penalty = sum(_SEVERITY_PENALTY.get(v.get("gravite") or "Faible", 1) for v in open_violations)
	return round(max(0.0, min(100.0, base - penalty)), 1)


def update_compliance_score(company):
	if not company:
		return
	score = calculate_compliance_score(company)
	frappe.db.set_value("customer_grc", company, "compliance_score", score)


# ── Permission query conditions ──────────────────────────────────────────────

def _client_clause(table, field, user):
	if is_grc_internal_user(user):
		return ""
	if is_grc_client(user):
		company = get_client_company(user)
		if company:
			safe = company.replace("'", "''")
			return f"`tab{table}`.`{field}` = '{safe}'"
		return "1=0"
	return "1=0"


def get_customer_grc_permission_query(user=None):
	return _client_clause("customer_grc", "name", user or frappe.session.user)

def get_violation_grc_permission_query(user=None):
	return _client_clause("violation_grc", "entreprise", user or frappe.session.user)

def get_action_plan_grc_permission_query(user=None):
	return _client_clause("action_plan_grc", "entreprise", user or frappe.session.user)

def get_make_right_grc_permission_query(user=None):
	return _client_clause("make_right_grc", "entreprise", user or frappe.session.user)

def get_traitement_grc_permission_query(user=None):
	return _client_clause("traitement_grc", "entreprise", user or frappe.session.user)

def get_point_de_controle_permission_query(user=None):
	return _client_clause("Point_de_controle", "entreprise", user or frappe.session.user)

def get_grc_document_permission_query(user=None):
	return _client_clause("grc_document", "entreprise", user or frappe.session.user)


# ── has_permission hooks ─────────────────────────────────────────────────────

def has_customer_grc_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if is_grc_internal_user(user):
		return True
	if is_grc_client(user):
		return doc.name == get_client_company(user)
	return False


def has_entreprise_doc_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if is_grc_internal_user(user):
		return True
	if is_grc_client(user):
		return doc.get("entreprise") == get_client_company(user)
	return False


def has_grc_document_permission(doc, user=None, permission_type=None):
	user = user or frappe.session.user
	if is_grc_internal_user(user):
		return True
	if is_grc_client(user):
		company = get_client_company(user)
		if doc.get("entreprise") != company:
			return False
		if permission_type == "read":
			return doc.get("visibilite") in ["Client", "Public"]
		if permission_type in ["write", "delete"]:
			return doc.get("televerse_par") == user
		return True
	return False


# ── Notification helper ──────────────────────────────────────────────────────

def notify_grc_user(to_user, title, message, ref_doctype=None, ref_name=None):
	if not to_user or to_user == "Guest":
		return
	try:
		doc = frappe.get_doc({
			"doctype": "Notification Log",
			"for_user": to_user,
			"type": "Alert",
			"document_type": ref_doctype,
			"document_name": ref_name,
			"subject": title,
			"email_content": message,
			"read": 0,
		})
		doc.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "GRC notify_grc_user failed")


def _portal_user(company):
	return frappe.db.get_value("customer_grc", company, "portal_user") if company else None


def _grc_manager(company):
	return frappe.db.get_value("customer_grc", company, "grc_manager") if company else None


# ── Document event hooks ─────────────────────────────────────────────────────

def on_violation_created(doc, method):
	update_compliance_score(doc.entreprise)
	portal_user = _portal_user(doc.entreprise)
	if portal_user:
		notify_grc_user(
			portal_user,
			_("Nouvelle violation enregistrée"),
			_(f"Une violation a été créée: {(doc.description or '')[:100]}"),
			"violation_grc", doc.name,
		)


def on_violation_updated(doc, method):
	update_compliance_score(doc.entreprise)


def on_action_plan_created(doc, method):
	update_compliance_score(doc.entreprise)
	portal_user = _portal_user(doc.entreprise)
	if portal_user:
		label = doc.get("titre") or (doc.get("description") or "")[:60]
		notify_grc_user(
			portal_user,
			_("Nouveau plan d'action"),
			_(f"Un plan d'action vous a été assigné: {label}"),
			"action_plan_grc", doc.name,
		)


def on_action_plan_updated(doc, method):
	update_compliance_score(doc.entreprise)


def on_grc_document_uploaded(doc, method):
	if is_grc_client(frappe.session.user):
		manager = _grc_manager(doc.entreprise)
		if manager:
			co_name = frappe.db.get_value("customer_grc", doc.entreprise, "entreprise") or doc.entreprise
			notify_grc_user(
				manager,
				_("Document téléversé par un client"),
				_(f"{co_name} a téléversé un document: {doc.titre}"),
				"grc_document", doc.name,
			)
	else:
		portal_user = _portal_user(doc.entreprise)
		if portal_user and doc.get("visibilite") in ["Client", "Public"]:
			notify_grc_user(
				portal_user,
				_("Nouveau document partagé"),
				_(f"Un document a été partagé avec vous: {doc.titre}"),
				"grc_document", doc.name,
			)


def on_make_right_created(doc, method):
	manager = _grc_manager(doc.entreprise)
	if manager:
		co_name = frappe.db.get_value("customer_grc", doc.entreprise, "entreprise") or (doc.entreprise or "")
		notify_grc_user(
			manager,
			_("Nouvelle demande de droit"),
			_(f"Demande '{doc.make_type}' reçue de {doc.name_maker or 'un demandeur'} ({co_name})"),
			"make_right_grc", doc.name,
		)


# ── Scheduled task ───────────────────────────────────────────────────────────

def refresh_all_compliance_scores():
	companies = frappe.db.get_list("customer_grc", filters={"statut": ["!=", "Inactif"]}, pluck="name")
	for company in companies:
		try:
			update_compliance_score(company)
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"GRC score update failed: {company}")
	frappe.db.commit()
