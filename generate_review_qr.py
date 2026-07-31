"""
Generate a "tap to copy a review" landing page and a printable QR code
for a business's Google review page.

Usage:
    python generate_review_qr.py \
        --business "Top & Top Bakers - Anand" \
        --maps-url "<google maps place URL or write-review URL>" \
        [--phrases phrases.txt] \
        [--out output] \
        [--qr-url https://your-hosted-page-url]

Run it once without --qr-url to produce review.html, host that file
somewhere public (GitHub Pages, Netlify, etc.), then run it again with
--qr-url pointing at the hosted address to produce the printable QR PNG.
"""

import argparse
import re
import string
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

DEFAULT_PHRASES = [
    "Great experience from start to finish — highly recommend.",
    "Friendly staff and quick service, will definitely come back.",
    "Exactly what I was hoping for — no complaints at all.",
    "Good value and a genuinely pleasant experience.",
]

PAGE_TEMPLATE = string.Template("""<title>$business — Leave a Review</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  :root {
    --bg: #241209;
    --bg-grain: #2c160b;
    --surface: #33200f;
    --text: #f6ead6;
    --text-muted: #b99a78;
    --accent: #d8442f;
    --accent-strong: #f05a3f;
    --gold: #cf9a2e;
    --border: #4d3319;
    --shadow: rgba(0,0,0,0.35);
  }

  :root[data-theme="light"] {
    --bg: #fbe9e2;
    --bg-grain: #f7ded4;
    --surface: #fffaf6;
    --text: #2b160b;
    --text-muted: #8a5a3a;
    --accent: #c23b28;
    --accent-strong: #a9301f;
    --gold: #a97418;
    --border: #ecd3c3;
    --shadow: rgba(90,50,20,0.15);
  }

  @media (prefers-color-scheme: light) {
    :root:not([data-theme="dark"]) {
      --bg: #fbe9e2;
      --bg-grain: #f7ded4;
      --surface: #fffaf6;
      --text: #2b160b;
      --text-muted: #8a5a3a;
      --accent: #c23b28;
      --accent-strong: #a9301f;
      --gold: #a97418;
      --border: #ecd3c3;
      --shadow: rgba(90,50,20,0.15);
    }
  }

  * { box-sizing: border-box; }

  body {
    margin: 0;
    min-height: 100vh;
    background:
      radial-gradient(circle at 1px 1px, var(--bg-grain) 1px, transparent 0) 0 0/22px 22px,
      var(--bg);
    color: var(--text);
    font-family: -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    display: flex;
    justify-content: center;
    padding: 40px 16px 64px;
    line-height: 1.5;
  }

  .card { width: 100%; max-width: 420px; display: flex; flex-direction: column; gap: 22px; }

  .eyebrow {
    text-transform: uppercase; letter-spacing: 0.14em; font-size: 11px;
    font-weight: 600; color: var(--gold); text-align: center;
  }

  h1 {
    font-family: Georgia, "Iowan Old Style", "Times New Roman", serif;
    font-weight: 700; font-size: clamp(26px, 7vw, 32px);
    text-align: center; margin: 0; text-wrap: balance;
  }

  .stars { text-align: center; font-size: 22px; color: var(--gold); letter-spacing: 4px; }

  .lede {
    text-align: center; color: var(--text-muted); font-size: 14.5px;
    max-width: 34ch; margin: 0 auto; text-wrap: balance;
  }

  .tags { display: flex; flex-direction: column; gap: 14px; margin-top: 4px; }

  .tag {
    position: relative; background: var(--surface); border: 1px solid var(--border);
    border-top: none; border-radius: 4px; padding: 18px 16px 16px;
    display: flex; align-items: center; gap: 14px;
  }

  .tag::before {
    content: ""; position: absolute; top: 0; left: 10px; right: 10px;
    height: 0; border-top: 2px dashed var(--border);
  }

  .tag-text { flex: 1; font-size: 15px; color: var(--text); }

  .copy-btn {
    flex-shrink: 0; appearance: none; border: 1px solid var(--gold); background: transparent;
    color: var(--gold); font-size: 12px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.06em; padding: 8px 12px; border-radius: 3px; cursor: pointer;
    transition: background-color 0.15s ease, color 0.15s ease, transform 0.1s ease;
    min-width: 68px;
  }

  .copy-btn:hover { background: var(--gold); color: var(--bg); }
  .copy-btn:active { transform: scale(0.96); }
  .copy-btn:focus-visible { outline: 2px solid var(--accent-strong); outline-offset: 2px; }

  .hint { text-align: center; font-size: 12.5px; color: var(--text-muted); margin-top: -6px; }

  .cta {
    display: block; text-align: center; text-decoration: none; background: var(--accent);
    color: #fff8f3; font-size: 16px; font-weight: 700; padding: 16px 20px; border-radius: 6px;
    box-shadow: 0 6px 16px var(--shadow); transition: background-color 0.15s ease, transform 0.1s ease;
  }

  .cta:hover { background: var(--accent-strong); }
  .cta:active { transform: scale(0.98); }
  .cta:focus-visible { outline: 2px solid var(--gold); outline-offset: 3px; }

  .footer-note { text-align: center; font-size: 11.5px; color: var(--text-muted); opacity: 0.8; }

  .toast {
    position: fixed; left: 50%; bottom: 28px; transform: translateX(-50%) translateY(12px);
    background: var(--gold); color: var(--bg); font-size: 13px; font-weight: 700;
    padding: 10px 18px; border-radius: 999px; opacity: 0; pointer-events: none;
    transition: opacity 0.2s ease, transform 0.2s ease; white-space: nowrap;
  }

  .toast.show { opacity: 1; transform: translateX(-50%) translateY(0); }

  @media (prefers-reduced-motion: reduce) {
    .copy-btn, .cta, .toast { transition: none; }
  }
</style>

<div class="card">
  <div class="eyebrow">$business</div>
  <h1>Loved it? Tell the world in one tap.</h1>
  <div class="stars" aria-hidden="true">★★★★★</div>
  <p class="lede">Pick a line below, copy it, then paste it into your Google review — tweak a word or two to make it yours.</p>

  <div class="tags">
$tags_html
  </div>

  <p class="hint">$hint</p>

  <a class="cta" href="$review_url" target="_blank" rel="noopener">$cta_label</a>

  <p class="footer-note">Thank you for the support.</p>
</div>

<div class="toast" id="toast" role="status" aria-live="polite">Copied!</div>

<script>
  var toast = document.getElementById('toast');
  var toastTimer = null;

  function showToast(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toast.classList.remove('show'); }, 1600);
  }

  function fallbackCopy(text) {
    var ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    try { document.execCommand('copy'); } catch (e) {}
    document.body.removeChild(ta);
  }

  document.querySelectorAll('.copy-btn').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var text = btn.getAttribute('data-text');
      var done = function () {
        var original = btn.textContent;
        btn.textContent = 'Copied';
        showToast('Copied — now paste it on Google');
        setTimeout(function () { btn.textContent = original; }, 1400);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () { fallbackCopy(text); done(); });
      } else {
        fallbackCopy(text);
        done();
      }
    });
  });
</script>
""")

TAG_TEMPLATE = string.Template(
    '    <div class="tag">\n'
    '      <span class="tag-text">$phrase</span>\n'
    '      <button class="copy-btn" data-text="$phrase">Copy</button>\n'
    '    </div>'
)


def review_url_from_maps_url(maps_url: str) -> tuple[str, bool]:
    """Accepts either a direct Google 'write a review' link, or a full
    Google Maps place URL. Returns (url, is_direct_composer).

    is_direct_composer is True only when the URL opens Google's review
    composer (stars + text box) immediately. The CID fallback opens the
    business's Maps page instead -- Google's writereview endpoint requires
    the actual Places API Place ID (a "ChIJ..." string), which is a
    different identifier than the CID embedded in Maps URLs, so CID cannot
    be used to build a writereview link directly.
    """
    parsed = urlparse(maps_url)

    if "search.google.com" in parsed.netloc and "placeid" in parse_qs(parsed.query):
        return maps_url, True

    match = re.search(r"!1s0x[0-9a-fA-F]+:0x([0-9a-fA-F]+)", maps_url)
    if match:
        cid = int(match.group(1), 16)
        return f"https://www.google.com/maps?cid={cid}", False

    raise ValueError(
        "Could not find a place ID in that URL. Pass either:\n"
        "  - a Google Maps place URL (the address-bar URL after opening the "
        "business on Google Maps), or\n"
        "  - a direct write-review URL "
        "(https://search.google.com/local/writereview?placeid=...)"
    )


def build_html(
    business: str, review_url: str, phrases: list[str], is_direct_composer: bool
) -> str:
    tags_html = "\n".join(
        TAG_TEMPLATE.substitute(phrase=phrase) for phrase in phrases
    )
    cta_label = (
        "Leave a Review on Google →"
        if is_direct_composer
        else "Open on Google Maps →"
    )
    hint = (
        "Copied text stays on your clipboard — paste it on the next screen."
        if is_direct_composer
        else "Copied text stays on your clipboard — on the next screen, tap "
        "the stars near the top to start your review, then paste."
    )
    return PAGE_TEMPLATE.substitute(
        business=business,
        review_url=review_url,
        tags_html=tags_html,
        cta_label=cta_label,
        hint=hint,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--business", required=True, help="Business display name")
    parser.add_argument(
        "--maps-url",
        required=True,
        help="Google Maps place URL or direct write-review URL",
    )
    parser.add_argument(
        "--phrases",
        type=Path,
        help="Text file with one suggested review phrase per line",
    )
    parser.add_argument(
        "--out", type=Path, default=Path("output"), help="Output directory"
    )
    parser.add_argument(
        "--qr-url",
        help="Public URL where review.html will be hosted; if given, also "
        "generates a QR PNG pointing at it",
    )
    args = parser.parse_args()

    try:
        review_url, is_direct_composer = review_url_from_maps_url(args.maps_url)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    phrases = DEFAULT_PHRASES
    if args.phrases:
        phrases = [
            line.strip()
            for line in args.phrases.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    args.out.mkdir(parents=True, exist_ok=True)
    html_path = args.out / "index.html"
    html_path.write_text(
        build_html(args.business, review_url, phrases, is_direct_composer),
        encoding="utf-8",
    )
    print(f"Wrote {html_path}")
    print(f"Review link resolved to: {review_url}")
    if not is_direct_composer:
        print(
            "Note: this link opens the business's Google Maps page, not the "
            "review composer directly (a CID-derived link can't reach the "
            "composer). For a one-tap-to-composer link instead, get the URL "
            "by clicking 'Write a review' on Maps yourself and pass that as "
            "--maps-url."
        )

    if args.qr_url:
        try:
            import qrcode
        except ImportError:
            print(
                "qrcode is not installed. Run: pip install qrcode[pil]",
                file=sys.stderr,
            )
            sys.exit(1)
        qr_path = args.out / "review-qr.png"
        qrcode.make(args.qr_url, box_size=12, border=4).save(qr_path)
        print(f"Wrote {qr_path} (encodes {args.qr_url})")
    else:
        print(
            "No --qr-url given. Host index.html somewhere public, then rerun "
            "with --qr-url <hosted-url> to generate the printable QR code."
        )


if __name__ == "__main__":
    main()
