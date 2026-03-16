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

	if context.is_client:
		doc_filters = {
			"entreprise": context.company,
			"visibilite": ["in", ["Client", "Public"]],
		}
	else:
		doc_filters = {"entreprise": context.company} if context.company else {}

	context.documents = frappe.db.get_list(
		"grc_document", filters=doc_filters,
		fields=["name", "titre", "type_document", "fichier", "televerse_par", "visibilite", "creation_date", "description", "entreprise"],
		order_by="creation_date desc",
	)

	# Document type options for upload form
	context.doc_types = ["Rapport d'audit", "Politique de conformité", "Contrat", "Formulaire RGPD", "Guide", "Autre"]

	# Company list for form
	if context.company:
		co = frappe.db.get_value("customer_grc", context.company, ["name", "entreprise"], as_dict=True)
		context.companies = [co] if co else []
	else:
		context.companies = frappe.db.get_list("customer_grc", fields=["name", "entreprise"], limit=100)

	context.notif_count = frappe.db.count("Notification Log", {"for_user": frappe.session.user, "read": 0})
