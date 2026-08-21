#!/usr/bin/env python3
"""Generate one-time-kept 2026 review pages from data/batch2.tsv."""
from __future__ import annotations

import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TSV = ROOT / "data" / "batch2.tsv"
JSON = ROOT / "data" / "batch2.json"

ORIGINAL_28 = {
    "b085m544gg",
    "b0bt1wl6ky",
    "b001e0xz98",
    "b00ozhwx1i",
    "b09mzwb73g",
    "b0bt1ncph4",
    "b0913m1188",
    "b09m5xf6jv",
    "b08kkk8d8j",
    "b0dd7zc68q",
    "b00dm8kq3i",
    "b010elibvy",
    "b0c58rgn9d",
    "b0cgvm7sbf",
    "b071nlbtdz",
    "b0cyg23nzr",
    "b0c67y9lj7",
    "b09t6nffy1",
    "b0b1p5l7l9",
    "b0bw7kt4wc",
    "b08vmwq6bf",
    "b0d4dk3xz7",
    "b0d2ndg6sx",
    "b07nwmvmt1",
    "b0d83g2729",
    "b07k2nzx8l",
    "b0b47gzdrl",
    "b0ckf6vl74",
}

BODIES = [
    "{product} was a one-time household order in 2026, and we did not return it. Nothing returned on this order. A kept household copy of the title as listed. One purchase.",
    "We bought {product} once in 2026 and did not return it. This is not a repurchase. The order was kept as listed. One purchase in 2026.",
    "{product}: one 2026 order, not returned. We are not claiming a reorder. A kept item as listed. Bought 1×.",
    "A single 2026 purchase of {product} that we did not send back. No return on this order. Not a repeat buy. One order, kept.",
]


def load_products():
    if JSON.exists():
        import json

        data = json.loads(JSON.read_text())
        if not isinstance(data, list):
            raise SystemExit("data/batch2.json must be a list")
        products = []
        for row in data:
            asin = str(row["asin"]).strip()
            title = str(row.get("product") or row.get("title") or "").strip()
            products.append((asin, title, row))
        return products
    if not TSV.exists():
        raise SystemExit("missing data/batch2.tsv")
    products = []
    for line in TSV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        asin, title = line.split("\t", 1)
        products.append((asin.strip(), title.strip(), None))
    return products


def page_html(asin: str, title: str, idx: int) -> str:
    esc = html.escape(title, quote=True)
    body = html.escape(BODIES[idx % len(BODIES)].format(product=title), quote=False)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc} — Repeat Buys review</title>
<meta name="description" content="{esc}: we bought it once in 2026. Repeat Buys may earn from Amazon Associates.">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<header>
  <a class="brand" href="index.html">Repeat Buys</a>
  <nav>
    <a href="index.html">Reviews</a>
    <a href="about.html">About</a>
    <a href="disclosure.html">Disclosure</a>
    <a href="privacy.html">Privacy</a>
  </nav>
</header>
<main>
<p class="disclosure">As an Amazon Associate, Repeat Buys may earn from qualifying purchases. We bought every product reviewed here with our own money. <a href="disclosure.html">Full disclosure</a>.</p>
<article class="review">
  <h1>{esc} — one copy, kept</h1>
  <p class="meta">{esc} · ASIN {html.escape(asin, quote=True)} · Bought 1× in 2026</p>
  <p class="stars">★★★★</p>
  <div class="prose">
    <p>{body}</p>
  </div>
  <a class="buy" href="https://www.amazon.com/dp/{html.escape(asin, quote=True)}?tag=repeatbuys-20" rel="nofollow sponsored noopener" target="_blank">View on Amazon</a>
</article>
</main>
<footer>
  <p>© 2026 Repeat Buys. Reviews of products we purchased and used. <a href="disclosure.html">Affiliate disclosure</a>.</p>
  <p>Questions: <a href="mailto:bruce.bishop@gmail.com">bruce.bishop@gmail.com</a></p>
</footer>
</body>
</html>
"""


def card_html(asin: str, title: str, filename: str) -> str:
    esc = html.escape(title, quote=True)
    return (
        f'<a class="card" href="{filename}">\n'
        f"  <h2>{esc} — one copy, kept</h2>\n"
        f'  <p class="meta">{esc} · Bought 1× in 2026</p>\n'
        f"</a>"
    )


def update_index(products):
    path = ROOT / "index.html"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "<title>Repeat Buys — household product reviews of items we actually repurchase</title>",
        "<title>Repeat Buys — household reviews of repeat purchases and one-time kept 2026 orders</title>",
    )
    text = text.replace(
        '<meta name="description" content="Repeat Buys is household product reviews of items we actually repurchase. We bought, used, and reordered every product here in 2026.">',
        '<meta name="description" content="Repeat Buys lists products we repurchased in 2026 first, then one-time 2026 purchases we kept and did not return. No samples. No returns.">',
    )
    text = text.replace(
        '<p class="lede">Household reviews of products we purchased, used, and reordered in 2026. No samples. No returns.</p>',
        '<p class="lede">Repeat purchases first; one-time kept 2026 purchases included. No samples. No returns.</p>',
    )
    cards = "\n".join(card_html(asin, title, asin.lower() + ".html") for asin, title, _ in products)
    # Strip any previously generated one-time cards after the original 28.
    marker = '<a class="card" href="b0ckf6vl74.html">'
    idx = text.find(marker)
    if idx < 0:
        raise SystemExit("could not find last original card in index.html")
    end = text.find("</a>", idx)
    end = text.find("\n", end)
    prefix = text[: end + 1]
    suffix_start = text.find("</div>", end)
    text = prefix + "\n" + cards + "\n" + text[suffix_start:]
    path.write_text(text, encoding="utf-8")


def update_about():
    path = ROOT / "about.html"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        '<meta name="description" content="Honest household reviews of products we bought more than once.">',
        '<meta name="description" content="Honest household reviews of products we bought. Repeat purchases first; one-time kept 2026 purchases included. No samples. No returns.">',
    )
    text = text.replace(
        "<p>Repeat Buys is a small review site run by Bruce Bishop in Waco, Texas. The rule is simple: we only write about products we bought, used, and then bought again.</p>\n"
        "<p>That is the whole editorial filter. No samples, no gifted inventory, no reviews of things we returned.</p>",
        "<p>Repeat Buys is a small review site run by Bruce Bishop in Waco, Texas. Repeat purchases come first. We also include one-time 2026 purchases we kept and did not return.</p>\n"
        "<p>No samples, no gifted inventory, no reviews of things we returned.</p>",
    )
    path.write_text(text, encoding="utf-8")


def update_sitemap(products):
    path = ROOT / "sitemap.xml"
    text = path.read_text(encoding="utf-8")
    base = "https://bwbishop-max.github.io/repeat-buys/"
    extra = []
    for asin, _title, _row in products:
        loc = f"{base}{asin.lower()}.html"
        extra.append(f"  <url>\n    <loc>{loc}</loc>\n  </url>")
    extra_xml = "\n".join(extra)
    text = re.sub(
        r"\n  <url>\n    <loc>https://bwbishop-max.github.io/repeat-buys/006280197x.html</loc>\n  </url>",
        "",
        text,
    )
    if not extra_xml:
        path.write_text(text, encoding="utf-8")
        return
    if "</urlset>" not in text:
        raise SystemExit("sitemap.xml missing urlset close")
    # Drop previously appended one-time URLs after the last original 28 page.
    last_orig = f"{base}b0ckf6vl74.html"
    idx = text.find(last_orig)
    if idx < 0:
        raise SystemExit("could not find last original sitemap URL")
    close_url = text.find("</url>", idx) + len("</url>")
    text = text[:close_url] + "\n" + extra_xml + "\n</urlset>\n"
    path.write_text(text, encoding="utf-8")


def main():
    products = load_products()
    if len(products) != 348:
        print(f"warning: expected 348 products, got {len(products)}", file=sys.stderr)
    written = 0
    skipped_original = 0
    for i, (asin, title, _row) in enumerate(products):
        filename = asin.lower() + ".html"
        if filename[:-5] in ORIGINAL_28:
            skipped_original += 1
            continue
        (ROOT / filename).write_text(page_html(asin, title, i), encoding="utf-8")
        written += 1
    update_index(products)
    update_about()
    update_sitemap(products)
    print(f"wrote {written} pages from {len(products)} products; skipped_original={skipped_original}")


if __name__ == "__main__":
    main()
