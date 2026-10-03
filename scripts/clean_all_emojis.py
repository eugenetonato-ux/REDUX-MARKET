import os
import re

REPLACEMENTS = {
    # Partials and badges
    "📦": "",
    "🔔": "",
    "⭐": "★",
    "★": "",
    "👤": "",
    "🏪": "",
    "🛡️": "",
    "🛡": "",
    "📍": "",
    "💳": "",
    "🔍": "",
    "✓": "",
    "✕": "",
    "🚀": "",
    "⚡": "",
    "🔥": "",
    "🏷️": "",
    "🏷": "",
    "🎉": "",
    "🔒": "",
    "⏳": "",
    "🚚": "",
    "💰": "",
    "📊": "",
    "📈": "",
    "🛍️": "",
    "🛍": "",
    "⚙️": "",
    "⚙": "",
    "🎯": "",
    "💡": "",
    "👥": "",
    "🎁": "",
    "❓": "",
    "🔄": "",
    "📡": "",
    "📞": "",
    "💼": "",
    "➕": "+",
    "🟢": "",
    "⛔": "",
    "🏆": "",
    "📱": "",
    "📲": "",
    "💬": "",
    "📢": "",
    "📋": "",
    "🛒": "",
    "🤝": "",
    "📜": "",
}

# We can perform specific context-aware cleanup so markup stays beautiful and doesn't leave empty awkward spans
SPECIFIC_FIXES = {
    "templates/campaigns/campaign_list.html": [
        ('<div style="font-size: 3.5rem; margin-bottom: 1rem;">🔍</div>', '<div style="margin-bottom: 1rem; color: var(--text-muted);"><svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg></div>'),
    ],
    "templates/pages/explorer.html": [
        ('🔍 Explorer les Offres', 'Explorer les Offres'),
        ('🔍 Aucun résultat', 'Aucun résultat'),
    ],
    "templates/dashboard/notifications.html": [
        ('<div style="font-size: 2.5rem; margin-bottom: 1rem;">🔔</div>', '<div style="margin-bottom: 1rem; color: var(--text-muted);"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h24s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg></div>'),
    ],
    "templates/dashboard/orders.html": [
        ('<div style="font-size: 3rem; margin-bottom: 0.75rem;">📦</div>', '<div style="margin-bottom: 0.75rem; color: var(--text-muted);"><svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg></div>'),
        ('⭐ Avis', 'Donner un avis'),
    ],
    "templates/checkout/order_detail.html": [
        ('⭐ Votre avis vérifié', 'Votre avis vérifié'),
        ('⭐ Laisser un avis vérifié', 'Laisser un avis vérifié'),
        ('💳 Procéder au paiement sécurisé', 'Procéder au paiement sécurisé'),
        ('📍 {{ order.campaign.product.store.city', '{{ order.campaign.product.store.city'),
    ],
    "templates/pages/categories.html": [
        ('<div style="font-size: 2rem; margin-bottom: 0.5rem;">🏷️</div>', '<div style="color: var(--primary); margin-bottom: 0.5rem;"><svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"></path><line x1="7" y1="7" x2="7.01" y2="7"></line></svg></div>'),
    ],
    "templates/pages/category_detail.html": [
        ('<div style="font-size: 3rem; margin-bottom: 0.75rem;">📦</div>', '<div style="margin-bottom: 0.75rem; color: var(--text-muted);"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg></div>'),
    ],
    "templates/disputes/dispute_form.html": [
        ('🛡️ Protection Acheteur REDUX', 'Protection Acheteur REDUX'),
    ],
    "templates/disputes/dispute_list.html": [
        ('🛡️ Protection Acheteur REDUX', 'Protection Acheteur REDUX'),
    ],
    "templates/merchant/nav_tabs.html": [
        ('📦 Produits', 'Produits'),
        ('🚀 Campagnes', 'Campagnes'),
        ('📋 Commandes Clients', 'Commandes Clients'),
        ('💰 Revenus & Séquestre', 'Revenus & Séquestre'),
        ('📈 Statistiques', 'Statistiques'),
        ('🏪 Ma Boutique', 'Ma Boutique'),
        ('🛡️ Vérification KYC', 'Vérification KYC'),
        ('📊 Paramètres', 'Paramètres'),
    ],
    "templates/merchant/orders.html": [
        ('📋 Commandes', 'Commandes'),
    ],
    "templates/merchant/products.html": [
        ('📦 Catalogue Produits', 'Catalogue Produits'),
    ],
    "templates/merchant/campaigns.html": [
        ('🚀 Campagnes à Paliers', 'Campagnes à Paliers'),
    ],
    "templates/merchant/dashboard.html": [
        ('🏪 Tableau de bord Marchand', 'Tableau de bord Marchand'),
        ('✓ Vérifiée', 'Vérifiée'),
    ],
    "templates/merchant/order_detail.html": [
        ('📍 Destination :', 'Destination :'),
        ('🚚 Expédition', 'Expédition'),
        ('📜 Historique', 'Historique'),
        ('🛍️ Articles commandés', 'Articles commandés'),
    ],
    "templates/merchant/campaign_form.html": [
        ('🚀 Lancer une Campagne à Paliers', 'Lancer une Campagne à Paliers'),
        ('✕ Supprimer', 'Supprimer'),
    ],
    "templates/merchant/revenue.html": [
        ('✓ Retrait', 'Retrait'),
    ],
    "templates/merchant/settings.html": [
        ('✓ Enregistré', 'Enregistré'),
    ],
    "templates/merchant/statistics.html": [
        ('★ Note moyenne :', 'Note moyenne :'),
        ('💡 Optimisation', 'Optimisation'),
    ],
    "templates/catalog/product_detail.html": [
        ('📍 {{ product.store.city', '{{ product.store.city'),
        ('📦 En stock', 'En stock'),
        ('<div style="font-size: 3rem; margin-bottom: 0.75rem;">📦</div>', '<div style="margin-bottom: 0.75rem; color: var(--text-muted);"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg></div>'),
    ],
    "templates/catalog/product_list.html": [
        ('<div style="font-size: 3rem; margin-bottom: 0.75rem;">📦</div>', '<div style="margin-bottom: 0.75rem; color: var(--text-muted);"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg></div>'),
    ],
    "templates/stores/store_detail.html": [
        ('📍 {{ store.city', '{{ store.city'),
        ('📞 Contact :', 'Contact :'),
    ],
    "templates/stores/store_list.html": [
        ('📍 {{ store.city', '{{ store.city'),
        ('🛍️ {{ store.products', '{{ store.products'),
    ],
    "templates/checkout/checkout.html": [
        ('🎉 Félicitations', 'Félicitations'),
    ],
    "templates/checkout/payment.html": [
        ('📱 Mobile Money', 'Mobile Money'),
        ('💳 Carte Bancaire', 'Carte Bancaire'),
        ('📲 Paiement direct', 'Paiement direct'),
        ('🔒 Sécurisé', 'Sécurisé'),
        ('✓ Confirmé', 'Confirmé'),
    ],
    "templates/checkout/payment_pending.html": [
        ('⏳ Traitement en cours', 'Traitement en cours'),
        ('⚙️ Synchronisation', 'Synchronisation'),
    ],
    "templates/checkout/payment_failed.html": [
        ('✕ Échec du paiement', 'Échec du paiement'),
    ],
    "templates/checkout/payment_success.html": [
        ('✓ Paiement Réussi', 'Paiement Réussi'),
    ],
    "templates/dashboard/index.html": [
        ('🎁 Avantages', 'Avantages'),
        ('👥 Parrainage', 'Parrainage'),
        ('📦 Commandes', 'Commandes'),
        ('🛍️ Achats', 'Achats'),
        ('💰 Économies', 'Économies'),
    ],
    "templates/dashboard/campaigns.html": [
        ('📦 Campagnes', 'Campagnes'),
        ('🛍️ Produits', 'Produits'),
    ],
    "templates/reviews/review_form.html": [
        ('🛍️ Avis sur le produit', 'Avis sur le produit'),
    ],
    "templates/base/base_merchant.html": [
        ('🎯 Objectifs', 'Objectifs'),
        ('🏪 Boutique', 'Boutique'),
        ('🛡️ Sécurité', 'Sécurité'),
        ('📊 Ventes', 'Ventes'),
        ('📦 Catalogue', 'Catalogue'),
        ('🛍️ Commandes', 'Commandes'),
        ('⚙️ Réglages', 'Réglages'),
    ],
    "templates/campaigns/campaign_detail.html": [
        ('📦 Expédié par', 'Expédié par'),
        ('✓ En stock', 'En stock'),
        ('🎉 Palier atteint', 'Palier atteint'),
        ('🤝 Groupe solidaire', 'Groupe solidaire'),
        ('🛒 Commander', 'Commander'),
        ('🛍️ Offre', 'Offre'),
        ('⚡ Express', 'Express'),
        ('🛡️ Garantie Séquestre', 'Garantie Séquestre'),
        ('🔒 Paiement Sécurisé', 'Paiement Sécurisé'),
    ],
    "templates/pages/how_it_works.html": [
        ('🔄 Processus', 'Processus'),
        ('✓ Garanti', 'Garanti'),
        ('🛒 Panier', 'Panier'),
        ('🛡️ Séquestre', 'Séquestre'),
    ],
    "templates/pages/help.html": [
        ('❓ Aide', 'Aide'),
        ('❓ FAQ', 'FAQ'),
    ],
    "templates/pages/offline.html": [
        ('🔄 Réessayer', 'Réessayer'),
        ('📡 Hors ligne', 'Hors ligne'),
    ],
    "templates/purchase_requests/request_detail.html": [
        ('💼 Proposition', 'Proposition'),
        ('✓ Validé', 'Validé'),
        ('⏳ En attente', 'En attente'),
    ],
    "templates/purchase_requests/request_list.html": [
        ('💬 Discussion', 'Discussion'),
        ('➕ Rejoindre', 'Rejoindre'),
        ('🟢 Ouverte', 'Ouverte'),
        ('🔄 Actualiser', 'Actualiser'),
        ('📢 Demande', 'Demande'),
    ],
    "templates/admin/index.html": [
        ('✓ Actif', 'Actif'),
        ('📊 Tableau', 'Tableau'),
    ],
}

def clean_file(filepath):
    rel_path = os.path.relpath(filepath).replace('\\', '/')
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    # Apply specific targeted fixes if defined
    for target_path, pairs in SPECIFIC_FIXES.items():
        if rel_path == target_path or rel_path.endswith(target_path):
            for old_str, new_str in pairs:
                content = content.replace(old_str, new_str)

    # Replace any remaining emoji characters with empty or clean equivalent
    for emo, rep in REPLACEMENTS.items():
        content = content.replace(emo, rep)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Cleaned emojis in: {rel_path}")

def run():
    for root, dirs, files in os.walk('templates'):
        for file in files:
            if file.endswith('.html'):
                clean_file(os.path.join(root, file))

if __name__ == '__main__':
    run()
