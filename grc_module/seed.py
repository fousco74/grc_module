import frappe
from frappe.utils import today, add_days

SITH_ID = "t6q3tjps83"
TECH_ID = "Client-2026-00182-00106"
MANAGER = "cyao@amoaman.com"
KLOSSENI = "klosseni@gmail.com"
AKONE = "akone@techsolutions182.ci"

def run():
    link_users()
    make_departments_sith()
    make_services_sith()
    make_traitements_sith()
    make_control_points_sith()
    make_violations_sith()
    make_action_plans_sith()
    make_make_rights_sith()
    make_documents_sith()
    make_question_score()
    make_niveau_avancement_sith()
    update_sith_score()
    frappe.db.commit()
    print("\n✓ Toutes les données ont été créées avec succès.")

def link_users():
    for name, portal, manager in [(SITH_ID, KLOSSENI, MANAGER), (TECH_ID, AKONE, MANAGER)]:
        frappe.db.set_value("customer_grc", name, {"portal_user": portal, "grc_manager": manager})
    print("✓ portal_user et grc_manager mis à jour")

def make_departments_sith():
    depts = ["Direction Générale", "Ressources Humaines", "Informatique & Systèmes", "Finance & Comptabilité"]
    count = 0
    for nom in depts:
        if frappe.db.exists("department_grc", {"entreprise": SITH_ID, "nom_du_departement": nom}):
            continue
        frappe.get_doc({"doctype": "department_grc", "entreprise": SITH_ID, "nom_du_departement": nom}).insert(ignore_permissions=True)
        count += 1
    print(f"✓ {count} départements SITH créés")

def make_services_sith():
    services = [("Service DSI", "Informatique & Systèmes"), ("Service RH", "Ressources Humaines"), ("Service Comptabilité", "Finance & Comptabilité"), ("Direction Générale", "Direction Générale")]
    count = 0
    for name_service, dept_nom in services:
        if frappe.db.exists("service_grc", {"entreprise": SITH_ID, "name_service": name_service}):
            continue
        dept = frappe.db.get_value("department_grc", {"entreprise": SITH_ID, "nom_du_departement": dept_nom}, "name")
        frappe.get_doc({"doctype": "service_grc", "name_service": name_service, "entreprise": SITH_ID, "departement": dept}).insert(ignore_permissions=True)
        count += 1
    print(f"✓ {count} services SITH créés")

def make_traitements_sith():
    svc_rh = frappe.db.get_value("service_grc", {"entreprise": SITH_ID, "name_service": "Service RH"}, "name")
    svc_dsi = frappe.db.get_value("service_grc", {"entreprise": SITH_ID, "name_service": "Service DSI"}, "name")
    svc_cpt = frappe.db.get_value("service_grc", {"entreprise": SITH_ID, "name_service": "Service Comptabilité"}, "name")
    traitements = [("Gestion du personnel", svc_rh), ("Gestion des accès systèmes", svc_dsi), ("Traitement des salaires", svc_cpt)]
    count = 0
    for traitement, svc in traitements:
        if frappe.db.exists("traitement_grc", {"entreprise": SITH_ID, "traitement": traitement}):
            continue
        frappe.get_doc({"doctype": "traitement_grc", "entreprise": SITH_ID, "traitement": traitement, "service": svc}).insert(ignore_permissions=True)
        count += 1
    print(f"✓ {count} traitements SITH créés")

def make_control_points_sith():
    svc_rh = frappe.db.get_value("service_grc", {"entreprise": SITH_ID, "name_service": "Service RH"}, "name")
    svc_dsi = frappe.db.get_value("service_grc", {"entreprise": SITH_ID, "name_service": "Service DSI"}, "name")
    points = [("Politique de protection des données RH", svc_rh, "Non conforme", "Critique"), ("Habilitations d'accès aux systèmes", svc_dsi, "Partiel", "Haute"), ("Chiffrement des données sensibles", svc_dsi, "Non évalué", "Critique"), ("Formation RGPD du personnel RH", svc_rh, "Partiel", "Normale")]
    count = 0
    for titre, svc, statut, priorite in points:
        if frappe.db.exists("Point_de_controle", {"entreprise": SITH_ID, "titre": titre}):
            continue
        frappe.get_doc({"doctype": "Point_de_controle", "entreprise": SITH_ID, "titre": titre, "description": f"Contrôle : {titre}", "service": svc, "statut": statut, "priorite": priorite}).insert(ignore_permissions=True)
        count += 1
    print(f"✓ {count} points de contrôle SITH créés")

def make_violations_sith():
    violations = [("Absence de politique de confidentialité", "Haute", "Légale", "A faire"), ("Données RH non chiffrées sur les serveurs", "Critique", "Technique", "En Cours"), ("Manque de registre des traitements", "Moyenne", "Organisationnelle", "A faire"), ("Formulaires web sans mentions légales RGPD", "Haute", "Légale", "En Cours")]
    count = 0
    for titre, gravite, type_vio, statut in violations:
        if frappe.db.exists("violation_grc", {"entreprise": SITH_ID, "titre": titre}):
            continue
        frappe.get_doc({"doctype": "violation_grc", "entreprise": SITH_ID, "titre": titre, "description": f"Violation détectée : {titre}", "gravite": gravite, "type_violation": type_vio, "statut": statut, "date_de_creation": today(), "responsable": MANAGER}).insert(ignore_permissions=True)
        count += 1
    print(f"✓ {count} violations SITH créées")

def make_action_plans_sith():
    plans = [("Rédaction de la politique de confidentialité", "Légal & Conformité", "En cours", 30), ("Chiffrement des données RH en transit", "Sécurité technique", "A faire", 60), ("Mise en place du registre des traitements", "Conformité RGPD", "En cours", 45), ("Mise à jour des formulaires web RGPD", "Légal & Web", "A faire", 20)]
    count = 0
    for titre, principe, statut, delai in plans:
        if frappe.db.exists("action_plan_grc", {"entreprise": SITH_ID, "titre": titre}):
            continue
        frappe.get_doc({"doctype": "action_plan_grc", "entreprise": SITH_ID, "titre": titre, "description": f"Plan d'action : {titre}", "principe_directeur": principe, "statut": statut, "responsable": MANAGER, "date_debut": today(), "delais_dexecution": add_days(today(), delai), "avancement": 0 if statut == "A faire" else 40}).insert(ignore_permissions=True)
        count += 1
    print(f"✓ {count} plans d'action SITH créés")

def make_make_rights_sith():
    demandes = [("Jean Koné", "+225 07 11 22 33", "jean.kone@sith.com", "Accès aux données", "Reçue"), ("Awa Diabaté", "+225 05 44 55 66", "awa.d@sith.com", "Suppression", "En cours"), ("Moussa Traoré", "+225 01 77 88 99", "moussa.t@gmail.com", "Rectification", "Reçue")]
    count = 0
    for nom, phone, email, make_type, statut in demandes:
        if frappe.db.exists("make_right_grc", {"entreprise": SITH_ID, "name_maker": nom}):
            continue
        frappe.get_doc({"doctype": "make_right_grc", "entreprise": SITH_ID, "name_maker": nom, "phone_maker": phone, "email_maker": email, "make_type": make_type, "statut": statut, "description": f"Demande de {make_type.lower()} soumise par {nom}."}).insert(ignore_permissions=True)
        count += 1
    print(f"✓ {count} demandes de droits SITH créées")

def make_documents_sith():
    docs = [("Rapport d'audit initial SITH", "Rapport d'audit", "Interne"), ("Politique de protection des données", "Politique de conformité", "Client"), ("Formulaire de consentement type", "Formulaire RGPD", "Public")]
    count = 0
    for titre, type_doc, visibilite in docs:
        if frappe.db.exists("grc_document", {"entreprise": SITH_ID, "titre": titre}):
            continue
        frappe.get_doc({"doctype": "grc_document", "entreprise": SITH_ID, "titre": titre, "type_document": type_doc, "visibilite": visibilite, "televerse_par": MANAGER, "creation_date": today(), "description": f"Document : {titre}"}).insert(ignore_permissions=True)
        count += 1
    print(f"✓ {count} documents SITH créés")

def make_question_score():
    for eid, is_sith in [(SITH_ID, True), (TECH_ID, False)]:
        if frappe.db.exists("question_score_grc", {"entreprise": eid}):
            continue
        oui_non = lambda s: "Non" if is_sith else s
        frappe.get_doc({"doctype": "question_score_grc", "entreprise": eid, "formation": oui_non("Partiel"), "registre": oui_non("Oui"), "conservation": oui_non("Partiel"), "legislative": "Non/applicable Partiel", "principe_securite": "Partiel", "analyse_impact": oui_non("Partiel"), "donnee_autorise_artci": "Non/applicable", "clause": oui_non("Oui"), "donnee_hors_cedeao": "Non/applicable", "site_conforme": oui_non("Partiel"), "correspondant": oui_non("Oui"), "finalite": "Partiel", "proportionnalite": "Partiel", "securite_locaux": oui_non("Partiel"), "procedure_remonte": oui_non("Partiel"), "privacy": "Non", "habilitation": "Partiel", "charte": oui_non("Oui"), "droit_personne": oui_non("Partiel"), "violationn": oui_non("Partiel")}).insert(ignore_permissions=True)
    print("✓ Questionnaires de conformité créés")

def make_niveau_avancement_sith():
    services_niveaux = [("Service RH", "Initi\u00e9"), ("Service DSI", "En cours d\u2019avancement"), ("Service Comptabilit\u00e9", "Initi\u00e9"), ("Direction G\u00e9n\u00e9rale", "En cours d\u2019avancement")]
    count = 0
    for name_service, niveau in services_niveaux:
        svc = frappe.db.get_value("service_grc", {"entreprise": SITH_ID, "name_service": name_service}, "name")
        if not svc or frappe.db.exists("Niveau_avancement_service", {"entreprise": SITH_ID, "service": svc}):
            continue
        frappe.get_doc({"doctype": "Niveau_avancement_service", "entreprise": SITH_ID, "service": svc, "niveau": niveau}).insert(ignore_permissions=True)
        count += 1
    print(f"✓ {count} niveaux d'avancement SITH créés")

def update_sith_score():
    frappe.db.set_value("customer_grc", SITH_ID, {"compliance_score": 8.0, "statut": "Actif", "etape_avancement": "Audit", "onboarding_date": add_days(today(), -30)})
    print("✓ Score et statut SITH mis à jour")
