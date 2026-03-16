app_name = "grc_module"
app_title = "GRC"
app_publisher = "KONE Fousseni"
app_description = "Gouvernance risque et conformité"
app_email = "hello@amoaman.com"
app_license = "mit"

fixtures = [
	{"dt": "Custom Field", "filters": [["module", "=", "GRC"]]},
	{"dt": "Property Setter", "filters": [["module", "=", "GRC"]]},
	{"dt": "Web Page", "filters": [["module", "=", "GRC"]]},
	{"dt": "Web Form", "filters": [["module", "=", "GRC"]]},
	{"dt": "DocType", "filters": [["module", "=", "GRC"]]},
	{"dt": "Module Def", "filters": [["module_name", "=", "GRC"]]},
	{"dt": "Workspace", "filters": [["module", "=", "GRC"]]},
	{"dt": "Report", "filters": [["module", "=", "GRC"]]},
	{"dt": "Print Format", "filters": [["module", "=", "GRC"]]},
	{"dt": "Client Script", "filters": [["module", "=", "GRC"]]},
	{"dt": "Server Script", "filters": [["module", "=", "GRC"]]},
	{"dt": "Role", "filters": [["name", "in", ["GRC Manager", "GRC Analyst", "GRC Client"]]]},
]

# Role home pages
role_home_page = {
	"customer grc": "/grc/dashboard",
	"GRC Client": "/grc/dashboard",
	"GRC Manager": "/app/grc",
	"GRC Analyst": "/app/grc",
}

# Row-level security: GRC Clients only see their company's data
permission_query_conditions = {
	"customer_grc": "grc_module.utils.get_customer_grc_permission_query",
	"violation_grc": "grc_module.utils.get_violation_grc_permission_query",
	"action_plan_grc": "grc_module.utils.get_action_plan_grc_permission_query",
	"make_right_grc": "grc_module.utils.get_make_right_grc_permission_query",
	"traitement_grc": "grc_module.utils.get_traitement_grc_permission_query",
	"Point_de_controle": "grc_module.utils.get_point_de_controle_permission_query",
	"grc_document": "grc_module.utils.get_grc_document_permission_query",
}

has_permission = {
	"customer_grc": "grc_module.utils.has_customer_grc_permission",
	"violation_grc": "grc_module.utils.has_entreprise_doc_permission",
	"action_plan_grc": "grc_module.utils.has_entreprise_doc_permission",
	"make_right_grc": "grc_module.utils.has_entreprise_doc_permission",
	"traitement_grc": "grc_module.utils.has_entreprise_doc_permission",
	"grc_document": "grc_module.utils.has_grc_document_permission",
}

# Document event hooks
doc_events = {
	"violation_grc": {
		"after_insert": "grc_module.utils.on_violation_created",
		"on_update": "grc_module.utils.on_violation_updated",
	},
	"action_plan_grc": {
		"after_insert": "grc_module.utils.on_action_plan_created",
		"on_update": "grc_module.utils.on_action_plan_updated",
	},
	"grc_document": {
		"after_insert": "grc_module.utils.on_grc_document_uploaded",
	},
	"make_right_grc": {
		"after_insert": "grc_module.utils.on_make_right_created",
	},
}

# Scheduled tasks
scheduler_events = {
	"daily": [
		"grc_module.utils.refresh_all_compliance_scores",
	],
}
