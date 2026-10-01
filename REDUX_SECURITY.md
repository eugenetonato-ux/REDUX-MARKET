# REDUX — SECURITY.md

## Objectif

Ce document définit les règles de sécurité à appliquer tout au long du développement de **REDUX**, une plateforme africaine de commerce collectif développée avec **Django, Django REST Framework, MySQL, Redis/Celery**, où des acheteurs se regroupent pour obtenir un meilleur prix (paliers de volume) et où des commerçants répondent à des demandes collectives. Le premier marché est le Bénin, mais l'architecture est multi-pays dès le départ.

---

# Rôle de l'auditeur IA

Tu agis comme un **Architecte Sécurité Senior** spécialisé dans Django, DRF, MySQL, les paiements mobiles (Mobile Money) et les plateformes marketplace multi-pays.

Le projet est supposé avoir été développé avec l'aide d'IA (ChatGPT, Claude, Cursor, Copilot, etc.).

Tu dois :

- analyser l'intégralité de la base de code ;
- comprendre l'architecture avant toute conclusion ;
- détecter les vulnérabilités réelles ;
- proposer des corrections prêtes à copier.

Ne fais aucune supposition.

---

# Architecture de référence

```
Visiteur (public, sans compte)
   ↓
Pages publiques (offres, campagnes, boutiques, catégories, demandes) — lecture seule, contenus validés uniquement
   ↓
Inscription / Connexion (email ou téléphone) → rôle ACHETEUR ou COMMERÇANT
   ↓
Espace Acheteur  |  Espace Commerçant (authentifiés)
   ↓
Interface web + API REST (DRF, /api/v1/)
   ↓
Services métier (services.py / selectors.py par app)
   ↓
MySQL ←→ Redis (cache, quotas, files Celery)
   ↓
Stockage (media/ ou objet) — images produits, logos, documents de vérification commerçants
   ↓
Fournisseur de paiement abstrait (PaymentProvider) — webhooks signés
   ↓
Administration — /<ADMIN_URL_PATH>/ — URL secrète en .env, rôle ADMIN non auto-attribuable
```

Flux de données obligatoire : **User → CampaignParticipant → Order → Payment**. Une participation n'est jamais une commande.

Deux surfaces sont **critiques et prioritaires** au même titre :
1. **Le paiement et l'intégrité du prix** — c'est le cœur économique. Un paiement n'est valide que s'il est confirmé côté serveur (webhook signé). Aucun acheteur ne doit payer un mauvais prix, et la plateforme ne doit jamais vendre sous le prix minimum du commerçant.
2. **L'authentification et l'isolation de l'administration** — aucun utilisateur ne doit pouvoir obtenir ou s'auto-attribuer le rôle ADMIN.

---

# Méthodologie

## Passage 1 — Compréhension

Avant toute conclusion :

- analyser les vues, formulaires et serializers DRF ;
- analyser les `services.py` et `selectors.py` de chaque app ;
- analyser l'authentification (email/téléphone), les rôles et les permissions (`accounts`) ;
- analyser la vérification des commerçants (`merchants`) et la protection des documents ;
- analyser le moteur de prix (`pricing`) : paliers, prix minimum, `pricing_policy` ;
- analyser le cycle de vie des campagnes (`campaigns`) et de leurs statuts ;
- analyser la séparation participation / commande (`CampaignParticipant` / `Order`) ;
- analyser le flux de paiement, les webhooks et les remboursements (`payments`) ;
- analyser les commissions (`CommissionRule`, `PlatformTransaction`) ;
- analyser les demandes inversées et les propositions (`purchase_requests`) ;
- analyser les avis, litiges et notifications ;
- analyser le stockage média (`media/`) ;
- analyser le journal d'audit (`AuditLog`) ;
- analyser la configuration multi-pays (pays, devises, fournisseurs de paiement).

Ne conclure qu'après cette étape.

---

## Passage 2 — Audit

Chaque point reçoit obligatoirement un verdict :

- ✅ Conforme
- ❌ Vulnérable
- ⚠️ Partiel
- ⬜ Non applicable

Ne jamais regrouper plusieurs points.

---

# Checklist

## 1. Authentification & sessions

- Inscription et connexion par email ou téléphone, avec validation côté serveur du format (téléphone selon le pays)
- Mots de passe hachés (hasher Django par défaut), validateurs de mot de passe actifs
- Aucune route ne permet à un utilisateur de définir lui-même `role = ADMIN` (ni via formulaire, ni via l'API, ni via un payload manipulé)
- À l'inscription, seuls les rôles ACHETEUR et COMMERÇANT sont proposés ; le rôle ADMIN se crée uniquement par commande serveur (`create_admin`) ou par un admin existant
- Protection contre le brute-force sur `/login` et sur la connexion admin (limitation de tentatives, verrouillage temporaire)
- Réinitialisation de mot de passe par jeton à usage unique et à durée limitée ; le message ne révèle pas si le compte existe
- Sessions sécurisées (cookies `HttpOnly`, `Secure`, `SameSite`), expiration raisonnable, invalidation effective à la déconnexion
- Possibilité de désactiver un compte et de révoquer ses sessions (admin)

---

## 2. Rôles & permissions (RBAC)

- Séparation stricte : visiteur, acheteur, commerçant, administrateur ; « créateur de groupe » est un état d'un acheteur, pas un rôle privilégié
- Un commerçant ne peut modifier que sa boutique, ses produits, ses campagnes et ses propositions
- Un acheteur ne voit que ses participations, commandes, paiements, demandes et notifications
- Un commerçant ne voit les participants de sa campagne que dans la mesure nécessaire à la commande (pas de données personnelles inutiles)
- Toutes les permissions sont vérifiées à chaque vue et endpoint DRF (permission classes), jamais uniquement dans le frontend
- Contrôle d'accès au niveau de l'objet (IDOR) : accéder à `/order/<id>` ou `/api/v1/orders/<id>/` d'un autre utilisateur est impossible
- Aucune escalade de privilèges possible

---

## 3. Moteur de prix & paliers (surface critique)

- Toute la logique de prix est dans `pricing/services.py` et `pricing/calculators.py` — jamais dans les templates, vues ou JavaScript
- `validate_price_tiers` rejette les configurations incohérentes : chevauchement de bornes, trou entre paliers, palier supérieur plus cher qu'un palier inférieur, premier palier incohérent, dernier palier non ouvert
- Aucun palier ne peut descendre sous `minimum_price` ; le prix normal ne peut pas être inférieur au prix minimum
- Le prix appliqué à un participant est **recalculé côté serveur** (`pricing_policy`) ; le montant envoyé par le client n'est jamais cru
- La politique de prix (`CURRENT_TIER_PRICE` / `FINAL_TIER_PRICE`) est figée au moment de la participation et affichée avant de rejoindre
- Le créateur d'un groupe ne peut pas modifier les prix, paliers ou prix minimum définis par le commerçant
- Arrondis et types monétaires en `Decimal`, jamais en `float`
- Un palier modifié après le début d'une campagne n'affecte pas les participations existantes sans règle explicite et journalisation

---

## 4. Campagnes

- Statuts contrôlés côté serveur par une machine à états : `DRAFT → PENDING_APPROVAL → ACTIVE → TARGET_REACHED → PAYMENT_PENDING → SUCCESS`, avec `FAILED`, `EXPIRED`, `CANCELLED`, `SUSPENDED` ; pas de saut arbitraire depuis le front
- Une campagne n'est publique qu'à l'état `ACTIVE` (ou statuts terminaux consultables) ; `DRAFT` et `PENDING_APPROVAL` ne sont jamais visibles publiquement
- Un commerçant ne peut pas approuver lui-même sa campagne (modération par l'admin quand la règle l'exige)
- Les filtres de recherche ne permettent pas d'exposer des campagnes non publiées via manipulation de paramètres d'URL
- Quantités (`minimum_participants`, `maximum_participants`, stock disponible) vérifiées côté serveur ; pas de dépassement de stock en cas de participations simultanées (verrouillage `select_for_update` ou contrainte)
- Expiration automatique par tâche planifiée ; pas d'action possible sur une campagne expirée, annulée ou suspendue
- **Aucun faux compteur ni fausse participation** : les chiffres affichés proviennent uniquement de données réelles

---

## 5. Participation & commande

- `CampaignParticipant` et `Order` sont deux entités séparées ; une participation ne crée pas automatiquement une commande payée
- Un utilisateur ne peut avoir qu'une participation active par campagne (contrainte d'unicité), sauf règle métier explicite
- Un utilisateur ne peut pas rejoindre sa propre campagne de manière multiple pour gonfler les paliers (anti-abus)
- Statuts de commande et de participation contrôlés côté serveur
- Le numéro de commande (`order_number`) est unique et non prédictible de manière exploitable
- Annulation et remboursement uniquement dans les conditions prévues par les règles de la campagne

---

## 6. Paiement & webhooks (surface critique)

- Une transaction est créée avec le statut `PENDING` **avant** tout appel au prestataire
- Un paiement n'est considéré comme réussi **qu'après confirmation serveur** (webhook signé ou vérification directe auprès du prestataire) — jamais sur simple redirection navigateur vers `/payment` ou une page « success »
- Une tentative non confirmée (`FAILED`, `CANCELLED`, `PENDING` expiré) ne valide ni commande ni participation
- La signature du webhook est vérifiée (secret du prestataire) avant tout traitement ; les webhooks non signés ou invalides sont rejetés et journalisés
- Le montant et la devise confirmés par le prestataire sont comparés à ceux attendus côté serveur ; en cas d'écart, la transaction est rejetée
- Idempotence : un même webhook reçu plusieurs fois (`WebhookEvent`) ne crée pas plusieurs validations ni doubles écritures
- Transaction inconnue : réponse contrôlée, aucune donnée exposée, alerte journalisée
- Protection contre le rejeu (identifiant d'événement, horodatage)
- Le fournisseur de paiement est choisi selon pays/devise via `PaymentProvider` ; aucun code ne suppose un fournisseur unique
- Aucune donnée de carte ou secret de paiement n'est stockée ; clés en variables d'environnement
- Réconciliation régulière avec le prestataire (`reconcile_payments`) pour détecter les écarts

---

## 7. Remboursements

- Un remboursement n'est possible que pour un paiement `SUCCESS` et selon les règles de la campagne (échec, annulation, litige résolu)
- Le montant remboursé ne peut pas dépasser le montant payé ; remboursements partiels cumulés contrôlés
- Chaque remboursement est lié à un paiement, une commande et un acteur (admin/système), et journalisé dans `AuditLog`
- Idempotence des remboursements (pas de double remboursement)

---

## 8. Commerçants & vérification

- Statuts de vérification `PENDING`, `VERIFIED`, `REJECTED`, `SUSPENDED` gérés uniquement par l'admin ; un commerçant ne peut pas se vérifier lui-même
- Documents d'identification/entreprise stockés hors accès public, servis uniquement à l'admin autorisé via une vue protégée
- Les données sensibles de vérification ne sont jamais exposées sur la page boutique ni dans l'API publique
- Un commerçant suspendu ne peut plus créer ni activer de campagnes ; ses campagnes actives sont gérées selon une règle définie
- Le badge « ✓ Commerçant vérifié » n'est affiché que pour le statut `VERIFIED`

---

## 9. Commissions & revenus

- Le taux de commission n'est **jamais codé en dur** : lu depuis `CommissionRule` (pays, catégorie, type de commerçant, période, statut)
- Le calcul de commission est côté serveur ; chaque commande garde le taux et le montant appliqués (historique immuable)
- Toute modification d'une règle de commission est journalisée (`AuditLog`) et n'affecte pas rétroactivement les commandes déjà validées
- `PlatformTransaction` est append-only

---

## 10. Demandes inversées & propositions (phase 2)

- Seul le créateur de la demande (ou l'admin) peut la modifier ou la clôturer
- Un utilisateur ne peut participer qu'une fois à une même demande (unicité)
- Seuls les commerçants au statut actif/vérifié peuvent déposer une `SellerProposal` ; un commerçant ne peut pas modifier la proposition d'un autre
- Les propositions expirées (`valid_until`) ne sont plus sélectionnables
- Les règles de sélection d'une proposition sont appliquées côté serveur
- Pas de faux nombre de participants : compteur basé sur les participations réelles

---

## 11. Avis & litiges

- Un avis n'est possible qu'après une commande terminée (`COMPLETED`/`DELIVERED`) de l'utilisateur ; un seul avis par commande éligible
- Le contenu des avis est échappé (pas de HTML/JS injecté) ; modération par l'admin
- Un litige (`Dispute`) ne peut être ouvert que par l'acheteur concerné, sur sa propre commande
- Les pièces jointes des litiges suivent les règles d'upload (section 12) et ne sont visibles que des parties concernées et de l'admin

---

## 12. Images & fichiers uploadés

- Validation du type MIME réel (pas seulement l'extension) pour images produits, logos et documents de vérification
- Limitation de la taille et compression/redimensionnement des images (mobile, faible débit)
- Noms de fichiers régénérés (pas de nom fourni par l'utilisateur utilisé tel quel), aucun chemin contrôlable
- Aucun fichier uploadé n'est exécuté ; `media/` servi sans exécution de scripts
- Suppression/remplacement des images réservé au propriétaire du produit ou à l'admin
- Répertoire des documents de vérification non servi publiquement

---

## 13. API REST (DRF)

- Authentification obligatoire sur les routes privées ; routes publiques (produits, campagnes actives, boutiques) en lecture seule et limitées aux champs publics
- Permissions par rôle vérifiées à chaque endpoint, y compris `/campaigns/<id>/join/`, `/orders/`, `/payments/`
- `read_only_fields` explicites sur les champs sensibles : `role`, `status`, `price`, `commission`, `verification_status`, `payment_status`
- Pagination systématique et taille de page bornée
- Limitation de débit (throttling) sur `join`, création de commandes, paiements, connexion, inscription
- Protection CORS limitée aux domaines autorisés
- Aucune règle métier dupliquée entre API et vues web : les deux appellent les services

---

## 14. Notifications

- Aucune donnée sensible d'un autre utilisateur dans une notification
- Pas d'injection dans le contenu des emails/SMS/WhatsApp via des variables dynamiques (titres, noms, commentaires) : échappement systématique
- Limitation du taux d'envoi (anti-spam) ; respect de `NotificationPreference`
- Identifiants d'API email/SMS en variables d'environnement
- Aucune notification de type « urgence » fondée sur de fausses informations

---

## 15. Journal d'audit (AuditLog) & logs

- Journalisation : connexions admin, changements de rôle, validations/refus de commerçants et de campagnes, suspensions, changements de prix/palier, paiements, remboursements, modifications de commission, litiges, changements de paramètres
- Journaux non modifiables a posteriori (append-only) ; pas d'édition ni de suppression depuis l'admin
- Aucune donnée sensible en clair dans les logs (mots de passe, jetons, secrets de paiement, numéros complets)
- Conservation de l'historique des transactions importantes

---

## 16. Multi-pays & confidentialité

- Aucun pays, devise, indicatif ou fournisseur en dur dans le code : tout vient de `Country`, `Currency`, `PaymentProvider`, `DeliveryMethod`
- Une campagne/commande ne mélange pas les devises ; conversions interdites sans règle explicite
- Seules les données nécessaires sont collectées (email/téléphone, nom, adresse de livraison si besoin)
- Les données personnelles (téléphone, adresse, historique de paiement) ne sont jamais indexées par les moteurs de recherche
- Les pages privées portent `noindex` ; seules les pages publiques importantes sont indexables (produits, campagnes, boutiques, catégories)
- Politique de conservation limitée au strict nécessaire ; préparation aux exigences locales de protection des données (à préciser par pays)

---

## 17. Anti-fraude (architecture préparée)

- Détection de comptes multiples (même téléphone, appareil, adresse) — journalisation dès le MVP, règles avancées ensuite
- Limitation des participations suspectes (rythme anormal, pics par IP)
- Vérification des paiements et rapprochement avec le prestataire
- Détection d'activités anormales (annulations répétées, litiges récurrents, commerçants à fort taux d'échec)
- Historique des transactions et journal d'audit exploitables pour enquête

---

## 18. Secrets, configuration & déploiement

- Aucun secret dans le code source ni dans Git : tout en variables d'environnement (`SECRET_KEY`, `MYSQL_*`, `PAYMENT_*`, `EMAIL_*`)
- `DEBUG=False` en production ; `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS` renseignés
- HTTPS obligatoire, HSTS, cookies `Secure`, en-têtes de sécurité activés
- Protection CSRF active sur tous les formulaires ; l'URL d'administration provient de `ADMIN_URL_PATH`
- Sauvegardes automatiques et testées de MySQL (commandes, paiements, audit)
- Dépendances à jour et auditées ; `.env` dans `.gitignore`

---

## 19. Performance & résistance aux abus

- Index sur les champs de recherche et de statut importants
- `select_related` / `prefetch_related`, pas de requêtes N+1 sur les listes de campagnes
- Pagination partout ; cache Redis pour les listes publiques, sans jamais servir un prix périmé pour une action de paiement
- Tâches longues (notifications, expirations, réconciliation) exécutées de façon asynchrone (Celery)
- Limitation de débit sur les endpoints publics coûteux (recherche, partage)

---

## 20. Préparation évolutions futures

Vérifier que l'architecture permet d'ajouter, **sans modifier les autres modules** :

- un nouveau fournisseur de paiement (fichier `providers/<nom>.py` + enregistrement) ;
- un nouveau pays, une nouvelle devise, une nouvelle langue ;
- les abonnements commerçants (FREE / PRO / PREMIUM) ;
- la mise en avant sponsorisée ;
- des partenaires de livraison et points relais ;
- une application mobile consommant `/api/v1/` ;
- une vérification renforcée des commerçants (KYC).

---

# Format des vulnérabilités

Pour chaque vulnérabilité :

- Gravité
- Emplacement
- Description
- Impact
- Scénario d'exploitation
- Correctif prêt à copier
- Temps estimé

---

# Rapport final

Le rapport doit contenir :

1. Évaluation globale (🔴 🟠 🟡 🟢)
2. Vulnérabilités critiques
3. Corrections rapides (< 10 minutes)
4. Plan de remédiation priorisé
5. Bonnes pratiques déjà présentes
6. Résumé complet de la checklist

---

# Principes de sécurité REDUX

- Aucune confiance dans les données envoyées par le client (rôle, prix, statut de campagne, statut de paiement recalculés/vérifiés côté serveur)
- Un paiement n'est valide que sur confirmation serveur signée, jamais sur une redirection frontend
- La plateforme ne vend jamais sous le prix minimum défini par le commerçant
- Participation et commande restent séparées
- Le rôle ADMIN ne s'attribue jamais depuis l'interface utilisateur
- Une campagne n'est publique qu'après les validations prévues
- Aucun pays, devise ou fournisseur de paiement codé en dur
- Aucun faux compteur, aucune fausse participation, aucune fausse urgence
- Toutes les actions sensibles sont protégées par permissions et journalisées
- Pas de secrets dans le code source — tout en variables d'environnement
- Services à responsabilité unique (`services.py` / `selectors.py` par app)
- Journalisation sans fuite de données sensibles

Ce document est la référence de sécurité officielle du projet REDUX.
