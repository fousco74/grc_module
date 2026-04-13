# GRC Module

Module de **Gouvernance, Risque et Conformité** pour ERPNext.  
Permet aux entreprises clientes de gérer leurs violations, plans d'action, demandes de droits et documents de conformité via un portail web dédié.

---

## Fonctionnalités

| Fonctionnalité | Description |
|----------------|-------------|
| **Violations** | Déclaration et suivi des incidents de conformité |
| **Plans d'action** | Création et suivi des plans correctifs |
| **Make Right** | Demandes d'exercice de droits (RGPD, etc.) |
| **Documents GRC** | Stockage et partage de documents réglementaires |
| **Registre de traitement** | Registre des activités de traitement des données |
| **Points de contrôle** | Grille d'audit avec scoring automatique |
| **Tableau de bord** | Score de conformité global par entreprise |
| **Portail client** | Interface web dédiée aux clients (rôle `GRC Client`) |

---

## Prérequis

- Frappe Framework ≥ 15
- ERPNext installé

---

## Installation

```bash
# 1. Récupérer l'app
bench get-app grc_module https://github.com/AMOAMAN/grc_module

# 2. Installer sur le site
bench --site <nom_du_site> install-app grc_module

# 3. Migrer
bench --site <nom_du_site> migrate

# 4. Construire les assets
bench build --app grc_module

# 5. Redémarrer
bench restart
```

---

## Configuration

### 1. Rôles

Deux rôles sont créés automatiquement à l'installation :

| Rôle | Accès |
|------|-------|
| `GRC Manager` | Accès complet (back-office) |
| `GRC Client` | Portail client — voit uniquement ses propres données |

Assigner le rôle `GRC Client` aux utilisateurs des entreprises clientes.

### 2. Portail web

Le portail est accessible à `/grc/dashboard` pour les utilisateurs avec le rôle `GRC Client`.

Navigation disponible :
- `/grc/dashboard` — Tableau de bord conformité
- `/grc/violations` — Violations
- `/grc/action-plan` — Plans d'action
- `/grc/make-right` — Demandes de droits
- `/grc/documents` — Documents
- `/grc/registre-processing` — Registre de traitement
- `/grc/audit` — Audit

### 3. Isolation des données

La sécurité au niveau ligne est configurée automatiquement : chaque client ne voit que les données de sa propre entreprise (`customer_grc`).  
Aucune configuration supplémentaire n'est requise.

### 4. Score de conformité

Calculé automatiquement chaque nuit via le scheduler (`daily`).  
Pour forcer un recalcul :

```bash
bench --site <nom_du_site> execute grc_module.utils.refresh_all_compliance_scores
```

---

## Notifications automatiques

Les événements suivants déclenchent des notifications :

| Événement | Déclencheur |
|-----------|-------------|
| Nouvelle violation | `after_insert` sur `violation_grc` |
| Mise à jour violation | `on_update` sur `violation_grc` |
| Nouveau plan d'action | `after_insert` sur `action_plan_grc` |
| Nouveau document | `after_insert` sur `grc_document` |
| Nouvelle demande de droits | `after_insert` sur `make_right_grc` |

---

## Mise à jour des fixtures

```bash
bench --site <nom_du_site> export-fixtures --app grc_module
git add grc_module/fixtures/
git commit -m "chore: mise à jour fixtures GRC"
```

---

## Désinstallation

```bash
bench --site <nom_du_site> uninstall-app grc_module
bench --site <nom_du_site> migrate
```

---

## Licence

MIT — AMOAMAN & ASSOCIES
