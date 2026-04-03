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

## Recommended remote access

If you want to check inventory from a phone, tablet, or another PC, the easiest path is to keep the app running on one home machine and reach it over a private network tool such as Tailscale.

Why this is the recommended first deployment:

- The checker uses a persistent Playwright browser profile in `browser_profile/`.
- Several retailers depend on stored location settings and cookies.
- A home machine keeps that profile stable, which makes scans more consistent than most free cloud hosts.

Suggested setup:

1. Install Tailscale on the machine that will run this app.
2. Install Tailscale on your phone/tablet/laptop.
3. Start the Flask app on the home machine:

```
python app.py
```

4. Access it from your other device using the Tailscale IP or MagicDNS name on port `5000`.

Example:

```
http://100.x.y.z:5000
```

If you want to expose it to your tailnet more cleanly later, you can also run it behind a small reverse proxy, but that is optional.

## Optional cloud deploy

You can experiment with Docker-based hosting if you want a public URL. This repo now includes a `Dockerfile`.

Build locally:

```
docker build -t findthekrimpets .
docker run --rm -p 5000:5000 findthekrimpets
```

Important caveats for free cloud hosts:

- Cold starts can make scans feel slow.
- Ephemeral filesystems can wipe `browser_profile/`.
- Losing the saved browser profile means retailer location setup may need to be repeated.

Because of that, cloud hosting is better as a later experiment than the first production setup for this project.

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
- Only one scan runs at a time in a given app process so the shared browser profile is not reused concurrently.
- Some retailers may block automation or require additional manual location setup.
- Always confirm in-store availability before driving out.
