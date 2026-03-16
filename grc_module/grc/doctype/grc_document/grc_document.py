import frappe
from frappe.model.document import Document


class grc_document(Document):
	def before_insert(self):
		if not self.televerse_par:
			self.televerse_par = frappe.session.user
		if not self.creation_date:
			self.creation_date = frappe.utils.today()
