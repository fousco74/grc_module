import frappe
from frappe import _
from collections import Counter
from datetime import date


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
		{"label": _("Statut"), "fieldname": "statut", "fieldtype": "Data", "width": 110},
		{"label": _("Avancement"), "fieldname": "avancement", "fieldtype": "Percent", "width": 110},
		{"label": _("Responsable"), "fieldname": "responsable", "fieldtype": "Data", "width": 150},
		{"label": _("Date début"), "fieldname": "date_debut", "fieldtype": "Date", "width": 110},
		{"label": _("Échéance"), "fieldname": "echeance", "fieldtype": "Date", "width": 110},
		{"label": _("Violation liée"), "fieldname": "violation", "fieldtype": "Link", "options": "violation_grc", "width": 160},
		{"label": _("Description"), "fieldname": "description", "fieldtype": "Small Text", "width": 260},
	]


def get_data(filters):
	conditions = ["1=1"]
	values = {}

	if filters.get("entreprise"):
		conditions.append("entreprise = %(entreprise)s")
		values["entreprise"] = filters["entreprise"]

	if filters.get("statut"):
		conditions.append("statut = %(statut)s")
		values["statut"] = filters["statut"]

	if filters.get("responsable"):
		conditions.append("responsable LIKE %(responsable)s")
		values["responsable"] = f"%{filters['responsable']}%"

	if filters.get("from_date"):
		conditions.append("`délais_dexécution` >= %(from_date)s")
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("`délais_dexécution` <= %(to_date)s")
		values["to_date"] = filters["to_date"]

	where = " AND ".join(conditions)

	rows = frappe.db.sql(f"""
		SELECT
			entreprise,
			titre,
			statut,
			avancement,
			responsable,
			date_debut,
			`délais_dexécution` AS echeance,
			violation,
			description
		FROM `tabaction_plan_grc`
		WHERE {where}
		ORDER BY
			FIELD(statut, 'En cours', 'A faire', 'Terminer'),
			`délais_dexécution` ASC
	""", values, as_dict=True)

	today = date.today()
	for r in rows:
		if r.get("echeance") and r["echeance"] < today and r.get("statut") != "Terminer":
			r["_overdue"] = True

	return rows


def get_chart(data):
	counts = Counter(r.get("statut") or "Non défini" for r in data)
	order = ["A faire", "En cours", "Terminer"]
	labels = [k for k in order if k in counts]
	values = [counts[k] for k in labels]
	colors = ["#94a3b8", "#3b82f6", "#10b981"]
	return {
		"type": "bar",
		"title": _("Plans d'action par statut"),
		"data": {"labels": labels, "datasets": [{"values": values}]},
		"colors": colors,
		"axisOptions": {"xIsSeries": True},
	}


def get_summary(data):
	total = len(data)
	open_count = sum(1 for r in data if r.get("statut") != "Terminer")
	done = sum(1 for r in data if r.get("statut") == "Terminer")
	overdue = sum(1 for r in data if r.get("_overdue"))
	return [
		{"label": _("Total"), "value": total, "indicator": "Blue"},
		{"label": _("En cours / À faire"), "value": open_count, "indicator": "Orange"},
		{"label": _("Terminés"), "value": done, "indicator": "Green"},
		{"label": _("En retard"), "value": overdue, "indicator": "Red"},
	]
