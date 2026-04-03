from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote_plus

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

USER_DATA_DIR = "browser_profile"

STATUS_SCORES = {
    "POSSIBLY_IN_STOCK": 2,
    "UNKNOWN": 1,
    "OUT_OR_NOT_LISTED": 0,
    "BLOCKED": -1,
    "TIMEOUT": -1,
    "ERROR": -1,
}

CONFIDENCE_SCORES = {
    "high": 2,
    "medium": 1,
    "low": 0,
}


@dataclass(frozen=True)
class Retailer:
    name: str
    home_url: str
    search_url_template: str
    location_mode: str
    notes: str
    in_stock_selectors: List[str] = field(default_factory=list)
    out_of_stock_selectors: List[str] = field(default_factory=list)
    no_results_selectors: List[str] = field(default_factory=list)
    blocked_selectors: List[str] = field(default_factory=list)
    in_stock_phrases: List[str] = field(default_factory=list)
    out_of_stock_phrases: List[str] = field(default_factory=list)
    no_results_phrases: List[str] = field(default_factory=list)
    in_stock_containers: List[str] = field(default_factory=list)


def build_retailers() -> List[Retailer]:
    return [
        Retailer(
            name="Meijer",
            home_url="https://www.meijer.com/",
            search_url_template="https://www.meijer.com/search.html?query={query}",
            location_mode="profile",
            notes="Set your store/ZIP in the site UI first.",
            in_stock_selectors=["button:has-text('Add to Cart')"],
            no_results_phrases=["no results"],
            in_stock_containers=["main", "[data-testid='product-grid']", ".product-grid"],
        ),
        Retailer(
            name="Kroger",
            home_url="https://www.kroger.com/",
            search_url_template="https://www.kroger.com/search?query={query}",
            location_mode="profile",
            notes="Set your store/ZIP in the site UI first.",
            in_stock_selectors=["button:has-text('Add to Cart')"],
            no_results_phrases=["no results", "we couldn't find"],
            in_stock_containers=["main", "[data-testid='AutoGrid']", ".AutoGrid"],
        ),
        Retailer(
            name="Target",
            home_url="https://www.target.com/",
            search_url_template="https://www.target.com/s?searchTerm={query}",
            location_mode="profile",
            notes="Set your store/ZIP in the site UI first.",
            in_stock_selectors=["[data-test='addToCartButton']", "button:has-text('Add to cart')"],
            out_of_stock_selectors=["[data-test='productNotAvailable']"],
            no_results_phrases=["we found 0 results"],
            in_stock_containers=["main", "[data-test='@web/site-top-of-funnel/ProductCardWrapper']", "[data-test='product-details']"],
        ),
        Retailer(
            name="Walmart",
            home_url="https://www.walmart.com/",
            search_url_template="https://www.walmart.com/search?q={query}",
            location_mode="profile",
            notes="Set your store/ZIP in the site UI first.",
            in_stock_selectors=["button:has-text('Add to cart')"],
            out_of_stock_selectors=["text=Out of stock"],
            no_results_phrases=["no results"],
            in_stock_containers=["main", "[data-testid='item-stack']", "[data-testid='search-results']"],
        ),
        Retailer(
            name="Dollar General",
            home_url="https://www.dollargeneral.com/",
            search_url_template="https://www.dollargeneral.com/search?searchTerm={query}",
            location_mode="profile",
            notes="Set your store/ZIP in the site UI first.",
            in_stock_selectors=["button:has-text('Add to Cart')"],
            no_results_phrases=["no results"],
            in_stock_containers=["main", ".products-grid", ".search-results"],
        ),
        Retailer(
            name="Walgreens",
            home_url="https://www.walgreens.com/",
            search_url_template="https://www.walgreens.com/search/results.jsp?Ntt={query}",
            location_mode="profile",
            notes="Set your store/ZIP in the site UI first.",
            in_stock_selectors=["button:has-text('Add to cart')"],
            out_of_stock_selectors=["text=Out of stock"],
            no_results_phrases=["we found 0 results"],
            in_stock_containers=["main", "#omni-results", ".product-container"],
        ),
        Retailer(
            name="CVS",
            home_url="https://www.cvs.com/",
            search_url_template="https://www.cvs.com/search?searchTerm={query}",
            location_mode="profile",
            notes="Set your store/ZIP in the site UI first.",
            in_stock_selectors=["button:has-text('Add to cart')"],
            out_of_stock_selectors=["text=Out of stock"],
            no_results_phrases=["0 results", "no results"],
            in_stock_containers=["main", "[data-testid='product-grid']", ".css-1dbjc4n"],
        ),
        Retailer(
            name="Aldi",
            home_url="https://www.aldi.us/",
            search_url_template="https://www.aldi.us/en/search/?q={query}",
            location_mode="profile",
            notes="Set your store/ZIP in the site UI first.",
            no_results_phrases=["no results"],
            in_stock_containers=["main", ".cmp-results", ".mod-search-results"],
        ),
        Retailer(
            name="Costco",
            home_url="https://www.costco.com/",
            search_url_template="https://www.costco.com/CatalogSearch?keyword={query}",
            location_mode="profile",
            notes="Set your warehouse/ZIP in the site UI first.",
            in_stock_selectors=["input#add-to-cart", "button:has-text('Add to Cart')"],
            out_of_stock_selectors=["text=Out of stock"],
            in_stock_containers=["main", "#search-results", ".product-list"],
        ),
        Retailer(
            name="Sam's Club",
            home_url="https://www.samsclub.com/",
            search_url_template="https://www.samsclub.com/s/{query}",
            location_mode="profile",
            notes="Set your club/ZIP in the site UI first.",
            in_stock_selectors=["button:has-text('Add to cart')"],
            out_of_stock_selectors=["text=Out of stock"],
            in_stock_containers=["main", "#idSearchResults", ".sc-product-card"],
        ),
        Retailer(
            name="Whole Foods",
            home_url="https://www.wholefoodsmarket.com/",
            search_url_template="https://www.wholefoodsmarket.com/search?text={query}",
            location_mode="profile",
            notes="Set your store/ZIP in the site UI first.",
            in_stock_phrases=["add to cart"],
            no_results_phrases=["no results"],
            in_stock_containers=["main", ".views-row", ".search-results"],
        ),
        Retailer(
            name="Giant Eagle",
            home_url="https://www.gianteagle.com/",
            search_url_template="https://www.gianteagle.com/grocery/search?q={query}",
            location_mode="profile",
            notes="Set your store/ZIP in the site UI first.",
            in_stock_selectors=["button:has-text('Add to cart')"],
            no_results_phrases=["no results"],
            in_stock_containers=["main", ".product-grid", ".search-results"],
        ),
        Retailer(
            name="Amazon",
            home_url="https://www.amazon.com/",
            search_url_template="https://www.amazon.com/s?k={query}",
            location_mode="profile",
            notes="Set your ZIP in the site UI first.",
            in_stock_selectors=["input#add-to-cart-button"],
            out_of_stock_selectors=["text=Currently unavailable"],
            blocked_selectors=["text=Type the characters you see"],
            in_stock_containers=["main", "[data-component-type='s-search-results']", "#search"],
        ),
    ]


def _first_selector_hit(page, selectors: Iterable[str]) -> Optional[str]:
    for selector in selectors:
        try:
            if page.locator(selector).count() > 0:
                return selector
        except Exception:
            continue
    return None


def _first_phrase_hit(text: str, phrases: Iterable[str]) -> Optional[str]:
    for phrase in phrases:
        if phrase in text:
            return phrase
    return None


def _page_text(page, selectors: Iterable[str]) -> str:
    for selector in selectors:
        try:
            locator = page.locator(selector)
            if locator.count() > 0:
                text = locator.first.inner_text().lower()
                if text:
                    return text
        except Exception:
            continue
    try:
        return page.inner_text("main").lower()
    except Exception:
        return page.inner_text("body").lower()


def _signal_confidence(signal_type: Optional[str]) -> str:
    if signal_type == "selector":
        return "high"
    if signal_type == "phrase":
        return "medium"
    return "low"


def _status_from_retailer(page, retailer: Retailer) -> Tuple[str, str, str]:
    text = page.inner_text("body").lower()
    focused_text = _page_text(page, retailer.in_stock_containers)

    selector_hit = _first_selector_hit(page, retailer.blocked_selectors)
    phrase_hit = _first_phrase_hit(text, ["access denied", "verify you are a human", "captcha", "unusual traffic"])
    if selector_hit or phrase_hit:
        signal_type = "selector" if selector_hit else "phrase"
        return "BLOCKED", f"Blocked by site protections ({selector_hit or phrase_hit}).", _signal_confidence(signal_type)

    selector_hit = _first_selector_hit(page, retailer.out_of_stock_selectors)
    phrase_hit = _first_phrase_hit(text, retailer.out_of_stock_phrases + [
        "out of stock",
        "sold out",
        "currently unavailable",
        "not available",
    ])
    if selector_hit or phrase_hit:
        signal_type = "selector" if selector_hit else "phrase"
        return "OUT_OR_NOT_LISTED", f"Matched out-of-stock signal ({selector_hit or phrase_hit}).", _signal_confidence(signal_type)

    selector_hit = _first_selector_hit(page, retailer.no_results_selectors)
    phrase_hit = _first_phrase_hit(text, retailer.no_results_phrases + ["no results", "we couldn't find", "0 results"])
    if selector_hit or phrase_hit:
        signal_type = "selector" if selector_hit else "phrase"
        return "OUT_OR_NOT_LISTED", f"Matched no-results signal ({selector_hit or phrase_hit}).", _signal_confidence(signal_type)

    selector_hit = _first_selector_hit(page, retailer.in_stock_selectors)
    phrase_hit = _first_phrase_hit(focused_text, retailer.in_stock_phrases + [
        "add to cart",
        "pickup",
        "delivery",
        "ship it",
        "in stock",
    ])
    if selector_hit or phrase_hit:
        signal_type = "selector" if selector_hit else "phrase"
        return "POSSIBLY_IN_STOCK", f"Matched in-stock signal ({selector_hit or phrase_hit}).", _signal_confidence(signal_type)

    return "UNKNOWN", "No clear stock signals found.", _signal_confidence(None)


def _filter_retailers(retailers: Iterable[Retailer], enabled: Optional[Iterable[str]]) -> List[Retailer]:
    if not enabled:
        return list(retailers)
    enabled_set = {name.strip().lower() for name in enabled if name.strip()}
    return [retailer for retailer in retailers if retailer.name.lower() in enabled_set]


def run_checks(
    zip_code: str,
    radius_miles: int,
    products: Iterable[str],
    headless: bool,
    enabled_retailers: Optional[Iterable[str]] = None,
    slow_mode_ms: int = 0,
) -> List[Dict[str, str]]:
    retailers = _filter_retailers(build_retailers(), enabled_retailers)
    results: List[Dict[str, str]] = []
    run_at = datetime.now(timezone.utc).isoformat()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(USER_DATA_DIR, headless=headless)
        for retailer in retailers:
            for product in products:
                query = quote_plus(product)
                url = retailer.search_url_template.format(query=query, zip=zip_code, radius=radius_miles)
                page = context.new_page()
                status = "ERROR"
                details = ""
                confidence = "low"
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(3000)
                    status, details, confidence = _status_from_retailer(page, retailer)
                    if slow_mode_ms > 0:
                        page.wait_for_timeout(slow_mode_ms)
                except PlaywrightTimeoutError:
                    status = "TIMEOUT"
                    details = "Page load timed out."
                    confidence = "low"
                except Exception as exc:  # noqa: BLE001 - surface unexpected errors
                    status = "ERROR"
                    details = f"{type(exc).__name__}: {exc}"
                    confidence = "low"
                finally:
                    page.close()

                score = STATUS_SCORES.get(status, 0)
                results.append(
                    {
                        "retailer": retailer.name,
                        "product": product,
                        "status": status,
                        "score": str(score),
                        "confidence": confidence,
                        "details": details,
                        "url": url,
                        "location_mode": retailer.location_mode,
                        "location_notes": retailer.notes,
                        "zip_code": zip_code,
                        "radius_miles": str(radius_miles),
                        "run_at": run_at,
                    }
                )

        context.close()

    return results
