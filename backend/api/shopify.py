import os
import secrets
import hmac
import hashlib
import base64
import json
import time
import requests

from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException

from backend.database.database import SessionLocal
from backend.models.store import Store


router = APIRouter(
    prefix="/shopify",
    tags=["Shopify"]
)


SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
SHOPIFY_SCOPES = os.getenv("SHOPIFY_SCOPES", "read_orders")
SHOPIFY_REDIRECT_URI = os.getenv("SHOPIFY_REDIRECT_URI")


def create_state(user_id: str) -> str:
    data = {
        "user_id": user_id,
        "nonce": secrets.token_urlsafe(32),
        "timestamp": int(time.time()),
    }

    payload = base64.urlsafe_b64encode(
        json.dumps(
            data,
            separators=(",", ":")
        ).encode()
    ).decode().rstrip("=")

    signature = hmac.new(
        SHOPIFY_API_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{payload}.{signature}"


def verify_state(state: str) -> str:
    try:
        if not state:
            raise ValueError("state manquant")

        parts = state.split(".", 1)

        if len(parts) != 2:
            raise ValueError("state invalide")

        payload, signature = parts

        expected_signature = hmac.new(
            SHOPIFY_API_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            signature,
            expected_signature
        ):
            raise ValueError("signature invalide")

        padding = "=" * (-len(payload) % 4)

        decoded = base64.urlsafe_b64decode(
            (payload + padding).encode()
        )

        data = json.loads(decoded.decode())

        timestamp = data.get("timestamp")

        if not timestamp:
            raise ValueError("timestamp manquant")

        # State valable pendant 10 minutes
        if time.time() - int(timestamp) > 600:
            raise ValueError("state expiré")

        user_id = data.get("user_id")

        if not user_id:
            raise ValueError("user_id manquant")

        return user_id

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid Shopify state"
        )


@router.get("/install")
def install(
    shop: str,
    user_id: str
):

    if not SHOPIFY_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="SHOPIFY_API_KEY manquante"
        )

    if not SHOPIFY_API_SECRET:
        raise HTTPException(
            status_code=500,
            detail="SHOPIFY_API_SECRET manquante"
        )

    if not SHOPIFY_REDIRECT_URI:
        raise HTTPException(
            status_code=500,
            detail="SHOPIFY_REDIRECT_URI manquante"
        )

    shop = shop.strip().lower()

    if shop.startswith("https://"):
        shop = shop.replace("https://", "", 1)

    if shop.startswith("http://"):
        shop = shop.replace("http://", "", 1)

    shop = shop.rstrip("/")

    if not shop.endswith(".myshopify.com"):
        raise HTTPException(
            status_code=400,
            detail="Utilise le domaine xxx.myshopify.com"
        )

    state = create_state(user_id)

    params = {
        "client_id": SHOPIFY_API_KEY,
        "scope": SHOPIFY_SCOPES,
        "redirect_uri": SHOPIFY_REDIRECT_URI,
        "state": state,
    }

    install_url = (
        f"https://{shop}/admin/oauth/authorize?"
        + urlencode(params)
    )

    return {
        "install_url": install_url
    }


@router.get("/callback")
def callback(
    shop: str,
    code: str,
    state: str
):

    if not SHOPIFY_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="SHOPIFY_API_KEY manquante"
        )

    if not SHOPIFY_API_SECRET:
        raise HTTPException(
            status_code=500,
            detail="SHOPIFY_API_SECRET manquante"
        )

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Code Shopify manquant"
        )

    user_id = verify_state(state)

    shop = shop.strip().lower()

    if shop.startswith("https://"):
        shop = shop.replace("https://", "", 1)

    if shop.startswith("http://"):
        shop = shop.replace("http://", "", 1)

    shop = shop.rstrip("/")

    if not shop.endswith(".myshopify.com"):
        raise HTTPException(
            status_code=400,
            detail="Domaine Shopify invalide"
        )

    response = requests.post(
        f"https://{shop}/admin/oauth/access_token",
        json={
            "client_id": SHOPIFY_API_KEY,
            "client_secret": SHOPIFY_API_SECRET,
            "code": code,
        },
        timeout=30,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail=f"Shopify OAuth error: {response.text}"
        )

    data = response.json()

    access_token = data.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Access token Shopify introuvable"
        )

    db = SessionLocal()

    try:
        store = (
            db.query(Store)
            .filter(
                Store.shopify_domain == shop
            )
            .first()
        )

        if store:
            store.access_token = access_token
            store.user_id = user_id
            store.is_active = True

        else:
            store = Store(
                user_id=user_id,
                shop_name=shop.replace(
                    ".myshopify.com",
                    ""
                ),
                shopify_domain=shop,
                access_token=access_token,
                is_active=True,
            )

            db.add(store)

        db.commit()
        db.refresh(store)

        return {
            "success": True,
            "message": "Boutique Shopify connectée avec succès",
            "store_id": str(store.id),
            "shop": store.shopify_domain,
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erreur sauvegarde boutique: {str(e)}"
        )

    finally:
        db.close()