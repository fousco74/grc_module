import frappe


def get_context(context):
    """
    Contexte partagé pour toutes les pages ConformIT.
    - Redirige les visiteurs non connectés vers /login
    - Injecte le layout de base ConformIT
    - Expose les infos session utiles aux templates Jinja
    """

    # ── 1. Authentification obligatoire ──────────────────────────
    # frappe.local.flags.redirect_location + raise frappe.Redirect
    # est la méthode correcte pour une redirection propre (HTTP 302)
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect

    # ── 2. Template de base ConformIT ────────────────────────────
    context.base_template = "grc_module/templates/layout.html"
    # ── 3. Infos session exposées au template Jinja ──────────────
    context.user_fullname  = frappe.session.user_fullname
    context.user_email     = frappe.session.user
    context.csrf_token     = frappe.session.csrf_token

    # ── 4. Métadonnées page (surchargeables par chaque page) ─────
    context.no_cache       = 1          # désactive le cache Frappe sur ces pages
    context.show_sidebar   = False      # masque la sidebar Frappe native