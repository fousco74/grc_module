# Copyright (c) 2025, KONE Fousseni and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

class customer_grc(Document):
    
    def after_insert(self):
        if not frappe.db.exists("User", {"email": self.email_legal}):
            frappe.get_doc({
                "doctype": "User",
                "first_name": self.first_name_legal,
                "last_name": self.last_name_legal,
                "email": self.email_legal,
                "mobile_no": self.phone,
                "roles": [{"role": "customer grc"}]
            }).insert(ignore_permissions=True)
     
