import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	summary = get_summary(data)
	return columns, data, None, chart, summary


def get_columns():
	return [
		{"label": _("Entreprise (ID)"), "fieldname": "name", "fieldtype": "Link", "options": "customer_grc", "width": 160},
		{"label": _("Nom de l'entreprise"), "fieldname": "entreprise", "fieldtype": "Data", "width": 200},
		{"label": _("Score"), "fieldname": "compliance_score", "fieldtype": "Float", "precision": 1, "width": 100},
		{"label": _("Niveau"), "fieldname": "niveau", "fieldtype": "Data", "width": 120},
		{"label": _("Statut"), "fieldname": "statut", "fieldtype": "Data", "width": 130},
		{"label": _("Responsable GRC"), "fieldname": "grc_manager", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": _("Violations ouvertes"), "fieldname": "open_violations", "fieldtype": "Int", "width": 130},
		{"label": _("Violations critiques"), "fieldname": "critical_violations", "fieldtype": "Int", "width": 130},
		{"label": _("Plans en cours"), "fieldname": "open_plans", "fieldtype": "Int", "width": 120},
		{"label": _("Date intégration"), "fieldname": "onboarding_date", "fieldtype": "Date", "width": 130},
	]


def get_data(filters):
	conditions = ["1=1"]
	values = {}

	if filters.get("entreprise"):
		conditions.append("name = %(entreprise)s")
		values["entreprise"] = filters["entreprise"]

	if filters.get("statut"):
		conditions.append("statut = %(statut)s")
		values["statut"] = filters["statut"]

	if filters.get("score_min") is not None and filters["score_min"] != "":
		conditions.append("compliance_score >= %(score_min)s")
		values["score_min"] = filters["score_min"]

	if filters.get("score_max") is not None and filters["score_max"] != "":
		conditions.append("compliance_score <= %(score_max)s")
		values["score_max"] = filters["score_max"]

	where = " AND ".join(conditions)

	companies = frappe.db.sql(f"""
		SELECT name, entreprise, compliance_score, statut, grc_manager, onboarding_date
		FROM `tabcustomer_grc`
		WHERE {where}
		ORDER BY compliance_score ASC
	""", values, as_dict=True)

	# Enrich with violation and action plan counts
	for co in companies:
		co_name = co["name"]
		co["open_violations"] = frappe.db.count(
			"violation_grc", {"entreprise": co_name, "statut": ["!=", "Terminer"]}
		)
		co["critical_violations"] = frappe.db.count(
			"violation_grc", {"entreprise": co_name, "gravite": "Critique", "statut": ["!=", "Terminer"]}
		)
		co["open_plans"] = frappe.db.count(
			"action_plan_grc", {"entreprise": co_name, "statut": ["!=", "Terminer"]}
		)
		score = co.get("compliance_score") or 0
		if score >= 80:
			co["niveau"] = "✅ Bon"
		elif score >= 50:
			co["niveau"] = "⚠️ Partiel"
		else:
			co["niveau"] = "🔴 Critique"

	return companies


def get_chart(data):
	data_sorted = sorted(data, key=lambda x: x.get("compliance_score") or 0, reverse=True)
	labels = [r.get("entreprise") or r.get("name") for r in data_sorted]
	values = [round(r.get("compliance_score") or 0, 1) for r in data_sorted]
	colors = [
		"#10b981" if v >= 80 else "#f59e0b" if v >= 50 else "#ef4444"
		for v in values
	]
	return {
		"type": "bar",
		"title": _("Score de conformité par entreprise"),
		"data": {"labels": labels, "datasets": [{"values": values}]},
		"colors": colors,
		"axisOptions": {"xIsSeries": True},
	}


def get_summary(data):
	scores = [r.get("compliance_score") or 0 for r in data]
	avg = round(sum(scores) / len(scores), 1) if scores else 0
	good = sum(1 for s in scores if s >= 80)
	at_risk = sum(1 for s in scores if s < 50)
	return [
		{"label": _("Entreprises"), "value": len(data), "indicator": "Blue"},
		{"label": _("Score moyen"), "value": avg, "indicator": "Green" if avg >= 70 else "Orange"},
		{"label": _("Conformes (≥80)"), "value": good, "indicator": "Green"},
		{"label": _("À risque (<50)"), "value": at_risk, "indicator": "Red"},
	]
