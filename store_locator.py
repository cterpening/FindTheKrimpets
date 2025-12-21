from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

USER_DATA_DIR = "browser_profile"


@dataclass(frozen=True)
class StoreLocator:
    name: str
    locator_url_template: str
    store_card_selector: str
    name_selector: str
    address_selector: str
    distance_selector: str
    link_selector: str
    notes: str
    fallback_url: str = ""


def build_store_locators() -> List[StoreLocator]:
    return [
        StoreLocator(
            name="Meijer",
            locator_url_template="https://www.meijer.com/shopping/store-locator.html?address={zip}",
            store_card_selector="[data-testid='store-card'], .store-card",
            name_selector=".store-card__name, [data-testid='store-name']",
            address_selector=".store-card__address, [data-testid='store-address']",
            distance_selector=".store-card__distance, [data-testid='store-distance']",
            link_selector="a[href*='store-locator'], a[href*='store']",
            notes="Store locator structure may change; update selectors if needed.",
        ),
        StoreLocator(
            name="Kroger",
            locator_url_template="https://www.kroger.com/stores/search?searchText={zip}",
            store_card_selector="[data-testid='store-card'], .StoreCard",
            name_selector="[data-testid='store-name'], .StoreCard-name",
            address_selector="[data-testid='store-address'], .StoreCard-address",
            distance_selector="[data-testid='store-distance'], .StoreCard-distance",
            link_selector="a[href*='/stores/']",
            notes="Store locator structure may change; update selectors if needed.",
        ),
        StoreLocator(
            name="Target",
            locator_url_template="https://www.target.com/store-locator/find-stores/{zip}",
            store_card_selector="[data-test='store-card'], .StoreCard",
            name_selector="[data-test='store-name'], .StoreCard-title",
            address_selector="[data-test='store-address'], .StoreCard-address",
            distance_selector="[data-test='store-distance'], .StoreCard-distance",
            link_selector="a[href*='/store/']",
            notes="Store locator structure may change; update selectors if needed.",
        ),
        StoreLocator(
            name="Walmart",
            locator_url_template="https://www.walmart.com/store/finder?distance={radius}&address={zip}",
            store_card_selector="[data-testid='store-list-item'], .StoreListItem",
            name_selector="[data-testid='store-name'], .StoreListItem-name",
            address_selector="[data-testid='store-address'], .StoreListItem-address",
            distance_selector="[data-testid='store-distance'], .StoreListItem-distance",
            link_selector="a[href*='/store/']",
            notes="Store locator structure may change; update selectors if needed.",
        ),
        StoreLocator(
            name="Dollar General",
            locator_url_template="https://www.dollargeneral.com/store-locator?location={zip}",
            store_card_selector=".store-card, [data-testid='store-card']",
            name_selector=".store-card__name, [data-testid='store-name']",
            address_selector=".store-card__address, [data-testid='store-address']",
            distance_selector=".store-card__distance, [data-testid='store-distance']",
            link_selector="a[href*='store-locator'], a[href*='store']",
            notes="Store locator structure may change; update selectors if needed.",
        ),
        StoreLocator(
            name="Walgreens",
            locator_url_template="https://www.walgreens.com/storelocator/find.jsp?requestType=locator&location={zip}",
            store_card_selector=".storeInfo, [data-testid='store-card']",
            name_selector=".storeName, [data-testid='store-name']",
            address_selector=".address, [data-testid='store-address']",
            distance_selector=".distance, [data-testid='store-distance']",
            link_selector="a[href*='storelocator']",
            notes="Store locator structure may change; update selectors if needed.",
        ),
        StoreLocator(
            name="CVS",
            locator_url_template="https://www.cvs.com/store-locator/cvs-pharmacy-locations?searchBy=address&address={zip}",
            store_card_selector=".store-info, [data-testid='store-card']",
            name_selector=".store-name, [data-testid='store-name']",
            address_selector=".store-address, [data-testid='store-address']",
            distance_selector=".store-distance, [data-testid='store-distance']",
            link_selector="a[href*='/store-locator/']",
            notes="Store locator structure may change; update selectors if needed.",
        ),
        StoreLocator(
            name="Aldi",
            locator_url_template="https://stores.aldi.us/?q={zip}",
            store_card_selector=".store-info, [data-testid='store-card']",
            name_selector=".location-name, [data-testid='store-name']",
            address_selector=".address, [data-testid='store-address']",
            distance_selector=".distance, [data-testid='store-distance']",
            link_selector="a[href*='stores.aldi.us']",
            notes="Store locator structure may change; update selectors if needed.",
        ),
        StoreLocator(
            name="Costco",
            locator_url_template="https://www.costco.com/warehouse-locations?zip={zip}",
            store_card_selector=".warehouse-list-item, [data-testid='store-card']",
            name_selector=".warehouse-list-item__name, [data-testid='store-name']",
            address_selector=".warehouse-list-item__address, [data-testid='store-address']",
            distance_selector=".warehouse-list-item__distance, [data-testid='store-distance']",
            link_selector="a[href*='warehouse-locations']",
            notes="Store locator structure may change; update selectors if needed.",
        ),
        StoreLocator(
            name="Sam's Club",
            locator_url_template="https://www.samsclub.com/storefinder?searchTerm={zip}",
            store_card_selector=".sc-store-info, [data-testid='store-card']",
            name_selector=".sc-store-info__name, [data-testid='store-name']",
            address_selector=".sc-store-info__address, [data-testid='store-address']",
            distance_selector=".sc-store-info__distance, [data-testid='store-distance']",
            link_selector="a[href*='store']",
            notes="Store locator structure may change; update selectors if needed.",
        ),
        StoreLocator(
            name="Whole Foods",
            locator_url_template="https://www.wholefoodsmarket.com/stores?search={zip}",
            store_card_selector=".store-teaser, [data-testid='store-card']",
            name_selector=".store-teaser__title, [data-testid='store-name']",
            address_selector=".store-teaser__address, [data-testid='store-address']",
            distance_selector=".store-teaser__distance, [data-testid='store-distance']",
            link_selector="a[href*='/stores/']",
            notes="Store locator structure may change; update selectors if needed.",
        ),
        StoreLocator(
            name="Giant Eagle",
            locator_url_template="https://www.gianteagle.com/store-locator?search={zip}",
            store_card_selector=".store-card, [data-testid='store-card']",
            name_selector=".store-card__name, [data-testid='store-name']",
            address_selector=".store-card__address, [data-testid='store-address']",
            distance_selector=".store-card__distance, [data-testid='store-distance']",
            link_selector="a[href*='store-locator'], a[href*='store']",
            notes="Store locator structure may change; update selectors if needed.",
        ),
    ]


def _safe_text(locator) -> str:
    try:
        return locator.inner_text().strip()
    except Exception:
        return ""


def _pick_first(locator, selectors: str) -> str:
    for selector in [s.strip() for s in selectors.split(",") if s.strip()]:
        item = locator.locator(selector)
        if item.count() > 0:
            text = _safe_text(item.first)
            if text:
                return text
    return ""


def _pick_first_link(locator, selectors: str) -> str:
    for selector in [s.strip() for s in selectors.split(",") if s.strip()]:
        item = locator.locator(selector)
        if item.count() > 0:
            href = item.first.get_attribute("href")
            if href:
                return href
    return ""


def find_stores(
    zip_code: str,
    radius_miles: int,
    enabled_retailers: Optional[Iterable[str]] = None,
    headless: bool = True,
    slow_mode_ms: int = 0,
    limit_per_retailer: int = 5,
) -> List[Dict[str, str]]:
    locators = build_store_locators()
    if enabled_retailers:
        enabled_set = {name.strip().lower() for name in enabled_retailers if name.strip()}
        locators = [locator for locator in locators if locator.name.lower() in enabled_set]

    results: List[Dict[str, str]] = []
    run_at = datetime.now(timezone.utc).isoformat()

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(USER_DATA_DIR, headless=headless)
        for locator in locators:
            url = locator.locator_url_template.format(zip=zip_code, radius=radius_miles)
            page = context.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(3000)
                cards = page.locator(locator.store_card_selector)
                card_count = min(cards.count(), limit_per_retailer)
                if card_count == 0:
                    results.append(
                        {
                            "retailer": locator.name,
                            "store_name": "No store cards found",
                            "address": "",
                            "distance": "",
                            "store_url": url,
                            "details": "Locator page loaded, but no store cards matched selectors.",
                            "zip_code": zip_code,
                            "radius_miles": str(radius_miles),
                            "run_at": run_at,
                        }
                    )
                else:
                    for i in range(card_count):
                        card = cards.nth(i)
                        store_name = _pick_first(card, locator.name_selector) or locator.name
                        address = _pick_first(card, locator.address_selector)
                        distance = _pick_first(card, locator.distance_selector)
                        store_url = _pick_first_link(card, locator.link_selector) or url
                        results.append(
                            {
                                "retailer": locator.name,
                                "store_name": store_name,
                                "address": address,
                                "distance": distance,
                                "store_url": store_url,
                                "details": "Parsed from store locator page.",
                                "zip_code": zip_code,
                                "radius_miles": str(radius_miles),
                                "run_at": run_at,
                            }
                        )
                if slow_mode_ms > 0:
                    page.wait_for_timeout(slow_mode_ms)
            except PlaywrightTimeoutError:
                results.append(
                    {
                        "retailer": locator.name,
                        "store_name": "Timeout loading locator page",
                        "address": "",
                        "distance": "",
                        "store_url": url,
                        "details": "Locator page load timed out.",
                        "zip_code": zip_code,
                        "radius_miles": str(radius_miles),
                        "run_at": run_at,
                    }
                )
            except Exception as exc:  # noqa: BLE001 - surface unexpected errors
                results.append(
                    {
                        "retailer": locator.name,
                        "store_name": "Locator error",
                        "address": "",
                        "distance": "",
                        "store_url": url,
                        "details": f"{type(exc).__name__}: {exc}",
                        "zip_code": zip_code,
                        "radius_miles": str(radius_miles),
                        "run_at": run_at,
                    }
                )
            finally:
                page.close()
        context.close()

    return results
