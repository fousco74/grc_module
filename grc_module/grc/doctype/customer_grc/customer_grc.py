import frappe
from frappe.model.document import Document


class customer_grc(Document):

	def after_insert(self):
		"""Create a portal User for the legal representative if not yet existing."""
		if self.email_legal and not frappe.db.exists("User", {"email": self.email_legal}):
			user = frappe.get_doc({
				"doctype": "User",
				"first_name": self.first_name_legal or "",
				"last_name": self.last_name_legal or "",
				"email": self.email_legal,
				"mobile_no": self.phone,
				"user_type": "Website User",
				"roles": [{"role": "GRC Client"}, {"role": "customer grc"}],
			})
			user.insert(ignore_permissions=True)
			# Link back the portal user
			self.db_set("portal_user", user.name, update_modified=False)

	def on_update(self):
		from grc_module.utils import calculate_compliance_score
		score = calculate_compliance_score(self.name)
		if self.compliance_score != score:
			self.db_set("compliance_score", score, update_modified=False)
