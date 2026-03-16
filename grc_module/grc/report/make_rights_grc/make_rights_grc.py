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
		{"label": _("Demandeur"), "fieldname": "name_maker", "fieldtype": "Data", "width": 160},
		{"label": _("Email"), "fieldname": "email_maker", "fieldtype": "Data", "width": 180},
		{"label": _("Type de demande"), "fieldname": "make_type", "fieldtype": "Data", "width": 150},
		{"label": _("Statut"), "fieldname": "statut", "fieldtype": "Data", "width": 110},
		{"label": _("Date de fin"), "fieldname": "updated_at", "fieldtype": "Date", "width": 120},
		{"label": _("Description"), "fieldname": "description", "fieldtype": "Small Text", "width": 280},
	]


def get_data(filters):
	conditions = ["1=1"]
	values = {}

	if filters.get("entreprise"):
		conditions.append("entreprise = %(entreprise)s")
		values["entreprise"] = filters["entreprise"]

	if filters.get("make_type"):
		conditions.append("make_type = %(make_type)s")
		values["make_type"] = filters["make_type"]

	if filters.get("statut"):
		conditions.append("statut = %(statut)s")
		values["statut"] = filters["statut"]

	if filters.get("from_date"):
		conditions.append("creation >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("creation <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where = " AND ".join(conditions)

	rows = frappe.db.sql(f"""
		SELECT
			entreprise,
			name_maker,
			email_maker,
			make_type,
			statut,
			updated_at,
			description
		FROM `tabmake_right_grc`
		WHERE {where}
		ORDER BY
			FIELD(statut, 'Reçue', 'Vérifiée', 'En cours', 'Terminée', 'rejetée'),
			creation DESC
	""", values, as_dict=True)

	return rows


def get_chart(data):
	counts = Counter(r.get("make_type") or "Non défini" for r in data)
	labels = list(counts.keys())
	values = [counts[k] for k in labels]
	colors = ["#6366f1", "#3b82f6", "#10b981", "#f59e0b", "#ef4444"]
	return {
		"type": "donut",
		"title": _("Demandes par type"),
		"data": {"labels": labels, "datasets": [{"values": values}]},
		"colors": colors,
	}


def get_summary(data):
	total = len(data)
	pending = sum(1 for r in data if r.get("statut") in ("Reçue", "Vérifiée", "En cours"))
	done = sum(1 for r in data if r.get("statut") == "Terminée")
	rejected = sum(1 for r in data if r.get("statut") == "rejetée")
	return [
		{"label": _("Total"), "value": total, "indicator": "Blue"},
		{"label": _("En attente"), "value": pending, "indicator": "Orange"},
		{"label": _("Traitées"), "value": done, "indicator": "Green"},
		{"label": _("Rejetées"), "value": rejected, "indicator": "Red"},
	]
