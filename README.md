# Review QR Generator

Generates a printable QR code that links to a small landing page with
tap-to-copy review phrases for a business, plus a button straight into
Google's own "write a review" composer.

This does **not** auto-submit reviews or pre-fill Google's actual review
box — that's against Google's review policies and can get a business's
listing suspended. It only removes the "what do I even write" friction:
the customer copies a suggested line, pastes it into Google, tweaks it if
they like, and submits it themselves.

## 1. Get the business's Google review URL

There are two ways to point this tool at a business. **Prefer the first —
it's the only one that lands the customer directly in Google's review
composer (stars + text box).**

**Option A — direct composer link (best):**
1. Open **Google Maps** (not Google Search) and find the business.
2. Click **"Write a review"** on the listing.
3. Copy the URL from your browser's address bar at that point — it looks
   like `https://search.google.com/local/writereview?placeid=ChIJ...`.

**Option B — plain Maps place URL (fallback):**
If you just copy the business's Maps page URL without clicking "Write a
review" first, `generate_review_qr.py` can still use it — but it can only
build a link to the business's Google Maps page (`google.com/maps?cid=...`),
not the review composer itself. That's a real limitation, not a shortcut:
Google's composer requires an official Places API Place ID (`ChIJ...`),
which isn't present in the Maps URL — only a different numeric ID (CID) is.
The script does not guess or convert between them silently; check your
terminal output after running it to see which kind of link you got.

## 2. Install dependencies

```
pip install qrcode[pil]
```

## 3. Generate the landing page

```
python generate_review_qr.py \
  --business "Your Business Name" \
  --maps-url "<the URL from step 1>" \
  --out output
```

This writes `output/review.html`. Optionally pass `--phrases phrases.txt`
with one suggested review line per file line to customize the wording
(defaults are generic if omitted).

## 4. Host the page

Upload `output/review.html` somewhere public — GitHub Pages, Netlify
Drop, or any static host. Note the final URL.

## 5. Generate the QR code

```
python generate_review_qr.py \
  --business "Your Business Name" \
  --maps-url "<the URL from step 1>" \
  --out output \
  --qr-url "<the hosted URL from step 4>"
```

This writes `output/review-qr.png`. Print it and place it wherever
customers will scan it.

---

*This information is for educational purposes. Automating or incentivizing
fake reviews violates Google's review policies — this tool is designed to
avoid that by requiring a genuine, user-submitted review at the end.*
