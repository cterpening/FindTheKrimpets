from __future__ import annotations

import csv
from contextlib import contextmanager
from datetime import datetime
from io import StringIO
import os
from threading import Lock
from typing import List, Optional

from flask import Flask, Response, render_template, request

import checker
import config
import store_locator

app = Flask(__name__)

LAST_RESULTS: List[dict] | None = None
LAST_STORES: List[dict] | None = None
LAST_PARAMS: dict | None = None
RUN_HISTORY: List[dict] = []
RUN_COUNTER = 0
SCAN_LOCK = Lock()
SCAN_ACTIVE = False


def _parse_products(text: str) -> List[str]:
    raw_items = [item.strip() for item in text.replace("\n", ",").split(",")]
    return [item for item in raw_items if item]


def _sort_results(results: List[dict]) -> List[dict]:
    return sorted(
        results,
        key=lambda row: (
            row.get("product", ""),
            -int(row.get("score", 0)),
            -checker.CONFIDENCE_SCORES.get(row.get("confidence", "low"), 0),
            row.get("retailer", ""),
        ),
    )


def _record_run(params: dict, results: List[dict], stores: Optional[List[dict]]) -> int:
    global RUN_COUNTER

    RUN_COUNTER += 1
    run_id = RUN_COUNTER
    RUN_HISTORY.append(
        {
            "id": run_id,
            "run_at": datetime.now(),
            "params": params,
            "results": results,
            "stores": stores or [],
        }
    )

    max_history = getattr(config, "MAX_HISTORY", 10)
    if len(RUN_HISTORY) > max_history:
        RUN_HISTORY.pop(0)

    return run_id


def _find_run(run_id: Optional[int]) -> Optional[dict]:
    if not RUN_HISTORY:
        return None
    if run_id is None:
        return RUN_HISTORY[-1]
    for run in RUN_HISTORY:
        if run.get("id") == run_id:
            return run
    return None


@contextmanager
def _scan_session():
    global SCAN_ACTIVE

    acquired = SCAN_LOCK.acquire(blocking=False)
    if not acquired:
        raise RuntimeError("Another scan is already running. Wait for it to finish, then try again.")

    SCAN_ACTIVE = True
    try:
        yield
    finally:
        SCAN_ACTIVE = False
        SCAN_LOCK.release()


@app.route("/", methods=["GET", "POST"])
def index():
    global LAST_RESULTS
    global LAST_STORES
    global LAST_PARAMS

    results = None
    stores = None
    run_error = None

    zip_code = config.ZIP_CODE
    radius_miles = config.RADIUS_MILES
    products = config.PRODUCTS
    headless = config.HEADLESS
    slow_mode_ms = getattr(config, "SLOW_MODE_MS", 0)
    include_stores = getattr(config, "INCLUDE_STORE_LOCATIONS", True)
    retailers = checker.build_retailers()
    enabled_retailers = [r.name for r in retailers]
    store_limit = getattr(config, "STORE_LIMIT", 5)

    if request.method == "POST":
        zip_code = request.form.get("zip_code", "").strip() or config.ZIP_CODE
        radius_raw = request.form.get("radius_miles", "").strip()
        if radius_raw.isdigit():
            radius_miles = int(radius_raw)
        products_text = request.form.get("products", "").strip()
        products = _parse_products(products_text) or config.PRODUCTS
        headless = request.form.get("headless") == "on"
        include_stores = request.form.get("include_stores") == "on"
        slow_mode_raw = request.form.get("slow_mode_ms", "").strip()
        if slow_mode_raw.isdigit():
            slow_mode_ms = int(slow_mode_raw)

        selected = request.form.getlist("retailers")
        if selected:
            enabled_retailers = selected

        try:
            with _scan_session():
                results = checker.run_checks(
                    zip_code=zip_code,
                    radius_miles=radius_miles,
                    products=products,
                    headless=headless,
                    enabled_retailers=enabled_retailers,
                    slow_mode_ms=slow_mode_ms,
                )
                results = _sort_results(results)
                LAST_RESULTS = results
                LAST_STORES = None
                LAST_PARAMS = {
                    "zip_code": zip_code,
                    "radius_miles": radius_miles,
                    "products": products,
                    "headless": headless,
                    "enabled_retailers": enabled_retailers,
                    "slow_mode_ms": slow_mode_ms,
                    "include_stores": include_stores,
                    "store_limit": store_limit,
                }
                if include_stores:
                    stores = store_locator.find_stores(
                        zip_code=zip_code,
                        radius_miles=radius_miles,
                        enabled_retailers=enabled_retailers,
                        headless=headless,
                        slow_mode_ms=slow_mode_ms,
                        limit_per_retailer=store_limit,
                    )
                    LAST_STORES = stores

                _record_run(LAST_PARAMS, results, LAST_STORES)
        except Exception as exc:  # noqa: BLE001 - surface unexpected errors
            run_error = f"{type(exc).__name__}: {exc}"

    return render_template(
        "index.html",
        results=results,
        run_error=run_error,
        zip_code=zip_code,
        radius_miles=radius_miles,
        products=products,
        headless=headless,
        slow_mode_ms=slow_mode_ms,
        include_stores=include_stores,
        now=datetime.now(),
        last_params=LAST_PARAMS,
        retailers=retailers,
        enabled_retailers=enabled_retailers,
        stores=stores,
        scan_active=SCAN_ACTIVE,
        run_history=list(reversed(RUN_HISTORY[-5:])),
    )


@app.route("/export.csv")
def export_csv() -> Response:
    run_id_raw = request.args.get("run_id")
    run_id = int(run_id_raw) if run_id_raw and run_id_raw.isdigit() else None
    run = _find_run(run_id)

    if not run:
        return Response("No results yet. Run a scan first.", status=400, mimetype="text/plain")

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "retailer",
            "product",
            "status",
            "score",
            "confidence",
            "details",
            "url",
            "location_mode",
            "location_notes",
            "zip_code",
            "radius_miles",
            "run_at",
        ],
    )
    writer.writeheader()
    writer.writerows(run["results"])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=inventory_run_{run['id']}.csv"
    return response


@app.route("/stores.csv")
def export_stores_csv() -> Response:
    run_id_raw = request.args.get("run_id")
    run_id = int(run_id_raw) if run_id_raw and run_id_raw.isdigit() else None
    run = _find_run(run_id)

    if not run or not run.get("stores"):
        return Response("No store results yet. Run a scan with store locations enabled.", status=400, mimetype="text/plain")

    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "retailer",
            "store_name",
            "address",
            "distance",
            "store_url",
            "details",
            "zip_code",
            "radius_miles",
            "run_at",
        ],
    )
    writer.writeheader()
    writer.writerows(run["stores"])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = f"attachment; filename=store_locations_run_{run['id']}.csv"
    return response


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=debug)
