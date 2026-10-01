# REDUX — Design System (Site public + Espaces Acheteur/Commerçant + Administration)

Ce document définit l'identité visuelle de la plateforme, pensée **mobile-first** : la majorité des utilisateurs viendront d'un smartphone, avec une connexion mobile moyenne.

Trois univers visuels cohérents :
- **Site public + espace acheteur** : moderne, simple, rassurant, orienté confiance (on parle d'argent et de groupes).
- **Espace commerçant** : tableau de bord clair, orienté ventes, campagnes et revenus.
- **Back-office admin** : dashboard dense, sombre, orienté supervision et modération.

Le style doit être **africain sans tomber dans les clichés visuels** : pas de motifs folkloriques plaqués, pas de caricature. L'identité vient du contraste noir / blanc, du dégradé vert-bleu du logo, de la lisibilité et de l'énergie du collectif.

---

## 1. Palette de couleurs

Palette tirée du **logo 2** (texte blanc sur fond noir, X en dégradé vert → bleu). Les codes sont estimés à l'œil à partir de l'image : à vérifier à la pipette ou avec le fichier source du logo avant de les figer.

### Couleurs de marque
| Rôle | Code | Origine |
|---|---|---|
| Noir de marque | `#0A0A0F` | Fond du logo |
| Blanc de marque | `#FFFFFF` | Lettres REDUX |
| Vert du X | `#1FE06A` | Début du dégradé |
| Bleu du X | `#0A6CFF` | Fin du dégradé |
| Dégradé signature | `linear-gradient(135deg, #1FE06A, #0A6CFF)` | Le X |

### Site public & espace acheteur
| Rôle | Couleur | Usage |
|---|---|---|
| Primaire (bleu) | `#0A6CFF` | Boutons principaux (« Rejoindre »), liens actifs |
| Primaire foncé | `#0753C9` | Hover, états pressés |
| Succès / économie (vert) | `#12B76A` | Prix actuel, économie, palier atteint, paiement confirmé |
| Dégradé | vert → bleu | Barre de progression des paliers, badges de mise en avant |
| Fond sombre | `#0A0A0F` | Header, pied de page, héro |
| Surface sombre | `#14141C` | Cartes sur fond sombre |
| Fond clair | `#FFFFFF` / `#F6F8FB` | Fond général des pages |
| Texte | `#0F172A` | Titres et corps sur fond clair |
| Texte secondaire | `#64748B` | Descriptions, labels |
| Bordures | `#E2E8F0` | Séparateurs, champs de formulaire |
| Attention | `#F59E0B` | Campagne bientôt terminée, en attente |
| Erreur | `#EF4444` | Paiement échoué, campagne échouée, erreurs de formulaire |
| Information | `#0A6CFF` | Messages neutres |

### Espace commerçant
| Rôle | Couleur | Usage |
|---|---|---|
| Sidebar / header | `#0A0A0F` | Navigation commerçant |
| Accent | `#0A6CFF` | Actions principales (créer une campagne) |
| Revenus / succès | `#12B76A` | Chiffre d'affaires, campagnes réussies |
| Fond | `#F6F8FB` | Fond de page |

### Back-office admin
| Rôle | Couleur | Usage |
|---|---|---|
| Sidebar | `#0A0A0F` | Navigation |
| Accent | `#0A6CFF` | Boutons, graphiques |
| Fond général | `#F1F5F9` | Fond de page |
| Cartes | `#FFFFFF` avec ombre douce | Blocs de contenu et statistiques |
| Succès | `#12B76A` | Campagne approuvée, paiement réussi |
| Attention | `#F59E0B` | En attente de validation |
| Erreur | `#EF4444` | Compte ou boutique suspendus, paiement échoué |

### Logique d'usage
- **Bleu = action et confiance** : boutons, liens, navigation.
- **Vert = argent économisé** : tout ce qui touche au prix, à l'économie et à la réussite.
- **Dégradé vert → bleu** : réservé au logo et à la barre de progression, pour que la progression vers le prochain palier reste l'élément le plus reconnaissable.
- Header et héro sur fond noir avec le logo blanc ; contenu sur fond clair pour la lisibilité. Une version du logo à texte foncé est nécessaire pour les fonds clairs.

Contrastes : tous les couples texte/fond respectent au moins le ratio WCAG AA (4,5:1). Le vert vif `#1FE06A` n'est jamais utilisé comme couleur de texte sur fond clair (utiliser `#12B76A` ou plus foncé) : il est réservé aux éléments graphiques et aux fonds sombres.

---

## 2. Typographie

- **Titres (H1-H3)** : sans-serif géométrique grasse (type *Sora* ou *Poppins* SemiBold/Bold).
- **Corps de texte** : sans-serif régulière (type *Inter*), lisible à petite taille sur mobile.
- **Prix** : toujours en gras, avec espace fine insécable entre les milliers et devise lue depuis la base : `15 000 XOF`. Le symbole ou code de la devise vient de `Currency`, jamais codé en dur.
- Pile de secours obligatoire (`system-ui, sans-serif`) ; limiter à 2 familles et 3 graisses pour alléger le chargement.

---

## 3. Élément visuel central : la progression de campagne

C'est le composant le plus important du produit (`partials/campaign_progress.html`). Il doit être compris en une seconde.

```
14 / 20 participants
██████████████░░░░░░
Prix actuel : 12 500 XOF
Prochain palier : 20 personnes → 11 000 XOF
Il manque 6 personnes
```

Règles :
- Barre de progression **vers le prochain palier**, avec les paliers marqués sur la barre (repères discrets).
- Le **prix actuel** est le plus visible (gras, couleur accent économie) ; le prix normal est barré en gris.
- Le texte « Il manque N personnes » est toujours calculé côté serveur à partir des données réelles.
- Au palier maximum : message « Meilleur prix atteint » à la place du prochain palier.
- Mise à jour après chaque participation sans recharger toute la page (progressive enhancement : la page reste exacte sans JavaScript).
- La progression doit donner envie de partager, **sans fausse urgence ni faux compteur** : aucun chiffre inventé, aucun minuteur factice, aucun « X personnes regardent cette offre » non réel.

---

## 4. Site public — Composants

### 4.1 En-tête (mobile-first)
- Logo « REDUX » à gauche
- Icône de recherche (ouvre la barre de recherche en plein écran)
- Bouton « Se connecter » / avatar si connecté
- Sur mobile : **barre de navigation basse** (Accueil, Explorer, Mes campagnes, Notifications, Profil)
- Sélecteur de pays et de langue discret (fr, en) dans le menu

### 4.2 Page d'accueil (`/`)
La page doit expliquer le concept immédiatement.

- **Bannière héro** : titre « Achetez ensemble, payez moins » + sous-texte + CTA « Voir les offres en cours » / « Comment ça marche »
- **Offres en cours** (section principale) : cartes de campagne avec progression
- Sections suivantes : offres populaires, campagnes proches de la fin, meilleures économies, nouvelles campagnes, catégories, boutiques populaires, demandes des acheteurs, comment ça marche
- Chaque section est une rangée horizontale défilable sur mobile (pas une longue pile de cartes énormes)

### 4.3 Carte de campagne
- Photo produit optimisée (WebP, dimensions fixes pour éviter les sauts de mise en page)
- Titre, boutique (badge « ✓ Commerçant vérifié » si applicable)
- Prix normal barré → **prix actuel**
- Barre de progression compacte + « 14 / 20 personnes »
- Mention « Encore 6 personnes → 11 000 XOF »
- Temps restant (réel)
- Bouton **REJOINDRE**
- Grille responsive : 1 colonne mobile, 2 tablette, 3-4 desktop

### 4.4 Page Explorer (`/explorer`)
- Recherche : produits, campagnes, boutiques, catégories, demandes
- Filtres dans un panneau glissant (bottom sheet) sur mobile : catégorie, pays, prix, réduction, nombre de participants, fin prochaine, boutique, disponibilité
- Tri et pagination (pas de défilement infini lourd)
- Skeleton loaders pendant le chargement

### 4.5 Page détail de campagne (`/campaigns/<slug>`)
Page la plus importante après l'accueil. Ordre sur mobile :

1. Galerie d'images (swipe)
2. Titre, boutique, badge de vérification
3. Prix normal, **prix actuel**, économie réalisée
4. **Composant de progression** (section 3)
5. **Tableau des paliers** avec le palier actuel mis en évidence :

```
1–4 personnes    15 000 XOF
5–9              13 500 XOF
10–19            12 500 XOF  ← PRIX ACTUEL
20–49            11 000 XOF
50+              10 000 XOF
```

6. Règles de la campagne : politique de prix (`pricing_policy`), conditions, date de fin, quantité disponible, frais de livraison, règles de remboursement, commission si pertinente
7. Livraison / retrait
8. Informations du commerçant, avis
9. CTA principal **REJOINDRE LA CAMPAGNE** (collant en bas d'écran sur mobile) + CTA secondaire **PARTAGER**

Avant de rejoindre, la règle de prix retenue est affichée clairement (« Vous payez le prix du palier atteint à la clôture » ou « Vous payez le prix du palier actuel »).

### 4.6 Partage (stratégique)
- Bouton **PARTAGER** ouvre un panneau : WhatsApp, Facebook, autres réseaux, copier le lien
- Message prérempli, rempli avec des données réelles :

```
🔥 On peut avoir ces sneakers à 11 000 XOF au lieu de 15 000 XOF.
Nous sommes actuellement 14/20. Il manque seulement 6 personnes.
Rejoins le groupe : [LIEN]
```

- Aperçu propre sur WhatsApp : balises Open Graph (image, titre, description avec prix et progression)

### 4.7 Tunnel de commande et paiement
- Parcours le plus court possible : récapitulatif → choix du moyen de paiement (selon pays) → confirmation
- Récapitulatif transparent : prix, quantité, frais de livraison, frais éventuels, total, règles de remboursement
- États visuels distincts : **en attente / confirmé / échoué**, jamais « réussi » avant confirmation serveur
- Page d'attente de paiement qui interroge le statut réel, avec message rassurant et possibilité de réessayer

---

## 5. Espace Acheteur (`/dashboard`)

- Aperçu : campagnes suivies, participations, commandes, notifications
- Sections : mes campagnes, mes participations, mes commandes, mes demandes, mes paiements, mes favoris, notifications, profil
- Suivi de commande en frise (confirmée → préparée → expédiée → livrée)
- Historique des paiements (montant, campagne, date, statut)
- Bouton « Signaler un problème » sur chaque commande (litige)
- Notifications : palier atteint, prochain palier proche, campagne bientôt terminée, résultat de campagne, paiement, livraison

---

## 6. Espace Commerçant (`/merchant/dashboard`)

- Cartes chiffrées : chiffre d'affaires, commandes, campagnes actives, participants, commissions, revenus nets
- Menu : Vue d'ensemble, Produits, Campagnes, Commandes, Demandes, Propositions, Revenus, Statistiques, Boutique, Paramètres
- **Formulaire de création de campagne en étapes** : infos générales → prix (normal, minimum) → paliers → conditions (dates, quantités) → livraison → aperçu

Tableau de paliers éditable :

| Minimum | Maximum | Prix |
|---|---|---|
| 1 | 4 | 15 000 |
| 5 | 9 | 13 500 |
| 20 | 49 | 11 000 |
| 50 | ∞ | 10 000 |

- Validation en direct des paliers (erreur claire si palier incohérent ou sous le prix minimum), la validation définitive reste côté serveur
- Statistiques simples : vues, participants, commandes, taux de conversion, chiffre d'affaires, économie moyenne générée, campagnes réussies/échouées, taux d'annulation, note moyenne
- Badge de statut sur chaque campagne : `Brouillon`, `En attente`, `Active`, `Objectif atteint`, `Réussie`, `Échouée`, `Expirée`, `Suspendue`

---

## 7. Back-office admin (`/<ADMIN_URL_PATH>/`)

### 7.1 Sidebar (fixe, bleu nuit)
- Logo « REDUX Admin »
- Navigation : **Dashboard**, **Utilisateurs**, **Commerçants**, **Boutiques**, **Produits**, **Campagnes**, **Commandes**, **Paiements**, **Demandes**, **Propositions**, **Réclamations**, **Avis**, **Pays**, **Catégories**, **Paramètres**, **Logs**

### 7.2 Cartes statistiques
- Utilisateurs, commerçants, campagnes, commandes, volume transactionnel, commissions, campagnes réussies/échouées, taux de conversion
- Graphiques : inscriptions, campagnes, volume par pays, commissions dans le temps

### 7.3 Files de modération
- Commerçants à vérifier (`PENDING`) avec accès protégé aux documents
- Campagnes `PENDING_APPROVAL` avec aperçu : Approuver / Refuser / Demander modification
- Réclamations ouvertes, avis signalés

### 7.4 Gestion des pays, devises et paramètres
- Pays (nom, code, indicatif, devise, actif), devises, moyens de paiement actifs, règles de commission
- Toute modification sensible est journalisée dans `AuditLog`

---

## 8. Composants transverses

- **Boutons** : coins arrondis (`border-radius: 12px`), taille tactile minimale 44 px de haut, état pressé visible
- **Cartes** : coins arrondis (`16px`), ombre douce (`0 4px 20px rgba(0,0,0,0.06)`)
- **Badges de statut** : pastille colorée + texte court, cohérents entre tous les espaces
- **Montants** : toujours en gras, formatés selon le pays et la devise de la campagne
- **Skeleton loaders** sur les listes
- **Toasts** de confirmation (participation enregistrée, lien copié, paiement confirmé)
- **États vides** utiles (« Aucune campagne pour l'instant — explorer les offres »)

---

## 9. Performance mobile et PWA

- Images optimisées (WebP, tailles adaptées, `loading="lazy"`), pas d'image lourde inutile
- CSS et JS légers, peu de bibliothèques ; polices limitées
- Pages publiques rendues côté serveur (rapides, indexables), JavaScript en amélioration progressive
- PWA-ready : `manifest.json`, `service-worker.js`, page hors ligne (`offline.html`)
- Pensée pour faible consommation de données : pagination, pas de vidéo en lecture automatique
- Interface tactile : zones de clic larges, espacements généreux, navigation à une main

---

## 10. Transparence et ton

L'interface doit toujours afficher clairement : prix normal, prix actuel, paliers, conditions, date de fin, frais éventuels, règles de remboursement, frais de livraison, commission si pertinente, quantité disponible.

- Ton simple, chaleureux et rassurant sur le site public (« Achetez ensemble, payez moins »)
- Ton fonctionnel et précis dans les espaces acheteur/commerçant (messages d'erreur explicites)
- Ton neutre et factuel dans le back-office
- **Interdits** : faux compteurs, fausses participations, fausses urgences, minuteurs factices, promesses de prix non garanties par les règles de la campagne

---

## 11. Internationalisation et accessibilité

- Tous les textes passent par le système de traduction (français d'abord, anglais préparé pour le Ghana et le Nigeria)
- Formats de prix, dates et téléphones dépendants du pays
- Pas de texte incrusté dans les images
- Contrastes AA, libellés de formulaires explicites, focus visible, textes alternatifs sur les images
