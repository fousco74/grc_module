import frappe
from frappe import _
from collections import Counter


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	summary = get_summary(data)
	return columns, data, None, chart, summary


def get_columns():
	return [
		{"label": _("Entreprise"), "fieldname": "entreprise", "fieldtype": "Link", "options": "customer_grc", "width": 180},
		{"label": _("Titre"), "fieldname": "titre", "fieldtype": "Data", "width": 200},
		{"label": _("Gravité"), "fieldname": "gravite", "fieldtype": "Data", "width": 100},
		{"label": _("Type"), "fieldname": "type_violation", "fieldtype": "Data", "width": 120},
		{"label": _("Statut"), "fieldname": "statut", "fieldtype": "Data", "width": 100},
		{"label": _("Date de création"), "fieldname": "date_creation", "fieldtype": "Date", "width": 120},
		{"label": _("Responsable"), "fieldname": "responsable", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": _("Description"), "fieldname": "description", "fieldtype": "Small Text", "width": 280},
	]


def get_data(filters):
	conditions = ["1=1"]
	values = {}

	if filters.get("entreprise"):
		conditions.append("entreprise = %(entreprise)s")
		values["entreprise"] = filters["entreprise"]

	if filters.get("gravite"):
		conditions.append("gravite = %(gravite)s")
		values["gravite"] = filters["gravite"]

	if filters.get("statut"):
		conditions.append("statut = %(statut)s")
		values["statut"] = filters["statut"]

	if filters.get("type_violation"):
		conditions.append("type_violation = %(type_violation)s")
		values["type_violation"] = filters["type_violation"]

	if filters.get("from_date"):
		conditions.append("date_de_creation >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("date_de_creation <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where = " AND ".join(conditions)

	rows = frappe.db.sql(f"""
		SELECT
			entreprise,
			titre,
			description,
			gravite,
			type_violation,
			statut,
			`date_de_création` AS date_creation,
			responsable
		FROM `tabviolation_grc`
		WHERE {where}
		ORDER BY
			FIELD(gravite, 'Critique', 'Haute', 'Moyenne', 'Faible'),
			`date_de_création` DESC
	""", values, as_dict=True)

	return rows


def get_chart(data):
	counts = Counter(r.get("gravite") or "Non définie" for r in data)
	order = ["Critique", "Haute", "Moyenne", "Faible", "Non définie"]
	labels = [k for k in order if k in counts]
	values = [counts[k] for k in labels]
	return {
		"type": "donut",
		"title": _("Violations par gravité"),
		"data": {"labels": labels, "datasets": [{"values": values}]},
		"colors": ["#ef4444", "#f97316", "#f59e0b", "#eab308", "#94a3b8"],
	}


def get_summary(data):
	open_count = sum(1 for r in data if r.get("statut") != "Terminer")
	critical = sum(1 for r in data if r.get("gravite") == "Critique")
	return [
		{"label": _("Total"), "value": len(data), "indicator": "Blue"},
		{"label": _("Ouvertes"), "value": open_count, "indicator": "Orange"},
		{"label": _("Critiques"), "value": critical, "indicator": "Red"},
	]
