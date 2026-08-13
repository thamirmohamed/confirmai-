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
from backend.models.order import Order


router = APIRouter(
    prefix="/shopify",
    tags=["Shopify"]
)


SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET")

SHOPIFY_SCOPES = os.getenv(
    "SHOPIFY_SCOPES",
    "read_orders,read_customers"
)

SHOPIFY_REDIRECT_URI = os.getenv("SHOPIFY_REDIRECT_URI")

SHOPIFY_API_VERSION = "2026-07"


# ============================================================
# STATE
# ============================================================

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

        data = json.loads(
            decoded.decode()
        )

        timestamp = data.get("timestamp")

        if not timestamp:
            raise ValueError("timestamp manquant")

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


# ============================================================
# INSTALL
# ============================================================

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
        shop = shop.replace(
            "https://",
            "",
            1
        )

    if shop.startswith("http://"):
        shop = shop.replace(
            "http://",
            "",
            1
        )

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


# ============================================================
# CALLBACK
# ============================================================

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
        shop = shop.replace(
            "https://",
            "",
            1
        )

    if shop.startswith("http://"):
        shop = shop.replace(
            "http://",
            "",
            1
        )

    shop = shop.rstrip("/")

    if not shop.endswith(".myshopify.com"):
        raise HTTPException(
            status_code=400,
            detail="Domaine Shopify invalide"
        )

    # ========================================================
    # ECHANGE DU CODE CONTRE LE TOKEN SHOPIFY
    # ========================================================

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

    # ========================================================
    # DEBUG
    # ========================================================

    print("==========================================")
    print("SHOPIFY OAUTH CALLBACK")
    print("SHOP :", shop)
    print("USER ID :", user_id)
    print("SCOPES DEMANDES :", SHOPIFY_SCOPES)
    print("SCOPES RETOURNES PAR SHOPIFY :", data.get("scope"))
    print(
        "TOKEN RECU :",
        (
            access_token[:10] + "..." + access_token[-5:]
        )
        if access_token
        else "AUCUN TOKEN"
    )
    print(
        "TOKEN LENGTH :",
        len(access_token)
        if access_token
        else 0
    )
    print("==========================================")

    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="Access token Shopify introuvable"
        )

    # ========================================================
    # SAUVEGARDE DE LA BOUTIQUE
    # ========================================================

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


# ============================================================
# IMPORT COMMANDES
# ============================================================

@router.get("/orders/import")
def import_orders(store_id: str):

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

        if not store.access_token:

            raise HTTPException(
                status_code=400,
                detail="Cette boutique n'a pas de token Shopify"
            )

        shop = store.shopify_domain

        access_token = store.access_token

        url = (
            f"https://{shop}"
            f"/admin/api/{SHOPIFY_API_VERSION}"
            f"/graphql.json"
        )

        query = """
        query GetOrders($first: Int!, $after: String) {

            orders(
                first: $first,
                after: $after,
                sortKey: CREATED_AT,
                reverse: true
            ) {

                edges {

                    cursor

                    node {

                        id
                        name
                        createdAt

                        customer {
                            displayName
                            phone
                        }

                        totalPriceSet {
                            shopMoney {
                                amount
                                currencyCode
                            }
                        }

                        shippingAddress {
                            address1
                            city
                            phone
                        }

                        lineItems(first: 50) {

                            edges {

                                node {
                                    name
                                    quantity
                                }

                            }

                        }

                    }

                }

                pageInfo {
                    hasNextPage
                    endCursor
                }

            }

        }
        """

        imported = 0
        updated = 0
        after = None

        while True:

            response = requests.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "X-Shopify-Access-Token": access_token,
                },
                json={
                    "query": query,
                    "variables": {
                        "first": 50,
                        "after": after,
                    },
                },
                timeout=30,
            )

            if response.status_code != 200:

                raise HTTPException(
                    status_code=400,
                    detail=f"Shopify API error: {response.text}"
                )

            result = response.json()

            if result.get("errors"):

                raise HTTPException(
                    status_code=400,
                    detail={
                        "shopify_errors": result["errors"]
                    }
                )

            orders_data = (
                result
                .get("data", {})
                .get("orders", {})
            )

            edges = orders_data.get(
                "edges",
                []
            )

            for edge in edges:

                shopify_order = edge["node"]

                shopify_order_id = shopify_order["id"]

                customer = (
                    shopify_order.get("customer")
                    or {}
                )

                customer_name = (
                    customer.get("displayName")
                    or "Client Shopify"
                )

                phone = (
                    customer.get("phone")
                    or (
                        shopify_order
                        .get("shippingAddress")
                        or {}
                    ).get("phone")
                    or "Non renseigné"
                )

                shipping_address = (
                    shopify_order
                    .get("shippingAddress")
                    or {}
                )

                address = shipping_address.get(
                    "address1"
                )

                city = shipping_address.get(
                    "city"
                )

                money = (
                    shopify_order
                    .get("totalPriceSet", {})
                    .get("shopMoney", {})
                )

                amount = float(
                    money.get(
                        "amount",
                        0
                    )
                )

                currency = (
                    money.get("currencyCode")
                    or "MAD"
                )

                line_items = (
                    shopify_order
                    .get("lineItems", {})
                    .get("edges", [])
                )

                products = []

                for item_edge in line_items:

                    item = item_edge["node"]

                    name = item.get(
                        "name",
                        "Produit"
                    )

                    quantity = item.get(
                        "quantity",
                        1
                    )

                    products.append(
                        f"{name} x{quantity}"
                    )

                product = ", ".join(
                    products
                )

                if not product:
                    product = "Commande Shopify"

                existing_order = (
                    db.query(Order)
                    .filter(
                        Order.shopify_order_id
                        == shopify_order_id
                    )
                    .first()
                )

                if existing_order:

                    existing_order.customer_name = customer_name
                    existing_order.phone = phone
                    existing_order.product = product
                    existing_order.price = amount
                    existing_order.city = city
                    existing_order.address = address
                    existing_order.currency = currency

                    updated += 1

                else:

                    new_order = Order(
                        store_id=store.id,
                        customer_name=customer_name,
                        phone=phone,
                        product=product,
                        price=amount,
                        city=city,
                        address=address,
                        status="Pending",
                        shopify_order_id=shopify_order_id,
                        currency=currency,
                    )

                    db.add(new_order)

                    imported += 1

            page_info = orders_data.get(
                "pageInfo",
                {}
            )

            if not page_info.get(
                "hasNextPage"
            ):
                break

            after = page_info.get(
                "endCursor"
            )

        db.commit()

        return {
            "success": True,
            "message": "Import des commandes terminé",
            "shop": shop,
            "imported": imported,
            "updated": updated,
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Erreur import commandes: {str(e)}"
        )

    finally:

        db.close()


# ============================================================
# VERIFICATION DES SCOPES SHOPIFY
# ============================================================

@router.get("/scopes")
def get_shopify_scopes(store_id: str):

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

        if not store.access_token:

            raise HTTPException(
                status_code=400,
                detail="Access token Shopify manquant"
            )

        response = requests.get(
            f"https://{store.shopify_domain}/admin/oauth/access_scopes.json",
            headers={
                "X-Shopify-Access-Token": store.access_token,
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if response.status_code != 200:

            raise HTTPException(
                status_code=response.status_code,
                detail=response.text,
            )

        data = response.json()

        scopes = [
            scope.get("handle")
            for scope in data.get(
                "access_scopes",
                []
            )
        ]

        return {
            "success": True,
            "shop": store.shopify_domain,
            "scopes": scopes,
            "has_read_orders": (
                "read_orders" in scopes
            ),
            "has_read_customers": (
                "read_customers" in scopes
            ),
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Erreur vérification scopes: {str(e)}"
        )

    finally:

        db.close()