"""AnyMind product catalogue + customer-impact assumptions."""

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
# CUSTOMER IMPACT MODEL (assumptions — edit to match real benchmarks).
# For the CUSTOMER-facing forecast: how much each product can lift the brand's
# own revenue growth once adopted. `growth_boost` is the incremental monthly
# revenue growth rate the product drives at full adoption; `lever` names the
# mechanism for the pitch narrative. Deterministic + transparent on purpose.
# ---------------------------------------------------------------------------
PRODUCT_IMPACT = {
    "AnyTag":     {"growth_boost": 0.010, "lever": "influencer-driven demand"},
    "AnyCreator": {"growth_boost": 0.006, "lever": "creator content & reach"},
    "AnyDigital": {"growth_boost": 0.012, "lever": "scaled paid acquisition"},
    "AnyManager": {"growth_boost": 0.004, "lever": "media monetisation"},
    "AnyX":       {"growth_boost": 0.009, "lever": "marketplace conversion"},
    "AnyShop":    {"growth_boost": 0.007, "lever": "D2C storefront sales"},
    "AnyLogi":    {"growth_boost": 0.005, "lever": "recovered stockout sales"},
    "AnyChat":    {"growth_boost": 0.006, "lever": "chat-commerce conversion"},
    "AnyFactory": {"growth_boost": 0.008, "lever": "new product margin"},
}

DEFAULT_IMPACT = {"growth_boost": 0.006, "lever": "commerce enablement"}


def impact_for(product: str) -> dict:
    return PRODUCT_IMPACT.get(product, DEFAULT_IMPACT)