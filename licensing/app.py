"""Service de vente Opsora : paiement Stripe -> génération + envoi de la licence.

⚠️ CE SERVICE DÉTIENT LA CLÉ PRIVÉE DE L'ÉDITEUR. Il doit être déployé SÉPARÉMENT
du produit, sur un serveur privé — jamais dans l'image publique Opsora.

Flux :
  1. Le site vitrine appelle POST /checkout {plan, email}
  2a. Stripe configuré -> crée une session Checkout, renvoie {url} ; le client paie
  2b. Sinon (mode démo) -> génère la licence immédiatement et la renvoie
  3. POST /webhook (Stripe) sur paiement réussi -> génère la licence signée,
     l'enregistre et l'envoie par e-mail
  4. GET /license/{session_id} -> la page de succès récupère la clé

Signature Ed25519 identique au produit : la clé s'active telle quelle dans Opsora.
"""
from __future__ import annotations

import base64
import json
import os
import smtplib
import sqlite3
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr

# ------- Config (variables d'environnement) -------
PLANS = {
    "professional": {"label": "Opsora Professional", "amount_eur": 29},
    "business": {"label": "Opsora Business", "amount_eur": 89},
    "enterprise": {"label": "Opsora Enterprise", "amount_eur": 0},  # sur devis, non vendu ici
}
PRIVATE_KEY_FILE = os.getenv("VENDOR_PRIVATE_KEY_FILE", "vendor_private.key")
LICENSE_MONTHS = int(os.getenv("LICENSE_MONTHS", "12"))       # durée de la licence émise
SITE_URL = os.getenv("SITE_URL", "http://localhost:8080")     # site vitrine (retour)
SELF_URL = os.getenv("SELF_URL", "http://localhost:8090")     # ce service
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "licences@opsora.io")
DB_PATH = os.getenv("ORDERS_DB", "orders.db")

app = FastAPI(title="Opsora Licensing")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ------- Base des commandes (SQLite, léger) -------
def _db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS orders (
        session_id TEXT PRIMARY KEY, email TEXT, plan TEXT, license_key TEXT,
        created_at TEXT, paid INTEGER DEFAULT 0)""")
    return con


# ------- Génération de licence (Ed25519, comme le produit) -------
def _sign_license(plan: str, email: str) -> str:
    key = serialization.load_pem_private_key(Path(PRIVATE_KEY_FILE).read_bytes(), password=None)
    payload = {
        "plan": plan,
        "customer": email,
        "features": [],  # les features découlent du plan côté produit
        "expires": (date.today() + timedelta(days=LICENSE_MONTHS * 31)).isoformat(),
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    sig = key.sign(raw).hex()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=") + "." + sig


def _email_license(to: str, plan: str, license_key: str) -> None:
    if not SMTP_HOST:
        return
    body = (
        f"Bonjour,\n\nMerci pour votre achat d'Opsora {plan.capitalize()} !\n\n"
        "Votre clé de licence :\n\n"
        f"LICENSE_KEY={license_key}\n\n"
        "Activation : collez cette ligne dans le fichier .env de votre instance Opsora, puis :\n"
        "  docker compose up -d backend worker scheduler && docker compose restart nginx\n\n"
        "Vérifiez ensuite dans la page Hosts que votre plan est actif.\n\n"
        "L'équipe Opsora"
    )
    msg = MIMEText(body)
    msg["Subject"] = f"Votre licence Opsora {plan.capitalize()}"
    msg["From"] = SMTP_FROM
    msg["To"] = to
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as s:
        s.starttls()
        if SMTP_USER:
            s.login(SMTP_USER, SMTP_PASSWORD)
        s.send_message(msg)


def _fulfill(session_id: str, email: str, plan: str) -> str:
    """Génère la licence, l'enregistre, l'envoie. Idempotent."""
    con = _db()
    row = con.execute("SELECT license_key FROM orders WHERE session_id=?", (session_id,)).fetchone()
    if row and row[0]:
        con.close()
        return row[0]
    key = _sign_license(plan, email)
    con.execute(
        "INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,1)",
        (session_id, email, plan, key, datetime.utcnow().isoformat()),
    )
    con.commit()
    con.close()
    try:
        _email_license(email, plan, key)
    except Exception as exc:  # noqa: BLE001
        print(f"[warn] envoi e-mail échoué : {exc}")
    return key


# ------- API -------
class CheckoutIn(BaseModel):
    plan: str
    email: EmailStr


@app.get("/health")
def health():
    return {"ok": True, "stripe": bool(STRIPE_SECRET_KEY), "private_key": Path(PRIVATE_KEY_FILE).exists()}


@app.post("/checkout")
def checkout(payload: CheckoutIn):
    if payload.plan not in ("professional", "business"):
        raise HTTPException(400, "Plan non vendable en ligne (Enterprise = nous contacter)")
    if not Path(PRIVATE_KEY_FILE).exists():
        raise HTTPException(500, "Clé privée éditeur absente sur le serveur de vente")

    # --- Mode démo (pas de Stripe) : licence générée immédiatement ---
    if not STRIPE_SECRET_KEY:
        import uuid
        sid = "demo_" + uuid.uuid4().hex
        key = _fulfill(sid, payload.email, payload.plan)
        return {"license_key": key, "demo": True}

    # --- Stripe Checkout ---
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    plan = PLANS[payload.plan]
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer_email=payload.email,
        line_items=[{
            "price_data": {
                "currency": "eur",
                "recurring": {"interval": "month"},
                "product_data": {"name": plan["label"]},
                "unit_amount": plan["amount_eur"] * 100,
            },
            "quantity": 1,
        }],
        metadata={"plan": payload.plan, "email": payload.email},
        success_url=f"{SELF_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{SITE_URL}/#pricing",
    )
    return {"url": session.url}


@app.post("/webhook")
async def webhook(request: Request):
    """Webhook Stripe : génère la licence au paiement confirmé."""
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Signature webhook invalide : {exc}")

    if event["type"] == "checkout.session.completed":
        s = event["data"]["object"]
        meta = s.get("metadata", {})
        _fulfill(s["id"], meta.get("email") or s.get("customer_email"), meta.get("plan", "professional"))
    return {"received": True}


@app.get("/license/{session_id}")
def get_license(session_id: str):
    con = _db()
    row = con.execute("SELECT license_key, plan FROM orders WHERE session_id=? AND paid=1", (session_id,)).fetchone()
    con.close()
    if not row:
        raise HTTPException(404, "Licence non prête (paiement en cours de confirmation)")
    return {"license_key": row[0], "plan": row[1]}


@app.get("/success", response_class=HTMLResponse)
def success(session_id: str = ""):
    """Page de confirmation après paiement : affiche la clé de licence."""
    return f"""<!DOCTYPE html><html lang=fr><head><meta charset=utf-8>
<title>Merci — Opsora</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-[#0A0F1C] text-slate-200 font-sans min-h-screen flex items-center justify-center p-6">
<div class="max-w-lg w-full rounded-2xl border border-slate-800 bg-slate-900/60 p-8 text-center">
  <div class="text-5xl">🎉</div>
  <h1 class="mt-4 text-2xl font-bold">Merci pour votre achat !</h1>
  <p class="mt-2 text-slate-400 text-sm">Votre clé de licence Opsora — également envoyée par e-mail.</p>
  <pre id="k" class="mt-5 overflow-x-auto rounded-lg bg-slate-800 p-4 text-left text-xs text-sky-300">Chargement…</pre>
  <p class="mt-4 text-xs text-slate-500">Collez <code>LICENSE_KEY=…</code> dans votre .env, puis redémarrez Opsora.</p>
  <a href="{SITE_URL}" class="mt-6 inline-block rounded-lg bg-gradient-to-r from-sky-400 to-violet-500 px-5 py-2.5 text-sm font-semibold text-white">Retour au site</a>
</div>
<script>
  fetch("{SELF_URL}/license/{session_id}").then(r=>r.json()).then(d=>{{
    document.getElementById("k").textContent = d.license_key ? "LICENSE_KEY="+d.license_key : "Licence en cours de préparation, vérifiez vos e-mails.";
  }}).catch(()=>document.getElementById("k").textContent="Vérifiez vos e-mails pour la clé.");
</script></body></html>"""
