"""Revenue dashboard model — projects AnyMind's OWN revenue from a deal.

This is deliberately deterministic and transparent (no LLM guessing on money),
so the numbers are defensible in a pitch. Given the recommended products and a
few assumptions about the brand's GMV, it projects AnyMind's monthly revenue
over a horizon under three go-to-market strategies.

Strategies:
  land_expand    : start with the 1-2 highest-value products, add the rest over
                   time. Lower upfront, compounding.
  full_suite     : all recommended products live from month 1. Highest upfront.
  performance    : reduced base fees, higher take-rate. Revenue scales with the
                   brand's growth — lower early, higher if the brand grows.
"""

from products import pricing_for

MONTHS = 18


def _brand_gmv_curve(start_gmv: float, monthly_growth: float, months: int):
    """Brand's attributable monthly GMV, compounding."""
    return [start_gmv * ((1 + monthly_growth) ** m) for m in range(months)]


def _strategy_schedule(products: list[str], strategy: str, months: int):
    """Return, per month, the set of active products for a strategy."""
    # order products by standalone monthly value (base + nominal take) desc
    ordered = sorted(products, key=lambda p: pricing_for(p)["monthly_base"]
                     + pricing_for(p)["take_rate"] * 100000, reverse=True)
    schedule = []
    if strategy == "full_suite":
        for _ in range(months):
            schedule.append(list(ordered))
    elif strategy == "performance":
        # all products, but pricing is adjusted later
        for _ in range(months):
            schedule.append(list(ordered))
    else:  # land_expand
        # start with top 1-2, add one product roughly every 3 months
        for m in range(months):
            n = min(len(ordered), 2 + m // 3)
            schedule.append(ordered[:n])
    return schedule


def _monthly_revenue(active, gmv, strategy):
    total = 0.0
    for p in active:
        pr = pricing_for(p)
        base, take = pr["monthly_base"], pr["take_rate"]
        if strategy == "performance":
            base *= 0.5          # lower fixed fee
            take *= 2.0          # higher take-rate
        total += base + take * gmv
    return total


def project_strategy(products, start_gmv, monthly_growth, strategy, months=MONTHS):
    gmv_curve = _brand_gmv_curve(start_gmv, monthly_growth, months)
    schedule = _strategy_schedule(products, strategy, months)
    series = [round(_monthly_revenue(schedule[m], gmv_curve[m], strategy))
              for m in range(months)]
    return {
        "strategy": strategy,
        "monthly_revenue": series,
        "total_revenue": round(sum(series)),
        "ending_mrr": series[-1],
    }


STRATEGY_LABELS = {
    "land_expand": "Land & Expand",
    "full_suite": "Full Suite Now",
    "performance": "Performance Partnership",
}
STRATEGY_BLURB = {
    "land_expand": "Start with the highest-value products and expand the "
                   "footprint quarter by quarter. Lower upfront commitment, "
                   "compounding revenue.",
    "full_suite": "Deploy the full recommended package from day one. Highest "
                  "upfront revenue and fastest time-to-impact.",
    "performance": "Reduced fixed fees in exchange for a higher take-rate. "
                   "Revenue scales with the brand's growth — aligned upside.",
}


def build_dashboard(pitch: dict, start_gmv: float = 500_000,
                    monthly_growth: float = 0.04, months: int = MONTHS) -> dict:
    """Build the full revenue dashboard payload for all strategies."""
    products = pitch.get("recommended_package", {}).get("included_products", [])
    if not products:
        products = [m.get("product") for m in pitch.get("solution_mapping", [])
                    if m.get("product")]
    products = [p for p in products if p]

    strategies = []
    for key in ("land_expand", "full_suite", "performance"):
        proj = project_strategy(products, start_gmv, monthly_growth, key, months)
        proj["label"] = STRATEGY_LABELS[key]
        proj["blurb"] = STRATEGY_BLURB[key]
        strategies.append(proj)

    return {
        "brand": pitch.get("brand"),
        "products": products,
        "assumptions": {
            "start_attributable_gmv_monthly": start_gmv,
            "brand_monthly_growth": monthly_growth,
            "horizon_months": months,
        },
        "brand_gmv_curve": [round(v) for v in
                            _brand_gmv_curve(start_gmv, monthly_growth, months)],
        "strategies": strategies,
        "recommended": max(strategies, key=lambda s: s["total_revenue"])["strategy"],
    }