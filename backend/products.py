"""AnyMind product catalogue — the fixed 'what we can sell' reference.

Keep this in sync with the real product suite. The analyzer is only allowed to
recommend products from this list, which keeps the pitch grounded.
"""

ANYMIND_PRODUCTS = {
    "AnyTag": "Influencer marketing platform: discover, activate, manage, "
              "track and attribute influencer campaigns across APAC.",
    "AnyCreator": "Creator network and tools for influencers to monetise and "
                  "collaborate with brands.",
    "AnyDigital": "Digital advertising platform for running and optimising "
                  "paid media campaigns.",
    "AnyManager": "Publisher / media monetisation and UX-improvement platform "
                  "(ad monetisation, header bidding, analytics).",
    "AnyX": "E-commerce management: run and centralise sales across "
            "marketplaces and D2C storefronts.",
    "AnyShop": "E-commerce storefront platform for launching D2C brands.",
    "AnyLogi": "Logistics management: inventory, warehousing and fulfilment.",
    "AnyChat": "Conversational commerce / customer engagement across chat "
               "channels.",
    "AnyFactory": "Cloud manufacturing to produce own-brand / private-label "
                  "products.",
}


def catalogue_text() -> str:
    """Render the catalogue as a bullet list for prompts."""
    return "\n".join(f"- {name}: {desc}"
                     for name, desc in ANYMIND_PRODUCTS.items())


# ---------------------------------------------------------------------------
# PRICING MODEL (assumptions — edit to match real commercials).
# Each product earns AnyMind two ways:
#   monthly_base : fixed SaaS / service fee per month (USD)
#   take_rate    : % of the brand's attributable monthly GMV it earns on top
# These drive the revenue dashboard. They are explicit and configurable so the
# projections stay transparent and defensible.
# ---------------------------------------------------------------------------
PRODUCT_PRICING = {
    "AnyTag":     {"monthly_base": 2500, "take_rate": 0.000},
    "AnyCreator": {"monthly_base": 1500, "take_rate": 0.000},
    "AnyDigital": {"monthly_base": 2000, "take_rate": 0.030},
    "AnyManager": {"monthly_base": 1000, "take_rate": 0.150},
    "AnyX":       {"monthly_base": 3000, "take_rate": 0.020},
    "AnyShop":    {"monthly_base": 1500, "take_rate": 0.015},
    "AnyLogi":    {"monthly_base": 2000, "take_rate": 0.040},
    "AnyChat":    {"monthly_base": 1200, "take_rate": 0.010},
    "AnyFactory": {"monthly_base": 2500, "take_rate": 0.050},
}

# Fallback used if the model recommends a product not in the table.
DEFAULT_PRICING = {"monthly_base": 2000, "take_rate": 0.02}


def pricing_for(product: str) -> dict:
    return PRODUCT_PRICING.get(product, DEFAULT_PRICING)