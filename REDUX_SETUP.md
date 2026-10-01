# REDUX — Mise en place du projet (Windows / PowerShell)

Ce guide applique le prompt maître du projet **REDUX** (plateforme africaine de commerce collectif : *offre → groupe → volume → prix* et *demande → groupe → vendeurs → propositions*). Il suit ton workflow habituel (venv, `apps/`, `startapp`, `.env`, Git) et crée **tout le squelette** du projet : apps, fichiers, templates, pages, static, tests, docs, déploiement.

> Règle : on crée d'abord le squelette (fichiers vides ou minimaux). La logique métier est ensuite écrite étape par étape (section 17), avec tests à chaque étape.

---

## 0. Architecture de référence

### 0.1 Flux général

```
Visiteur (public) → offres, campagnes, boutiques, demandes (lecture seule)
   ↓
Inscription / Connexion (email ou téléphone) → rôle : ACHETEUR ou COMMERÇANT
   ↓
Acheteur                                   Commerçant
   ↓                                          ↓
Participation (CampaignParticipant)        Boutique → Produit → Campagne + PriceTier
   ↓                                          ↓
Commande (Order / OrderItem)  ←────────  Gestion commandes, revenus, stats
   ↓
Paiement (Payment → PaymentTransaction) — confirmé UNIQUEMENT par webhook serveur
   ↓
Livraison / retrait (Shipment) → Avis, Litiges
   ↓
Commission (CommissionRule → PlatformTransaction)
   ↓
Administration (Django admin durci, URL secrète, rôle ADMIN non auto-attribuable)
```

Séparation obligatoire : **User → CampaignParticipant → Order → Payment**. Une participation n'est jamais une commande.

### 0.2 Décisions d'architecture

- Monolithe Django modulaire (pas de microservices). Chaque app expose ses règles métier dans `services.py` (écriture) et `selectors.py` (lecture). Vues et API DRF appellent les mêmes services.
- `requests` du prompt devient **`purchase_requests`** : évite la confusion avec la librairie Python `requests`.
- Deux apps ajoutées au prompt (autorisé par la section 44) : `pages` (accueil, aide, conditions, SEO, sitemap) et `api` (routes `/api/v1/` fines, sans logique métier).
- Administration : Django admin personnalisé (URL en `.env`) + tableau de bord statistiques dans `core`.
- Devise, pays, indicatif, fournisseur de paiement : toujours lus en base (`countries`, `payments`), jamais en dur.
- Paramètres modifiables par l'admin (commission, frais, durées) : `PlatformSetting` et `CommissionRule` en base.

### 0.3 Applications (18) et modèles

| App | Rôle | Modèles principaux |
|---|---|---|
| `core` | Commun : timestamps, audit, paramètres, utilitaires | `TimeStampedModel` (abstrait), `AuditLog`, `PlatformSetting` |
| `countries` | Pays, devises, config locale | `Country`, `Currency` |
| `accounts` | Utilisateurs, auth, profils, rôles | `User`, `BuyerProfile` |
| `merchants` | Commerçants, vérification | `MerchantProfile`, `MerchantVerification` |
| `stores` | Boutiques | `Store` |
| `catalog` | Catalogue | `Category`, `Product`, `ProductImage`, `ProductVariant` |
| `pricing` | Paliers et moteur de prix | `PriceTier` (+ `calculators.py`, `services.py`) |
| `campaigns` | Campagnes et participations | `Campaign`, `CampaignParticipant`, `CampaignView` |
| `orders` | Commandes | `Order`, `OrderItem`, `OrderStatusHistory` |
| `payments` | Paiement abstrait, webhooks | `PaymentProvider`, `Payment`, `PaymentTransaction`, `WebhookEvent`, `Refund` |
| `deliveries` | Livraison / retrait | `DeliveryMethod`, `DeliveryZone`, `Shipment` |
| `purchase_requests` | Demande inversée (phase 2) | `PurchaseRequest`, `PurchaseRequestParticipant`, `SellerProposal` |
| `reviews` | Avis, réputation | `Review` |
| `disputes` | Réclamations | `Dispute`, `DisputeMessage` |
| `notifications` | Notifications | `Notification`, `NotificationPreference` |
| `commissions` | Commissions, revenus plateforme | `CommissionRule`, `PlatformTransaction` |
| `pages` | Pages statiques, SEO | (aucun) |
| `api` | API `/api/v1/` | (aucun) |

### 0.4 Relations clés

- `Country` 1—N `Currency` (devise par défaut du pays), `Store`, `PaymentProvider`, `DeliveryMethod`
- `User` 1—1 `BuyerProfile` ; `User` 1—1 `MerchantProfile` ; `MerchantProfile` 1—N `Store`
- `Store` 1—N `Product` ; `Category` (arbre, parent) 1—N `Product` ; `Product` 1—N `ProductImage` / `ProductVariant`
- `Campaign` N—1 `Product`, `MerchantProfile`, `User` (créateur) ; `Campaign` 1—N `PriceTier`
- `Campaign` 1—N `CampaignParticipant` N—1 `User`
- `CampaignParticipant` 1—0..1 `Order` ; `Order` 1—N `OrderItem` ; `Order` 1—N `Payment` 1—N `PaymentTransaction`
- `PaymentProvider` 1—N `Payment` ; `WebhookEvent` référence une `PaymentTransaction` (idempotence)
- `Order` 1—0..1 `Shipment` N—1 `DeliveryMethod`/`DeliveryZone`
- `Order` 1—0..1 `Review` ; `Order` 1—N `Dispute`
- `PurchaseRequest` 1—N `PurchaseRequestParticipant`, 1—N `SellerProposal`
- `CommissionRule` (pays, catégorie, type de commerçant, dates) appliquée à `Order` → `PlatformTransaction`
- `AuditLog` référence n'importe quel objet (`content_type` / `object_id`)

---

## 1. Création du dossier et de l'environnement virtuel

```powershell
mkdir Redux
cd Redux
python -m venv env
env\Scripts\activate
```

Tu dois voir `(env)` devant ton prompt avant de continuer.

Ouvre ensuite un fichier de session pour définir la fonction utilitaire utilisée dans tout le guide (à recopier dans **la même fenêtre PowerShell**) :

```powershell
function New-EmptyFile {
    param([string]$Path)
    $dir = Split-Path $Path -Parent
    if ($dir -and -not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (-not (Test-Path $Path)) { New-Item -ItemType File -Path $Path -Force | Out-Null }
}
```

---

## 2. Dépendances (fichiers `requirements/`)

```powershell
mkdir requirements

@"
Django>=5.1,<5.3
djangorestframework
drf-spectacular
django-filter
django-cors-headers
django-ratelimit
python-decouple
Pillow
mysqlclient
celery
redis
django-redis
phonenumbers
"@ | Set-Content requirements\base.txt

@"
-r base.txt
black
isort
flake8
pytest
pytest-django
pytest-cov
factory-boy
django-debug-toolbar
"@ | Set-Content requirements\development.txt

@"
-r base.txt
gunicorn
whitenoise
sentry-sdk
"@ | Set-Content requirements\production.txt

"-r requirements/development.txt" | Set-Content requirements.txt

python -m pip install --upgrade pip
pip install -r requirements\development.txt
```

> Si `mysqlclient` ne s'installe pas sous Windows (pas de wheel/compilateur), remplace-le par `pip install pymysql` et ajoute `import pymysql; pymysql.install_as_MySQLdb()` dans `config/__init__.py`.

---

## 3. Démarrage du projet Django (settings séparés)

```powershell
django-admin startproject config .

# Settings en trois fichiers : base / development / production
mkdir config\settings
Move-Item config\settings.py config\settings\base.py
New-EmptyFile config\settings\__init__.py
New-EmptyFile config\settings\development.py
New-EmptyFile config\settings\production.py

# Pointer manage.py, wsgi.py et asgi.py vers les settings de développement
foreach ($f in "manage.py", "config\wsgi.py", "config\asgi.py") {
    (Get-Content $f) -replace "config\.settings", "config.settings.development" | Set-Content $f
}

# Celery
New-EmptyFile config\celery.py
```

Dans `config\settings\base.py`, corrige `BASE_DIR` (le fichier est descendu d'un niveau) :

```python
BASE_DIR = Path(__file__).resolve().parent.parent.parent
```

---

## 4. Dossier `apps/` et création des 18 applications

```powershell
mkdir apps
New-EmptyFile apps\__init__.py

$apps = @(
    "core", "countries", "accounts", "merchants", "stores", "catalog",
    "pricing", "campaigns", "orders", "payments", "deliveries",
    "purchase_requests", "reviews", "disputes", "notifications",
    "commissions", "pages", "api"
)

foreach ($a in $apps) {
    mkdir apps\$a | Out-Null
    python manage.py startapp $a apps\$a

    # Corriger name = "apps.<app>" dans apps.py
    (Get-Content apps\$a\apps.py) -replace "name = ['""]$a['""]", "name = ""apps.$a""" | Set-Content apps\$a\apps.py

    # On utilise un package tests/ à la place de tests.py
    Remove-Item apps\$a\tests.py -ErrorAction SilentlyContinue
}
```

Vérifie qu'un `apps.py` ressemble à :

```python
# apps/campaigns/apps.py
from django.apps import AppConfig

class CampaignsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.campaigns"   # ✅ corrigé automatiquement
```

---

## 5. Fichiers communs à toutes les apps

Chaque app reçoit la même ossature : formulaires, URLs, serializers, permissions, services (écriture), selectors (lecture), signaux, tâches, validateurs, exceptions, constantes, et un dossier de tests.

```powershell
$common = @(
    "forms.py", "urls.py", "serializers.py", "permissions.py",
    "services.py", "selectors.py", "signals.py", "tasks.py",
    "validators.py", "exceptions.py", "constants.py"
)

foreach ($a in $apps) {
    foreach ($f in $common) { New-EmptyFile "apps\$a\$f" }
    New-EmptyFile "apps\$a\tests\__init__.py"
    New-EmptyFile "apps\$a\tests\test_models.py"
    New-EmptyFile "apps\$a\tests\test_services.py"
    New-EmptyFile "apps\$a\tests\test_views.py"
    New-EmptyFile "apps\$a\tests\test_permissions.py"
}
```

> `pages` et `api` n'ont pas de modèles : leurs `test_models.py` peuvent rester vides.

---

## 6. Fichiers spécifiques à chaque app

### 6.1 `core` — commun, audit, tableau de bord admin

```powershell
$core = @(
    "mixins.py", "utils.py", "audit.py", "middleware.py", "pagination.py",
    "throttling.py", "context_processors.py", "admin_dashboard.py",
    "templatetags\__init__.py", "templatetags\money.py", "templatetags\campaign_tags.py",
    "management\__init__.py", "management\commands\__init__.py",
    "management\commands\seed_all.py", "management\commands\create_admin.py"
)
foreach ($f in $core) { New-EmptyFile "apps\core\$f" }
```

### 6.2 `countries` — pays, devises, formats

```powershell
$countries = @(
    "formatters.py", "middleware.py", "context_processors.py",
    "fixtures\countries.json", "fixtures\currencies.json",
    "management\__init__.py", "management\commands\__init__.py",
    "management\commands\seed_countries.py"
)
foreach ($f in $countries) { New-EmptyFile "apps\countries\$f" }
```

### 6.3 `accounts` — utilisateurs, rôles, authentification

```powershell
$accounts = @("managers.py", "backends.py", "tokens.py", "roles.py", "decorators.py", "mixins.py")
foreach ($f in $accounts) { New-EmptyFile "apps\accounts\$f" }
```

### 6.4 `merchants` et `stores`

```powershell
foreach ($f in "verification.py", "documents.py") { New-EmptyFile "apps\merchants\$f" }
foreach ($f in "stats.py", "visibility.py") { New-EmptyFile "apps\stores\$f" }
```

### 6.5 `catalog` — produits, catégories, images

```powershell
$catalog = @(
    "image_processing.py", "slugs.py", "fixtures\categories.json",
    "management\__init__.py", "management\commands\__init__.py",
    "management\commands\seed_categories.py"
)
foreach ($f in $catalog) { New-EmptyFile "apps\catalog\$f" }
```

### 6.6 `pricing` — moteur de prix (cœur du produit)

```powershell
$pricing = @("calculators.py", "policies.py")
foreach ($f in $pricing) { New-EmptyFile "apps\pricing\$f" }
New-EmptyFile "apps\pricing\tests\test_calculators.py"
New-EmptyFile "apps\pricing\tests\test_tiers_validation.py"
New-EmptyFile "apps\pricing\tests\test_policies.py"
```

Fonctions à implémenter (étape 6) : `calculate_current_tier`, `calculate_current_price`, `get_next_tier`, `get_remaining_participants`, `calculate_savings`, `validate_price_tiers`.

### 6.7 `campaigns`

```powershell
$campaigns = @(
    "state_machine.py", "share.py", "sitemaps.py", "progress.py",
    "management\__init__.py", "management\commands\__init__.py",
    "management\commands\close_expired_campaigns.py"
)
foreach ($f in $campaigns) { New-EmptyFile "apps\campaigns\$f" }
New-EmptyFile "apps\campaigns\tests\test_state_machine.py"
New-EmptyFile "apps\campaigns\tests\test_participation.py"
New-EmptyFile "apps\campaigns\tests\test_expiration.py"
```

### 6.8 `orders`

```powershell
foreach ($f in "numbering.py", "state_machine.py") { New-EmptyFile "apps\orders\$f" }
New-EmptyFile "apps\orders\tests\test_order_lifecycle.py"
New-EmptyFile "apps\orders\tests\test_refunds.py"
```

### 6.9 `payments` — abstraction multi-fournisseurs et webhooks

```powershell
$payments = @(
    "webhooks.py", "reconciliation.py", "refunds.py",
    "providers\__init__.py", "providers\base.py",
    "providers\registry.py", "providers\mock.py",
    "management\__init__.py", "management\commands\__init__.py",
    "management\commands\reconcile_payments.py"
)
foreach ($f in $payments) { New-EmptyFile "apps\payments\$f" }
New-EmptyFile "apps\payments\tests\test_webhooks.py"
New-EmptyFile "apps\payments\tests\test_idempotency.py"
New-EmptyFile "apps\payments\tests\test_providers.py"
```

Un nouveau prestataire = un nouveau fichier `providers\<nom>.py` qui hérite de `providers\base.py`, enregistré dans `registry.py`. Aucun autre module ne change.

### 6.10 `deliveries`, `purchase_requests`, `reviews`, `disputes`

```powershell
New-EmptyFile apps\deliveries\fees.py
foreach ($f in "state_machine.py", "expiration.py", "proposals.py") { New-EmptyFile "apps\purchase_requests\$f" }
New-EmptyFile apps\reviews\eligibility.py
New-EmptyFile apps\disputes\state_machine.py
```

### 6.11 `notifications` — canaux et événements

```powershell
$notifications = @(
    "events.py", "dispatcher.py",
    "channels\__init__.py", "channels\in_app.py", "channels\email.py",
    "channels\sms.py", "channels\whatsapp.py"
)
foreach ($f in $notifications) { New-EmptyFile "apps\notifications\$f" }
```

### 6.12 `commissions`

```powershell
foreach ($f in "calculators.py", "ledger.py") { New-EmptyFile "apps\commissions\$f" }
New-EmptyFile apps\commissions\tests\test_calculators.py
```

### 6.13 `pages` — pages statiques et SEO

```powershell
foreach ($f in "seo.py", "sitemaps.py", "robots.py") { New-EmptyFile "apps\pages\$f" }
```

### 6.14 `api` — `/api/v1/`

```powershell
$api = @(
    "v1\__init__.py", "v1\urls.py", "v1\auth.py", "v1\products.py",
    "v1\campaigns.py", "v1\orders.py", "v1\payments.py",
    "v1\requests.py", "v1\notifications.py", "v1\schema.py"
)
foreach ($f in $api) { New-EmptyFile "apps\api\$f" }
```

> Les vues API n'ont **aucune** règle métier : elles appellent les `services.py` / `selectors.py` des apps.

---

## 7. Templates (toutes les pages du projet)

```powershell
$templates = @(
    # Bases et composants réutilisables
    "base\base.html", "base\base_dashboard.html", "base\base_merchant.html", "base\base_auth.html",
    "partials\header.html", "partials\footer.html", "partials\bottom_nav.html",
    "partials\messages.html", "partials\pagination.html", "partials\seo_meta.html",
    "partials\price.html", "partials\campaign_card.html", "partials\campaign_progress.html",
    "partials\tier_table.html", "partials\share_buttons.html", "partials\empty_state.html",
    "partials\skeleton.html", "partials\verified_badge.html", "partials\status_badge.html",

    # Pages publiques
    "pages\home.html", "pages\explorer.html", "pages\categories.html", "pages\category_detail.html",
    "pages\how_it_works.html", "pages\help.html", "pages\terms.html", "pages\privacy.html",
    "pages\offline.html", "errors\403.html", "errors\404.html", "errors\500.html",

    # Authentification
    "accounts\login.html", "accounts\register.html", "accounts\register_merchant.html",
    "accounts\forgot_password.html", "accounts\reset_password_confirm.html",
    "accounts\verify_email.html", "accounts\verify_phone.html",

    # Catalogue, boutiques, campagnes
    "catalog\product_list.html", "catalog\product_detail.html",
    "stores\store_list.html", "stores\store_detail.html",
    "campaigns\campaign_list.html", "campaigns\campaign_detail.html",
    "campaigns\campaign_create.html", "campaigns\campaign_join.html", "campaigns\campaign_share.html",

    # Demandes inversées (phase 2)
    "purchase_requests\request_list.html", "purchase_requests\request_detail.html",
    "purchase_requests\request_create.html", "purchase_requests\request_join.html",

    # Tunnel de commande et paiement
    "checkout\checkout.html", "checkout\payment.html", "checkout\payment_pending.html",
    "checkout\payment_success.html", "checkout\payment_failed.html", "checkout\order_detail.html",

    # Tableau de bord acheteur
    "dashboard\index.html", "dashboard\campaigns.html", "dashboard\participations.html",
    "dashboard\orders.html", "dashboard\requests.html", "dashboard\payments.html",
    "dashboard\favorites.html", "dashboard\notifications.html", "dashboard\profile.html",

    # Espace commerçant
    "merchant\dashboard.html", "merchant\products.html", "merchant\product_form.html",
    "merchant\campaigns.html", "merchant\campaign_form.html", "merchant\campaign_detail.html",
    "merchant\participants.html", "merchant\orders.html", "merchant\order_detail.html",
    "merchant\requests.html", "merchant\proposals.html", "merchant\proposal_form.html",
    "merchant\revenue.html", "merchant\statistics.html", "merchant\store.html", "merchant\settings.html",

    # Avis et litiges
    "reviews\review_form.html", "disputes\dispute_form.html",
    "disputes\dispute_list.html", "disputes\dispute_detail.html",

    # Surcharges de l'administration Django
    "admin\index.html", "admin\base_site.html",

    # Emails
    "emails\base_email.html", "emails\welcome.html", "emails\password_reset.html",
    "emails\campaign_joined.html", "emails\new_participant.html", "emails\tier_reached.html",
    "emails\tier_close.html", "emails\campaign_ending.html", "emails\campaign_success.html",
    "emails\campaign_failed.html", "emails\payment_success.html", "emails\payment_failed.html",
    "emails\order_confirmed.html", "emails\order_shipped.html", "emails\order_delivered.html",
    "emails\new_proposal.html", "emails\request_expiring.html"
)
foreach ($t in $templates) { New-EmptyFile "templates\$t" }
```

---

## 8. Static, PWA, media, logs

```powershell
$static = @(
    "css\base.css", "css\components.css", "css\campaign.css", "css\dashboard.css", "css\merchant.css", "css\admin.css",
    "js\main.js", "js\campaign_progress.js", "js\share.js", "js\explorer.js", "js\checkout.js", "js\pwa.js",
    "manifest.json", "service-worker.js", "robots.txt"
)
foreach ($s in $static) { New-EmptyFile "static\$s" }

mkdir static\images, static\icons, static\vendor, static\fonts | Out-Null

mkdir media\products, media\stores, media\profiles, media\merchant_documents | Out-Null
mkdir staticfiles, logs, backups, scripts, locale | Out-Null
```

> `media\merchant_documents` contient des pièces sensibles de vérification : ne jamais l'exposer publiquement (voir `SECURITY.md`).

---

## 9. Tests, documentation, déploiement et configuration

```powershell
# Tests transverses
$tests = @(
    "conftest.py", "factories.py",
    "test_pricing\__init__.py", "test_pricing\test_tiers.py", "test_pricing\test_min_price.py",
    "test_campaigns\__init__.py", "test_campaigns\test_lifecycle.py",
    "test_orders\__init__.py", "test_orders\test_orders.py",
    "test_payments\__init__.py", "test_payments\test_webhooks.py",
    "test_permissions\__init__.py", "test_permissions\test_roles.py",
    "test_multicountry\__init__.py", "test_multicountry\test_currency_country.py",
    "test_requests\__init__.py", "test_requests\test_purchase_requests.py"
)
foreach ($t in $tests) { New-EmptyFile "tests\$t" }

# Documentation
$docs = @(
    "README.md",
    "docs\ARCHITECTURE.md", "docs\DATABASE.md", "docs\API.md", "docs\BUSINESS_RULES.md",
    "docs\DEPLOYMENT.md", "docs\SECURITY.md",
    "docs\ERD.md", "docs\USER_FLOWS.md", "docs\ROUTES.md", "docs\TEST_PLAN.md",
    "docs\MULTI_COUNTRY.md", "docs\ROADMAP.md"
)
foreach ($d in $docs) { New-EmptyFile $d }

# Déploiement
$deploy = @(
    "Dockerfile", "docker-compose.yml", "deploy\gunicorn.conf.py",
    "deploy\nginx.conf", "deploy\celery.service", "deploy\gunicorn.service"
)
foreach ($d in $deploy) { New-EmptyFile $d }

# Qualité de code
$config = @("pytest.ini", "setup.cfg", "pyproject.toml", ".editorconfig", ".flake8")
foreach ($c in $config) { New-EmptyFile $c }
```

Contenu de `pytest.ini` :

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = tests.py test_*.py *_tests.py
addopts = -q --reuse-db
```

---

## 10. Fichiers `.env` et `.env.example`

```powershell
New-EmptyFile .env.example
New-EmptyFile .env
New-EmptyFile .gitignore
```

Contenu de `.env.example` (à copier dans `.env` puis remplir ; **ne jamais commiter `.env`**) :

```
# Général
DEBUG=True
SECRET_KEY=change-moi-en-production
ALLOWED_HOSTS=127.0.0.1,localhost
PLATFORM_NAME=REDUX
DEFAULT_COUNTRY_CODE=BJ
DEFAULT_LANGUAGE=fr

# Administration (URL non devinable)
ADMIN_URL_PATH=cpanel-redux

# Base de données MySQL
MYSQL_DATABASE=redux
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306

# Redis / Celery
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1

# Paiement (fournisseur choisi en base ; ces clés sont celles du fournisseur actif)
PAYMENT_PROVIDER=mock
PAYMENT_API_KEY=
PAYMENT_SECRET=
PAYMENT_WEBHOOK_SECRET=

# Email
DEFAULT_FROM_EMAIL=noreply@redux.app
EMAIL_HOST=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
ADMIN_NOTIFICATION_EMAIL=

# Sécurité (production)
CSRF_TRUSTED_ORIGINS=
SENTRY_DSN=
```

`.gitignore` :

```powershell
Add-Content .gitignore "env/`n.env`n__pycache__/`n*.pyc`nmedia/`nstaticfiles/`nlogs/`nbackups/`n.pytest_cache/`n.coverage`ndb.sqlite3"
```

---

## 11. Configuration `config/settings/base.py`

### a) Imports et variables sensibles

```python
from pathlib import Path
from decouple import config, Csv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

PLATFORM_NAME = config("PLATFORM_NAME", default="REDUX")
ADMIN_URL_PATH = config("ADMIN_URL_PATH", default="cpanel-redux")
DEFAULT_COUNTRY_CODE = config("DEFAULT_COUNTRY_CODE", default="BJ")
```

> `DEFAULT_COUNTRY_CODE` n'est qu'une valeur de secours pour l'affichage initial. Devise, indicatif et formats sont lus depuis `countries.Country`.

### b) `INSTALLED_APPS`

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",

    # Tiers
    "rest_framework",
    "drf_spectacular",
    "corsheaders",
    "django_filters",

    # Apps Redux
    "apps.core",
    "apps.countries",
    "apps.accounts",
    "apps.merchants",
    "apps.stores",
    "apps.catalog",
    "apps.pricing",
    "apps.campaigns",
    "apps.orders",
    "apps.payments",
    "apps.deliveries",
    "apps.purchase_requests",
    "apps.reviews",
    "apps.disputes",
    "apps.notifications",
    "apps.commissions",
    "apps.pages",
    "apps.api",
]
```

### c) `MIDDLEWARE`

```python
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.countries.middleware.CountryMiddleware",
]
```

### d) Authentification et rôles

```python
AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailOrPhoneBackend",
]

LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/dashboard"
LOGOUT_REDIRECT_URL = "/"
```

> Rappel : le rôle (`BUYER`, `MERCHANT`) est choisi à l'inscription ; `ADMIN` n'est **jamais** sélectionnable depuis l'interface. Un admin se crée uniquement par `python manage.py create_admin` (voir section 13). Le « créateur de groupe » n'est pas un rôle : c'est un acheteur qui a créé une campagne.

### e) Base de données MySQL

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("MYSQL_DATABASE"),
        "USER": config("MYSQL_USER"),
        "PASSWORD": config("MYSQL_PASSWORD"),
        "HOST": config("MYSQL_HOST", default="127.0.0.1"),
        "PORT": config("MYSQL_PORT", default="3306"),
        "OPTIONS": {"charset": "utf8mb4"},
        "CONN_MAX_AGE": 60,
    }
}
```

### f) Templates

```python
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.platform",
                "apps.countries.context_processors.country",
            ],
        },
    },
]
```

### g) Internationalisation (français d'abord, anglais préparé)

```python
LANGUAGE_CODE = "fr"
LANGUAGES = [("fr", "Français"), ("en", "English")]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
USE_TZ = True
TIME_ZONE = "UTC"
```

### h) Static / Media

```python
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
```

### i) Django REST Framework

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {"anon": "60/min", "user": "240/min"},
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}
```

### j) Cache Redis et Celery

```python
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/0"),
    }
}

CELERY_BROKER_URL = config("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/1")
CELERY_TASK_ALWAYS_EAGER = False
```

`config/celery.py` :

```python
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
app = Celery("redux")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
```

`config/__init__.py` :

```python
from .celery import app as celery_app

__all__ = ("celery_app",)
```

### k) `development.py`

```python
from .base import *  # noqa

DEBUG = True
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
```

### l) `production.py`

```python
from .base import *  # noqa

DEBUG = False
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_CONTENT_TYPE_NOSNIFF = True
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())
```

---

## 12. Configuration `config/urls.py`

Routes du prompt (section 46), organisées par app. Aucun pays ni devise dans les URLs.

```python
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Administration (URL secrète, non devinable)
    path(f"{settings.ADMIN_URL_PATH}/", admin.site.urls),

    # API mobile-ready
    path("api/v1/", include("apps.api.v1.urls")),

    # Authentification
    path("", include("apps.accounts.urls")),                 # /login /register /forgot-password /dashboard/profile

    # Pages publiques
    path("", include("apps.pages.urls")),                    # / /explorer /categories /help /terms /privacy
    path("products/", include("apps.catalog.urls")),         # /products/<slug>
    path("stores/", include("apps.stores.urls")),            # /stores/<slug>
    path("campaigns/", include("apps.campaigns.urls")),      # /campaigns /campaigns/<slug>
    path("requests/", include("apps.purchase_requests.urls")),  # /requests /requests/<id>

    # Tunnel de commande
    path("", include("apps.orders.urls")),                   # /checkout /order/<id>
    path("", include("apps.payments.urls")),                 # /payment (+ webhooks)

    # Espaces connectés
    path("dashboard/", include("apps.accounts.urls_dashboard")),
    path("merchant/", include("apps.merchants.urls")),

    # Autres
    path("reviews/", include("apps.reviews.urls")),
    path("disputes/", include("apps.disputes.urls")),
    path("notifications/", include("apps.notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Pour que ce fichier fonctionne, crée aussi le fichier d'URLs du tableau de bord acheteur (les autres `urls.py` existent déjà via la section 5) :

```powershell
New-EmptyFile apps\accounts\urls_dashboard.py
```

Le webhook de paiement est exposé sur `POST /payments/webhook/<provider>/` (déclaré dans `apps\payments\urls.py`, protégé par vérification de signature).

---

## 13. MySQL, migrations et administrateur

Crée la base (dans MySQL) :

```sql
CREATE DATABASE redux CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Puis :

```powershell
python manage.py makemigrations
python manage.py migrate
```

Données de départ (pays, devises, catégories) :

```powershell
python manage.py seed_countries
python manage.py seed_categories
```

> ⚠️ L'administrateur n'est **pas** créé via une inscription publique. Il est créé par la commande dédiée `create_admin` (à écrire dans `apps\core\management\commands\create_admin.py`), ou à défaut :

```powershell
python manage.py createsuperuser
```

Vérifier les utilisateurs par rôle :

```powershell
python manage.py shell -c "from apps.accounts.models import User; print(User.objects.filter(role='ADMIN').count())"
```

Tâches asynchrones (dans un second terminal, Redis démarré) :

```powershell
celery -A config worker --loglevel=info --pool=solo
celery -A config beat --loglevel=info
```

---

## 14. Lancement du serveur

```powershell
python manage.py runserver
```

- Site public : `http://127.0.0.1:8000/`
- Explorer : `http://127.0.0.1:8000/explorer`
- Espace acheteur : `http://127.0.0.1:8000/dashboard`
- Espace commerçant : `http://127.0.0.1:8000/merchant/dashboard`
- Administration : `http://127.0.0.1:8000/<ADMIN_URL_PATH>/` (valeur dans `.env`)
- Documentation API : `http://127.0.0.1:8000/api/v1/docs/`

---

## 15. Toutes les routes du projet

| Zone | Route | Accès |
|---|---|---|
| Public | `/`, `/explorer`, `/categories`, `/help`, `/terms`, `/privacy` | Visiteur |
| Public | `/campaigns`, `/campaigns/<slug>`, `/products/<slug>`, `/stores/<slug>` | Visiteur |
| Public | `/requests`, `/requests/<id>` | Visiteur (lecture) |
| Auth | `/login`, `/register`, `/forgot-password` | Visiteur |
| Acheteur | `/dashboard`, `/dashboard/campaigns`, `/dashboard/orders`, `/dashboard/requests`, `/dashboard/notifications`, `/dashboard/profile` | Acheteur |
| Acheteur | `/checkout`, `/payment`, `/order/<id>` | Acheteur (propriétaire de la commande) |
| Commerçant | `/merchant/dashboard`, `/merchant/products`, `/merchant/products/create` | Commerçant |
| Commerçant | `/merchant/campaigns`, `/merchant/campaigns/create`, `/merchant/orders` | Commerçant |
| Commerçant | `/merchant/requests`, `/merchant/proposals`, `/merchant/revenue`, `/merchant/statistics`, `/merchant/settings` | Commerçant |
| API | `/api/v1/auth/`, `/products/`, `/campaigns/`, `/campaigns/<id>/`, `/campaigns/<id>/join/`, `/orders/`, `/payments/`, `/requests/`, `/notifications/` | Selon permissions |
| Système | `/payments/webhook/<provider>/`, `/sitemap.xml`, `/robots.txt` | Serveur / robots |
| Admin | `/<ADMIN_URL_PATH>/` | Rôle ADMIN uniquement |

---

## 16. Structure finale du projet

```
Redux/
├── manage.py
├── config/
│   ├── settings/ (base.py, development.py, production.py)
│   ├── celery.py, urls.py, wsgi.py, asgi.py
├── apps/
│   ├── core/ countries/ accounts/ merchants/ stores/ catalog/
│   ├── pricing/ campaigns/ orders/ payments/ deliveries/
│   ├── purchase_requests/ reviews/ disputes/ notifications/
│   └── commissions/ pages/ api/
├── templates/  (base, partials, pages, accounts, catalog, stores, campaigns,
│                purchase_requests, checkout, dashboard, merchant, reviews,
│                disputes, admin, emails, errors)
├── static/     (css, js, images, icons, manifest.json, service-worker.js)
├── media/      (products, stores, profiles, merchant_documents)
├── tests/      (conftest.py, factories.py + un dossier par domaine)
├── docs/       (ARCHITECTURE, DATABASE, API, BUSINESS_RULES, DEPLOYMENT, SECURITY, ERD, …)
├── deploy/     (gunicorn, nginx, celery)
├── requirements/ (base.txt, development.txt, production.txt)
├── locale/
├── .env.example  .gitignore  README.md  requirements.txt
└── Dockerfile  docker-compose.yml  pytest.ini  pyproject.toml
```

---

## 17. Ordre de développement recommandé (13 étapes)

À chaque étape : tester, corriger, documenter, vérifier permissions et règles métier, éviter les régressions.

1. **Architecture + modèles** — `core`, `countries` (Country, Currency), ERD dans `docs\ERD.md`, tous les modèles + migrations
2. **Authentification + rôles** — `accounts` : `User` (email/téléphone), `BuyerProfile`, rôles, permissions
3. **Commerçants + boutiques** — `merchants`, `stores`, statuts de vérification
4. **Produits + catégories** — `catalog`, catégories gérées depuis l'admin
5. **Campagnes + paliers** — `campaigns`, `pricing.PriceTier`, `validate_price_tiers`
6. **Participations + moteur de prix** — `CampaignParticipant`, `pricing.services`, `pricing_policy`
7. **Commandes** — `orders`
8. **Paiements** — `payments` : fournisseur abstrait, webhooks signés, idempotence
9. **Notifications** — `notifications`, `NotificationPreference`
10. **Administration** — Django admin, modération, tableau de bord statistiques
11. **Tests** — couverture complète selon `docs\TEST_PLAN.md`
12. **Demande inversée** — `purchase_requests` (après validation du MVP)
13. **Optimisation** — index, `select_related`/`prefetch_related`, cache, SEO, PWA, i18n anglais

---

## 18. Commandes utiles (rappel de ton workflow)

```powershell
# Qualité de code
black .
isort .
flake8

# Tests
pytest
pytest --cov=apps

# Traductions
python manage.py makemessages -l fr -l en
python manage.py compilemessages

# Mise à jour GitHub
git status
git add .
git commit -m "mise a jour"
git push origin main
```
