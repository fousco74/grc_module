frappe.ready(function() {

    // Vérifier qu'on est sur une page d'erreur Not Permitted
    const titleEl = document.querySelector('.page-card-head');
    if (!titleEl || !titleEl.innerText.includes('Not Permitted')) {
        return;
    }

    // Protection contre double exécution
    if (document.getElementById('grc-smart-btn')) return;

    const userEmail = frappe.session.user || 'Guest';
    const currentPath = (window.location.pathname || '').toLowerCase();

    let redirectUrl = '/desk';
    let buttonText = 'Retourner au bureau';
    let icon = 'fa-arrow-left';

    // === Logique améliorée sans dépendre de frappe.user_roles ===
    
    if (userEmail === 'Guest') {
        redirectUrl = '/login';
        buttonText = 'Se connecter';
        icon = 'fa-sign-in';
    } 
    // Si l'utilisateur essaie d'accéder à une page /grc/* → on suppose qu'il veut aller au dashboard GRC
    else if (currentPath.startsWith('/grc/')) {
         redirectUrl = '/desk';
        buttonText = 'Retourner au bureau';
        icon = 'fa-desktop';
    } 
    // Sinon, on redirige vers le bureau (comportement par défaut pour les utilisateurs connectés)
    else {
        redirectUrl = '/grc/dashboard';
        buttonText = 'Accéder au dashboard GRC';
        icon = 'fa-tachometer';
    }

    const newButtonHTML = `
        <div id="grc-smart-btn" style="text-align:center; margin: 35px 0 25px 0;">
            <a href="${redirectUrl}" 
               class="btn btn-primary btn-lg btn-block"
               style="padding: 14px 30px; font-size: 18px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <i class="fa ${icon}"></i> ${buttonText}
            </a>
        </div>`;

    // Remplacer le bouton Login existant
    const oldLoginBtn = document.querySelector('a[href*="/login"], a.btn-primary');

    if (oldLoginBtn) {
        const parentDiv = oldLoginBtn.parentElement;
        if (parentDiv) {
            parentDiv.innerHTML = newButtonHTML;
            console.log(`Bouton remplacé avec succès → ${buttonText} (${redirectUrl})`);
        }
    } 
    // Fallback : ajouter à la fin de .details si on ne trouve pas le bouton
    else {
        const detailsDiv = document.querySelector('.details');
        if (detailsDiv) {
            detailsDiv.insertAdjacentHTML('beforeend', newButtonHTML);
            console.log(`Bouton ajouté en fallback → ${buttonText}`);
        }
    }
});