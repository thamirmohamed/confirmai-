import os
import secrets
import hmac
import hashlib
import base64
import json
import requests

from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException

from backend.database.database import SessionLocal
from backend.models.store import Store


router = APIRouter(prefix="/shopify", tags=["Shopify"])


SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")

SHOPIFY_SCOPES = os.getenv(
    "SHOPIFY_SCOPES",
    "read_orders,read_customers"
)

SHOPIFY_REDIRECT_URI = os.getenv(
    "SHOPIFY_REDIRECT_URI"
)

SHOPIFY_SHOP = "hkdhpg-fm.myshopify.com"


def create_state(user_id: str, shop: str) -> str:
    data = {
        "user_id": user_id,
        "shop": shop,
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


def verify_state(state: str):
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

        return data

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

    if not shop.endswith(".myshopify.com"):
        raise HTTPException(
            status_code=400,
            detail="Utilise le domaine xxx.myshopify.com"
        )

    if shop != SHOPIFY_SHOP:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Mauvaise boutique",
                "shop_recu": shop,
                "shop_attendu": SHOPIFY_SHOP
            }
        )

    state = create_state(
        user_id,
        shop
    )

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
        "success": True,
        "shop": shop,
        "scopes": SHOPIFY_SCOPES.split(","),
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

    state_data = verify_state(state)

    user_id = state_data["user_id"]
    expected_shop = state_data["shop"]

    shop = shop.strip().lower()

    if shop != expected_shop:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Shop différent entre install et callback",
                "shop_recu": shop,
                "shop_attendu": expected_shop
            }
        )

    if shop != SHOPIFY_SHOP:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Boutique Shopify non autorisée",
                "shop_recu": shop,
                "shop_attendu": SHOPIFY_SHOP
            }
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
            detail=response.text
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
                shop_name="CAPS WORLD",
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
            "shop_name": store.shop_name,
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erreur sauvegarde boutique: {str(e)}"
        )

    finally:
        db.close()


@router.get("/scopes")
def scopes(store_id: str):
    db = SessionLocal()

    try:
        store = (
            db.query(Store)
            .filter(
                Store.id == store_id
            )
            .first()
        )

        if not store:
            raise HTTPException(
                status_code=404,
                detail="Boutique introuvable"
            )

        return {
            "success": True,
            "shop": store.shopify_domain,
            "scopes": [
                scope.strip()
                for scope in SHOPIFY_SCOPES.split(",")
            ],
            "has_read_orders": (
                "read_orders"
                in SHOPIFY_SCOPES.split(",")
            ),
            "has_read_customers": (
                "read_customers"
                in SHOPIFY_SCOPES.split(",")
            ),
        }

    finally:
        db.close()


@router.get("/orders")
def get_orders(store_id: str):
    db = SessionLocal()

    try:
        store = (
            db.query(Store)
            .filter(
                Store.id == store_id
            )
            .first()
        )

        if not store:
            raise HTTPException(
                status_code=404,
                detail="Boutique introuvable"
            )

        response = requests.get(
            f"https://{store.shopify_domain}/admin/api/2026-07/orders.json",
            headers={
                "X-Shopify-Access-Token": store.access_token
            },
            params={
                "status": "any",
                "limit": 50,
            },
            timeout=30,
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response.text
            )

        data = response.json()

        return {
            "success": True,
            "shop": store.shopify_domain,
            "orders": data.get("orders", [])
        }

    finally:
        db.close()