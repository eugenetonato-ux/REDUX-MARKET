# Cartographie des Routes REDUX

Tableau exhaustif des URLs de la plateforme REDUX classées par domaine et permissions d'accès.

---

## 1. Pages Publiques (`apps/pages/`)

| URL | Méthode | Vue / Action | Droits |
| :--- | :--- | :--- | :--- |
| `/` | `GET` | `pages:home` (Accueil, campagnes vedettes, statistiques) | Public |
| `/explorer/` | `GET` | `pages:explorer` (Moteur de recherche unifié campagnes & demandes) | Public |
| `/comment-ca-marche/`| `GET` | `pages:how_it_works` (Explication didactique du modèle) | Public |
| `/aide/` | `GET` | `pages:help` (FAQ & support) | Public |
| `/cgu/` | `GET` | `pages:terms` (Conditions Générales d'Utilisation) | Public |
| `/confidentialite/` | `GET` | `pages:privacy` (Protection des données personnelles) | Public |
| `/offline/` | `GET` | `pages:offline` (Page PWA de secours hors-ligne) | Public |
| `/robots.txt` | `GET` | `pages:robots_txt` (Directives d'indexation moteurs de recherche) | Public |
| `/sitemap.xml` | `GET` | `django.contrib.sitemaps.views.sitemap` | Public |

---

## 2. Authentification & Profils (`apps/accounts/`)

| URL | Méthode | Vue / Action | Droits |
| :--- | :--- | :--- | :--- |
| `/login/` | `GET, POST` | Connexion par téléphone/email et mot de passe | Public |
| `/register/` | `GET, POST` | Inscription acheteur ou commerçant | Public |
| `/logout/` | `POST` | Déconnexion sécurisée | Connecté |
| `/dashboard/` | `GET` | Espace personnel de l'acheteur (mes commandes, participations) | Acheteur connecté |

---

## 3. Campagnes d'Achats Groupés (`apps/campaigns/`)

| URL | Méthode | Vue / Action | Droits |
| :--- | :--- | :--- | :--- |
| `/campaigns/` | `GET` | Liste des campagnes actives filtrées par pays/catégorie | Public |
| `/campaigns/<slug>/` | `GET` | Fiche détaillée d'une campagne avec jauge de paliers | Public |
| `/campaigns/<slug>/join/` | `POST` | Rejoindre la campagne (crée `CampaignParticipant`) | Connecté |

---

## 4. Demandes Groupées — Marché Inversé (`apps/purchase_requests/`)

| URL | Méthode | Vue / Action | Droits |
| :--- | :--- | :--- | :--- |
| `/requests/` | `GET` | Liste des demandes groupées en cours | Public |
| `/requests/nouveau/` | `GET, POST` | Publication d'un besoin groupé (quantité et prix cible) | Connecté |
| `/requests/<id>/` | `GET` | Détail d'une demande, participants et offres reçues | Public |
| `/requests/<id>/rejoindre/` | `POST` | S'engager dans la demande groupée | Connecté |
| `/requests/<id>/proposer/` | `GET, POST` | Soumettre une offre commerciale formelle | Commerçant vérifié |
| `/requests/<id>/propositions/<prop_id>/accepter/` | `POST` | Sélectionner et valider une offre pour le groupe | Créateur / Admin |

---

## 5. Tunnel de Commande & Paiement (`apps/orders/` & `apps/payments/`)

| URL | Méthode | Vue / Action | Droits |
| :--- | :--- | :--- | :--- |
| `/checkout/<participant_id>/` | `GET, POST` | Tunnel de paiement (adresse, sélection moyen Mobile Money) | Acheteur titulaire |
| `/payments/process/<order_id>/` | `POST` | Initiation du paiement auprès du provider Mobile Money | Acheteur titulaire |
| `/payments/webhook/<provider>/` | `POST` | Réception et validation serveur-à-serveur par HMAC | Passerelle externe |
| `/orders/<order_id>/success/` | `GET` | Confirmation de commande et reçu de paiement | Acheteur titulaire |

---

## 6. Espace Commerçant (`apps/merchants/`)

| URL | Méthode | Vue / Action | Droits |
| :--- | :--- | :--- | :--- |
| `/merchant/dashboard/` | `GET` | Tableau de bord commerçant (ventes, encaissements, alertes) | Commerçant connecté |
| `/merchant/campaigns/create/` | `GET, POST` | Création d'une nouvelle campagne avec définition des paliers | Commerçant vérifié |
| `/merchant/verification/` | `GET, POST` | Dépôt des pièces légales pour obtention du badge certifié | Commerçant |

---

## 7. Administration REDUX & API Mobile

| URL | Méthode | Rôle | Droits |
| :--- | :--- | :--- | :--- |
| `/<ADMIN_URL_PATH>/` | `GET, POST` | Administration Django & KPI Dashboard | Staff / Admin |
| `/api/v1/schema/` | `GET` | Schéma OpenAPI 3 | Public |
| `/api/v1/docs/` | `GET` | Documentation Swagger interactive | Public |
| `/api/v1/*` | `GET, POST, ...` | Endpoints REST (auth, catalog, campaigns, orders, requests) | Authentification Token / JWT |
