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
		{"label": _("Traitement"), "fieldname": "traitement", "fieldtype": "Data", "width": 240},
		{"label": _("Service"), "fieldname": "service", "fieldtype": "Link", "options": "service_grc", "width": 180},
		{"label": _("Nom du service"), "fieldname": "service_name", "fieldtype": "Data", "width": 200},
	]


def get_data(filters):
	conditions = ["t.1=1"]
	values = {}

	if filters.get("entreprise"):
		conditions.append("t.entreprise = %(entreprise)s")
		values["entreprise"] = filters["entreprise"]

	if filters.get("service"):
		conditions.append("t.service = %(service)s")
		values["service"] = filters["service"]

	where = " AND ".join(conditions).replace("t.1=1", "1=1")

	rows = frappe.db.sql(f"""
		SELECT
			t.entreprise,
			t.traitement,
			t.service,
			s.name_service AS service_name
		FROM `tabtraitement_grc` t
		LEFT JOIN `tabservice_grc` s ON s.name = t.service
		WHERE {where}
		ORDER BY t.entreprise, s.name_service
	""", values, as_dict=True)

	return rows


def get_chart(data):
	counts = Counter(r.get("service_name") or r.get("service") or "Sans service" for r in data)
	# Top 10 services by treatment count
	top = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
	labels = [k for k, v in top]
	values = [v for k, v in top]
	return {
		"type": "bar",
		"title": _("Traitements par service"),
		"data": {"labels": labels, "datasets": [{"values": values}]},
		"colors": ["#6366f1"],
		"axisOptions": {"xIsSeries": True},
	}


def get_summary(data):
	total = len(data)
	companies = len(set(r.get("entreprise") for r in data if r.get("entreprise")))
	services = len(set(r.get("service") for r in data if r.get("service")))
	return [
		{"label": _("Total traitements"), "value": total, "indicator": "blue"},
		{"label": _("Entreprises"), "value": companies, "indicator": "green"},
		{"label": _("Services distincts"), "value": services, "indicator": "purple"},
	]
