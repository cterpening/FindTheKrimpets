# FindTheKrimpets

Local inventory checker for Tastykake Butterscotch Krimpets and Vanilla Coke Zero.

## Quick start

1. Install dependencies:

```
pip install -r requirements.txt
playwright install
```

2. Edit `config.py` to set your ZIP code (50-mile radius is the default) and products.
   - Optional: tweak `SLOW_MODE_MS`, `STORE_LIMIT`, and `INCLUDE_STORE_LOCATIONS`.

3. Run the one-time location setup (opens a browser for each retailer that needs a profile location):

```
python setup_location.py
```

This also opens store locator pages for quick verification of nearby stores.

You can skip blocked retailers or override ZIP:

```
python setup_location.py --zip 46038 --skip Meijer Kroger
```

4. Start the web app:

```
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## CSV export

After a scan, click "Export CSV" for the latest run or use the run history links:

```
http://127.0.0.1:5000/export.csv
```

For store locator results:

```
http://127.0.0.1:5000/stores.csv
```

## Notes

- The checker uses retailer-specific selectors plus fallback text heuristics.
- ZIP/radius are included with each scan, but most retailers still rely on saved profile locations.
- Store locator pages are best-effort and may require selector tweaks per retailer.
- You can enable/disable retailers per scan in the web UI.
- Some retailers may block automation or require additional manual location setup.
- Always confirm in-store availability before driving out.
