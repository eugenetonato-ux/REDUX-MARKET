# Plan de Test & Matrice de Couverture REDUX

Ce document décrit la stratégie de test globale, la couverture des règles métier critiques et la conformité avec la checklist de sécurité `REDUX_SECURITY.md`.

---

## 1. Stratégie de Test

La suite de test REDUX repose sur **pytest** et **pytest-django**, avec base de données SQLite isolée pour l'exécution rapide et reproductible.

- **Isolation par transaction** : Chaque test s'exécute dans une transaction atomique nettoyée à la fin (`@pytest.mark.django_db`).
- **Fixtures & Usines** : Définition modulaire des utilisateurs, pays, devises, commerçants vérifiés et boutiques dans `tests/factories.py` et les `conftest.py`.
- **Zéro dépendance réseau** : Les passerelles de paiement externes (CinetPay, Paypack, Fedapay, NotchPay) sont simulées via des providers de test et des webhooks signés HMAC.

---

## 2. Matrice de Couverture des Tests

| Domaine | Fichier de Test | Scénarios Couverts | Statut |
| :--- | :--- | :--- | :---: |
| **Multi-pays & Devises** | `tests/test_multicountry/test_countries.py` | Sélection pays, devises XOF, middleware pays, isolation boutique/pays | ✅ Conforme |
| **Sécurité & RBAC** | `tests/test_permissions/test_roles.py` | Rôle ADMIN non auto-assignable, accès réservé commerçants, isolation acheteurs | ✅ Conforme |
| **Commerçants & Magasins** | `tests/test_merchants/test_verification.py` | Badge vérifié strictement réservé au statut VERIFIED, workflow de modération | ✅ Conforme |
| **Moteur de Tarification** | `tests/test_pricing/test_calculators.py` | Paliers dégressifs, seuils minimaux, économies, calcul du prix de gros | ✅ Conforme |
| **Campagnes & Concurrence** | `tests/test_campaigns/test_concurrency.py` | Réservation atomique `select_for_update`, gestion des dépassements de seuil | ✅ Conforme |
| **Commandes & Séparation** | `tests/test_orders/test_orders.py` | Invariant strict `User -> Participant -> Order -> Payment`, anti-IDOR | ✅ Conforme |
| **Paiements & Webhooks** | `tests/test_payments/test_providers.py` | Signature HMAC-SHA256, initialisation du paiement Mobile Money | ✅ Conforme |
| **Idempotence Paiements** | `tests/test_payments/test_idempotency.py` | Rejeu d'événements webhook sans doublon d'encaissement ni double validation | ✅ Conforme |
| **Marché Inversé** | `tests/test_requests/test_purchase_requests.py` | Demandes groupées, anti-doublon d'engagement, offre réservée aux marchands vérifiés | ✅ Conforme |
| **Pages, SEO & PWA** | `tests/test_pages.py` | Accueil, explorer, robots.txt avec sitemap, sitemap.xml, offline fallback | ✅ Conforme |

---

## 3. Invariants de Sécurité Contrôlés

1. **Auto-attribution de rôle interdite** : Aucun utilisateur ne peut s'auto-promouvoir `Role.ADMIN` lors de son inscription.
2. **Badge Commerçant Vérifié** : L'affichage du badge certifié n'est possible que si `verification_status == VerificationStatus.VERIFIED`.
3. **Séparation 4 couches** : Une commande (`Order`) ne peut être rattachée directement à un produit sans passer par une participation active (`CampaignParticipant`).
4. **Validation Webhook Serveur-à-Serveur** : Aucun paiement ne peut être validé par un appel direct du client front-end. Seul un webhook signé cryptographiquement ou un appel serveur authentifié modifie l'état de la commande en `PAID`.
5. **Prévention des attaques de rejeu (Replay attacks)** : Les clés d'idempotence et les identifiants d'événements webhooks sont tracés dans la table `WebhookEvent` avec contrainte d'unicité.

---

## 4. Exécution de la Suite de Test

```bash
# Exécution complète de la suite
pytest -v

# Exécution avec rapport de couverture
pytest --cov=apps -v

# Exécution ciblée par domaine
pytest tests/test_pricing/ -v
pytest tests/test_payments/ -v
pytest tests/test_requests/ -v
```
