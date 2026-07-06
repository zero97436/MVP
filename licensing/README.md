# Opsora — Service de vente de licences

⚠️ **Ce service détient la clé privée de l'éditeur.** Il se déploie **séparément**
du produit, sur un serveur privé. Ne jamais l'inclure dans l'image publique Opsora
ni committer `vendor_private.key`.

## Rôle
Paiement Stripe → génération d'une **clé de licence signée Ed25519** (identique à
celle attendue par Opsora) → envoi par e-mail + page de confirmation.

## Démarrage (mode démo, sans Stripe — pour tester le site)

```bash
cd licensing
python -m venv .venv && . .venv/bin/activate   # (Windows : .venv\Scripts\activate)
pip install -r requirements.txt

# Copier votre clé privée éditeur ici (générée par scripts/generate_license.py --init)
cp ../scripts/vendor_private.key .

uvicorn app:app --port 8090
```

Sans `STRIPE_SECRET_KEY`, le bouton « Choisir » du site génère la licence
**immédiatement** (utile pour tester la chaîne complète).

## Passage en production (Stripe réel)

Variables d'environnement :

| Variable | Rôle |
|---|---|
| `VENDOR_PRIVATE_KEY_FILE` | chemin de la clé privée éditeur (défaut `vendor_private.key`) |
| `STRIPE_SECRET_KEY` | clé secrète Stripe (`sk_live_…` ou `sk_test_…`) |
| `STRIPE_WEBHOOK_SECRET` | secret du endpoint webhook (`whsec_…`) |
| `SITE_URL` | URL du site vitrine (retour après paiement) |
| `SELF_URL` | URL publique de ce service |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `SMTP_FROM` | envoi de la clé par e-mail |
| `LICENSE_MONTHS` | durée de la licence émise (défaut 12) |

Chez Stripe : créer un **endpoint webhook** vers `SELF_URL/webhook` sur l'événement
`checkout.session.completed`, et coller son secret dans `STRIPE_WEBHOOK_SECRET`.

## Sécurité
- `vendor_private.key` : jamais dans git (déjà gitignoré), sauvegardé hors ligne.
- Ce service derrière HTTPS. Restreindre l'accès réseau au strict nécessaire.
- Le webhook Stripe est vérifié par signature (anti-falsification).
