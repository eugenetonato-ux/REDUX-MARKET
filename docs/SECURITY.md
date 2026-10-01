# Référentiel de Sécurité & Bonnes Pratiques REDUX

Ce document consacre les règles de sécurité obligatoires appliquées sur l'ensemble de la codebase REDUX conformément au cahier des charges `REDUX_SECURITY.md`.

---

## 1. Authentification & Contrôle d'Accès (RBAC)

1. **Auto-attribution de rôle interdite** :
   - Le formulaire d'inscription et l'API n'exposent que les rôles `BUYER` et `MERCHANT`.
   - Le rôle `ADMIN` ne peut être conféré que par un administrateur déjà authentifié ou via la CLI (`create_admin`).
2. **Protection Anti-IDOR (Insecure Direct Object Reference)** :
   - Les commandes, paiements, profils et participations sont toujours filtrés avec `user=request.user` côté serveur.
   - Les clés primaires ne sont jamais injectées sans contrôle de possession.
   - Les identifiants de commande utilisent une numérotation non-séquentielle cryptographiquement robuste (`RDX-YYYYMM-XXXXXX`).

---

## 2. Intégrité des Commerçants & Badge Vérifié

1. **Badge strictement conditionné** :
   - Le badge `✓ Commerçant Vérifié` n'est affiché dans les templates que si `merchant.verification_status == 'VERIFIED'`.
2. **Modération administrative obligatoire** :
   - Tout passage à l'état `VERIFIED` requiert une revue de pièces justificatives (RCCM, IFU) tracée dans `MerchantVerification` et `AuditLog`.
3. **Privilèges commerciaux exclusifs** :
   - Seuls les commerçants vérifiés ont le droit de créer des campagnes d'achats groupés et de soumettre des offres sur les demandes inversées (`apps.purchase_requests.services.create_seller_proposal`).

---

## 3. Paiements, Séquestre & Webhooks

1. **Séquestre Financier Obligatoire** :
   - Les fonds versés par les acheteurs restent consignés sur le compte séquestre technique de REDUX.
   - Le déblocage vers le compte du commerçant nécessite soit la validation du code de retrait par l'acheteur, soit l'expiration du délai légal sans litige ouvert.
2. **Validation Serveur-à-Serveur des Paiements** :
   - Le front-end ne valide jamais un paiement. La mise à jour de l'état `Order.PAID` s'effectue exclusivement lors de la réception d'un webhook émis par la passerelle Mobile Money.
3. **Signature HMAC & Idempotence** :
   - Chaque webhook est validé par signature cryptographique (ex: HMAC-SHA256).
   - L'identifiant unique de chaque événement est consigné dans la table `WebhookEvent` pour prévenir toute attaque par rejeu (*replay attack*).
   - Le montant et la devise de la transaction sont systématiquement vérifiés par rapport au montant attendu de la commande avant validation.

---

## 4. Protection Web Standard

1. **Cross-Site Request Forgery (CSRF)** :
   - Tous les formulaires POST/PUT/DELETE intègrent le token CSRF Django.
2. **Cross-Site Scripting (XSS)** :
   - Échappement automatique dans les templates Django (`autoescape on`).
   - Assainissement strict dans le dispatcher de notifications (`apps/notifications/dispatcher.py`) via `django.utils.html.escape`.
3. **Audit Log & Traçabilité** :
   - Toutes les opérations sensibles (création de campagne, changement de statut de commande, validation de commerçant, litiges) enregistrent un log immuable dans `AuditLog` (acteur, action, date, modifications JSON).
