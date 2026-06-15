"""Customer-facing revenue forecast.

This models the CUSTOMER brand's own revenue — the value AnyMind delivers —
not AnyMind's fees. Given the recommended products and the brand's current
revenue, it projects the brand's monthly revenue under a do-nothing baseline
and three adoption strategies, so the pitch can show the uplift each path
unlocks. Deterministic and transparent so the numbers are defensible.

Strategies:
  quick_win      : adopt the 1-2 highest-impact products, fast ramp.
  full_transform : adopt the full recommended package immediately.
  phased         : adopt the full package, gradual ramp over the horizon.
"""

from products import impact_for

MONTHS = 18


def _adoption(strategy: str, month: int, months: int) -> float:
    """Fraction of a product's impact realised by `month` (0..1)."""
    if strategy == "full_transform":
        ramp = 3          # ~3 months to full effect
    elif strategy == "quick_win":
        ramp = 2
    else:                 # phased
        ramp = max(6, months // 2)
    return min(1.0, (month + 1) / ramp)


def _products_for(strategy: str, products: list[str]) -> list[str]:
    ordered = sorted(products, key=lambda p: impact_for(p)["growth_boost"],
                     reverse=True)
    if strategy == "quick_win":
        return ordered[:2]
    return ordered


def _series(start_rev, organic_growth, products, strategy, months):
    rev, out = start_rev, []
    for m in range(months):
        boost = sum(impact_for(p)["growth_boost"] * _adoption(strategy, m, months)
                    for p in products)
        rev = rev * (1 + organic_growth + boost)
        out.append(round(rev))
    return out


def _baseline(start_rev, organic_growth, months):
    rev, out = start_rev, []
    for _ in range(months):
        rev = rev * (1 + organic_growth)
        out.append(round(rev))
    return out


STRATEGY_LABELS = {
    "quick_win": "Quick Win",
    "full_transform": "Full Transformation",
    "phased": "Phased Rollout",
}
STRATEGY_BLURB = {
    "quick_win": "Deploy the two highest-impact products first for fast, "
                 "visible results — lowest disruption, quickest proof.",
    "full_transform": "Adopt the full recommended package now for the steepest "
                      "growth curve — highest upside, more change to manage.",
    "phased": "Roll the full package out gradually — a balanced path that "
              "builds momentum while keeping the team's load manageable.",
}


def build_dashboard(pitch: dict, start_revenue: float = 800_000,
                    organic_growth: float = 0.02, months: int = MONTHS) -> dict:
    """Customer revenue forecast: baseline vs each adoption strategy."""
    products = pitch.get("recommended_package", {}).get("included_products", [])
    if not products:
        products = [m.get("product") for m in pitch.get("solution_mapping", [])
                    if m.get("product")]
    products = [p for p in products if p]

    base = _baseline(start_revenue, organic_growth, months)
    base_total = sum(base)

    strategies = []
    for key in ("quick_win", "full_transform", "phased"):
        ps = _products_for(key, products)
        series = _series(start_revenue, organic_growth, ps, key, months)
        total = sum(series)
        strategies.append({
            "strategy": key,
            "label": STRATEGY_LABELS[key],
            "blurb": STRATEGY_BLURB[key],
            "products_used": ps,
            "monthly_revenue": series,
            "total_revenue": total,
            "ending_mrr": series[-1],
            "uplift_vs_baseline": total - base_total,
            "uplift_pct": round((total - base_total) / base_total * 100, 1),
        })

    return {
        "brand": pitch.get("brand"),
        "products": products,
        "assumptions": {
            "start_monthly_revenue": start_revenue,
            "organic_monthly_growth": organic_growth,
            "horizon_months": months,
        },
        "baseline": {"monthly_revenue": base, "total_revenue": base_total,
                     "ending_mrr": base[-1]},
        "strategies": strategies,
        "recommended": max(strategies, key=lambda s: s["uplift_vs_baseline"])["strategy"],
    }