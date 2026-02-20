import frappe

def get_context(context):
    # Si tu veux changer le base template utilisé :
    context.base_template = "grc_module/templates/layout.html"
    
    return context
