@router.get("/scopes")
def get_shopify_scopes(store_id: str):
    """
    Vérifie les permissions Shopify réellement accordées
    au token de la boutique.
    """

    db = SessionLocal()

    try:
        store = (
            db.query(Store)
            .filter(Store.id == store_id)
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
            for scope in data.get("access_scopes", [])
        ]

        return {
            "success": True,
            "shop": store.shopify_domain,
            "scopes": scopes,
            "has_read_orders": "read_orders" in scopes,
            "has_read_customers": "read_customers" in scopes,
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