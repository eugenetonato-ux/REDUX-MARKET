# REDUX — Entity Relationship Diagram (ERD)

Ce document décrit le modèle de données relationnel de la plateforme **REDUX**.

```mermaid
erDiagram
    COUNTRY ||--o{ CURRENCY : "utilise devise par defaut"
    COUNTRY ||--o{ USER : "pays de residence"
    COUNTRY ||--o{ STORE : "pays d implantation"
    COUNTRY ||--o{ DELIVERY_METHOD : "disponible dans"
    COUNTRY ||--o{ COMMISSION_RULE : "applicable a"

    USER ||--o| BUYER_PROFILE : "possede"
    USER ||--o| MERCHANT_PROFILE : "peut gerer"
    USER ||--o{ CAMPAIGN : "cree en tant que lead buyer"
    USER ||--o{ CAMPAIGN_PARTICIPANT : "participe a"
    USER ||--o{ ORDER : "passe"
    USER ||--o{ REVIEW : "redige"
    USER ||--o{ DISPUTE : "ouvre"
    USER ||--o{ NOTIFICATION : "recoit"
    USER ||--o| NOTIFICATION_PREFERENCE : "definit"

    MERCHANT_PROFILE ||--o{ MERCHANT_VERIFICATION : "fournit"
    MERCHANT_PROFILE ||--o{ STORE : "exploite"
    MERCHANT_PROFILE ||--o{ CAMPAIGN : "propose"
    MERCHANT_PROFILE ||--o{ SELLER_PROPOSAL : "soumet"

    STORE ||--o{ PRODUCT : "vend"
    STORE ||--o{ DELIVERY_METHOD : "propose"
    CATEGORY ||--o{ CATEGORY : "parent de"
    CATEGORY ||--o{ PRODUCT : "classifie"
    PRODUCT ||--o{ PRODUCT_IMAGE : "illustre par"
    PRODUCT ||--o{ PRODUCT_VARIANT : "decline en"
    PRODUCT ||--o{ CAMPAIGN : "fait l objet de"

    CAMPAIGN ||--o{ PRICE_TIER : "definit les paliers de prix"
    CAMPAIGN ||--o{ CAMPAIGN_PARTICIPANT : "regroupe"
    CAMPAIGN_PARTICIPANT ||--o| ORDER : "se transforme en commande"

    ORDER ||--o{ ORDER_ITEM : "contient"
    ORDER ||--o{ ORDER_STATUS_HISTORY : "trace son statut"
    ORDER ||--o{ PAYMENT : "regle par"
    ORDER ||--o| SHIPMENT : "expedie via"
    ORDER ||--o| REVIEW : "evaluee par"
    ORDER ||--o{ DISPUTE : "peut faire l objet de"
    ORDER ||--o{ PLATFORM_TRANSACTION : "genere une commission"

    PAYMENT_PROVIDER ||--o{ PAYMENT : "traite"
    PAYMENT_PROVIDER ||--o{ WEBHOOK_EVENT : "notifie via"
    PAYMENT ||--o{ PAYMENT_TRANSACTION : "se compose de"
    PAYMENT ||--o{ REFUND : "peut etre rembourse"

    PURCHASE_REQUEST ||--o{ PURCHASE_REQUEST_PARTICIPANT : "rejoint par"
    PURCHASE_REQUEST ||--o{ SELLER_PROPOSAL : "recoit des offres de"
    DISPUTE ||--o{ DISPUTE_MESSAGE : "echanges"
```

## Règles architecturales strictes
1. **User → CampaignParticipant → Order → Payment** : une participation n'est pas une commande.
2. **Double surface critique** :
   - Paiement validé uniquement côté serveur par webhook signé (`WebhookEvent`, `PaymentTransaction`).
   - Rôle `ADMIN` non auto-attribuable.
3. **Multi-pays** : Devises et pays gérés dynamiquement (`Country`, `Currency`).
4. **Append-only** pour la comptabilité : `PlatformTransaction` et `AuditLog`.
