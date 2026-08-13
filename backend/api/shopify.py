import os
import secrets
import hmac
import hashlib
import base64
import json
import requests

from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from backend.database.database import SessionLocal
from backend.models.store import Store


router = APIRouter(prefix="/shopify", tags=["Shopify"])


SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")
SHOPIFY_SCOPES = os.getenv(
    "SHOPIFY_SCOPES",
    "read_orders"
)
SHOPIFY_REDIRECT_URI = os.getenv("SHOPIFY_REDIRECT_URI")


def create_state(user_id: str) -> str:
    """
    Crée un state signé contenant l'utilisateur.
    """

    data = {
        "user_id": user_id,
        "nonce": secrets.token_urlsafe(32),
    }

    payload = base64.urlsafe_b64encode(
        json.dumps(data).encode()
    ).decode()

    signature = hmac.new(
        SHOPIFY_API_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{payload}.{signature}"


def verify_state(state: str) -> str:
    """
    Vérifie le state et retourne le user_id.
    """

    try:
        payload, signature = state.split(".", 1)

        expected_signature = hmac.new(
            SHOPIFY_API_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            signature,
            expected_signature
        ):
            raise HTTPException(
                status_code=400,
                detail="Invalid Shopify state"
            )

        data = json.loads(
            base64.urlsafe_b64decode(
                payload.encode()
            )
        )

        return data["user_id"]

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
    """
    Démarre la connexion Shopify.
    """

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
    """
    Callback Shopify après installation.
    """

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

    user_id = verify_state(state)

    shop = shop.strip().lower()

    # Échange du code contre le token Shopify
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
            detail=response.text,
        )

    data = response.json()

    access_token = data.get("access_token")

    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Access token Shopify introuvable"
        )

    # Sauvegarde de la boutique
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
            "store_id": store.id,
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