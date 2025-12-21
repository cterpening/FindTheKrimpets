from __future__ import annotations

import argparse

from playwright.sync_api import sync_playwright

import config
from checker import USER_DATA_DIR, build_retailers
from store_locator import build_store_locators


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Open retailer sites to set location profiles.")
    parser.add_argument("--zip", dest="zip_code", default=config.ZIP_CODE, help="ZIP code for store locators.")
    parser.add_argument("--skip", nargs="*", default=[], help="Retailer names to skip.")
    parser.add_argument("--only", nargs="*", default=[], help="Retailer names to include exclusively.")
    return parser.parse_args()


def _filter_names(items, only, skip):
    only_set = {name.strip().lower() for name in only if name.strip()}
    skip_set = {name.strip().lower() for name in skip if name.strip()}
    filtered = []
    for item in items:
        name = item.name.lower()
        if only_set and name not in only_set:
            continue
        if name in skip_set:
            continue
        filtered.append(item)
    return filtered


def main() -> None:
    args = _parse_args()
    retailers = [r for r in build_retailers() if r.location_mode == "profile"]
    locators = build_store_locators()
    retailers = _filter_names(retailers, args.only, args.skip)
    locators = _filter_names(locators, args.only, args.skip)
    print("Location setup: a browser will open for each retailer.")
    print("Set your ZIP/store within ~50 miles, then return here and press Enter.")
    print(f"ZIP used for store locator pages: {args.zip_code}")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(USER_DATA_DIR, headless=False)
        for retailer in retailers:
            page = context.new_page()
            print(f"\nOpening {retailer.name}: {retailer.home_url}")
            page.goto(retailer.home_url, wait_until="domcontentloaded", timeout=60000)
            input("Press Enter after you set location on the site...")
            page.close()
        for locator in locators:
            page = context.new_page()
            url = locator.locator_url_template.format(zip=args.zip_code, radius=config.RADIUS_MILES)
            print(f"\nOpening {locator.name} store locator: {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            input("Press Enter after you confirm store locator results...")
            page.close()
        context.close()

    print("\nSetup complete. You can now run the checker or web app.")


if __name__ == "__main__":
    main()
