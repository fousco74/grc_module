import frappe

def run():
    # Check existing GRC onboarding steps
    steps = frappe.db.sql("SELECT name, title, action, action_label, reference_document, is_complete FROM `tabOnboarding Step` WHERE parent = 'Onboarding GRC'", as_dict=True)
    print("=== GRC Onboarding Steps ===")
    for s in steps:
        print(f"  {s}")

    # Check Onboarding Step fields
    cols = frappe.db.sql("DESCRIBE `tabOnboarding Step`", as_dict=True)
    print("\n=== Onboarding Step columns ===")
    for c in cols:
        print(f"  {c['Field']}")

    # Check Module Onboarding fields
    cols2 = frappe.db.sql("DESCRIBE `tabModule Onboarding`", as_dict=True)
    print("\n=== Module Onboarding columns ===")
    for c in cols2:
        print(f"  {c['Field']}")
