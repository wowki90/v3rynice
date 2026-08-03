#!/usr/bin/env python3
"""
Build the static VERY NICE catalogue from tools/products.json.

The shop is paused: nothing is purchasable, so there is no cart, no checkout
and no Shopify JS. Every product is rendered as browsable-but-unavailable.

Run from the repo root:   python3 tools/build.py
"""

import json
import os
import re
import html
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRODUCTS = os.path.join(ROOT, "tools", "products.json")
IMG_DIR = os.path.join(ROOT, "assets", "products")

SITE_NAME = "VERY NICE"
TAGLINE = "Style with purpose. 50% of profits to causes that matter."
PAUSED_MSG = "The shop is on pause — nothing is available to order right now."
CHARITY_URL = "https://www.saveukraineua.org"

# Set this once you've confirmed the address, then re-run the build.
CONTACT_EMAIL = ""


def esc(s):
    return html.escape(s or "", quote=True)


def clean_html(raw):
    """Shopify body_html, stripped of anything that shouldn't be in a static page."""
    if not raw:
        return ""
    s = re.sub(r"(?is)<(script|style|iframe|form)\b.*?</\1>", "", raw)
    s = re.sub(r"(?is)<\s*(script|style|iframe|form|input|button)\b[^>]*>", "", s)
    s = re.sub(r'(?i)\son\w+\s*=\s*"[^"]*"', "", s)
    s = re.sub(r"(?i)\son\w+\s*=\s*'[^']*'", "", s)
    return s.strip()


def money(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return ""
    return f"${f:,.2f}".replace(".00", "")


def images_for(handle):
    if not os.path.isdir(IMG_DIR):
        return []
    found = [f for f in os.listdir(IMG_DIR) if f.startswith(handle + "-")]

    def idx(name):
        m = re.search(r"-(\d+)\.[a-z]+$", name)
        return int(m.group(1)) if m else 0

    return sorted(found, key=idx)


def shell(title, body, depth=0, desc="", current=""):
    """Wrap page content in the site chrome. `depth` = how many dirs deep."""
    up = "../" * depth if depth else ""

    def nav_item(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{up}{href}"{cur}>{label}</a>'

    nav = "\n        ".join([
        nav_item("", "Shop", "shop"),
        nav_item("pages/the-very-nice-promise/", "The Promise", "promise"),
        nav_item("pages/contact/", "Contact", "contact"),
    ])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc or PAUSED_MSG)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc or PAUSED_MSG)}">
<meta property="og:type" content="website">
<link rel="icon" href="{up}assets/brand/logo_small.png" type="image/png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}assets/site.css">
</head>
<body>

<div class="paused-bar"><strong>Shop paused.</strong> Nothing is available to order right now.</div>

<header class="site-head">
  <div class="wrap">
    <a class="logo" href="{up}"><img src="{up}assets/brand/logo.png" alt="{SITE_NAME}" width="148"></a>
    <nav class="site-nav">
        {nav}
    </nav>
  </div>
</header>

<main>
  <div class="wrap">
{body}
  </div>
</main>

<footer class="site-foot">
  <div class="wrap">
    <div class="foot-links">
      <a href="{up}">Shop</a>
      <a href="{up}pages/the-very-nice-promise/">The Promise</a>
      <a href="{up}pages/contact/">Contact</a>
    </div>
    <div>&copy; {SITE_NAME} — shop currently paused</div>
  </div>
</footer>

</body>
</html>
"""


def write(path, content):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  wrote {path}")


def build():
    data = json.load(open(PRODUCTS, encoding="utf-8"))
    products = data["products"]

    # ---------- home / catalogue ----------
    cards = []
    for p in products:
        imgs = images_for(p["handle"])
        if not imgs:
            print(f"  !! no local images for {p['handle']} — skipping card")
            continue
        price = money(p["variants"][0]["price"]) if p.get("variants") else ""
        cards.append(f"""      <a class="card" href="products/{esc(p['handle'])}/">
        <div class="card-media">
          <span class="badge">Unavailable</span>
          <img src="assets/products/{esc(imgs[0])}" alt="{esc(p['title'])}" loading="lazy">
        </div>
        <div class="card-body">
          <div class="card-title">{esc(p['title'])}</div>
          <div class="card-price">{esc(price)}</div>
        </div>
      </a>""")

    home = f"""    <div class="lede">
      <h1>The shop is taking a break</h1>
      <p>Everything below is part of the {SITE_NAME} range. None of it is
      available to order at the moment — have a look around anyway.</p>
    </div>
    <div class="grid">
{chr(10).join(cards)}
    </div>"""
    write("index.html", shell(f"{SITE_NAME} — shop paused", home, 0,
                             desc=TAGLINE, current="shop"))

    # ---------- product pages ----------
    for p in products:
        imgs = images_for(p["handle"])
        if not imgs:
            continue
        price = money(p["variants"][0]["price"]) if p.get("variants") else ""

        gallery = "\n".join(
            f'        <img src="../../assets/products/{esc(i)}" alt="{esc(p["title"])}" loading="lazy">'
            for i in imgs
        )

        opts = []
        for o in p.get("options", []):
            vals = [v for v in o.get("values", []) if v and v.lower() != "default title"]
            if not vals:
                continue
            chips = "\n".join(f'          <span class="chip">{esc(v)}</span>' for v in vals)
            opts.append(f"""      <div class="opt-group">
        <div class="opt-label">{esc(o.get('name', ''))}</div>
        <div class="chips">
{chips}
        </div>
      </div>""")

        body = f"""    <a class="back" href="../../">&larr; Back to the shop</a>
    <div class="product">
      <div class="gallery">
{gallery}
      </div>
      <div class="product-info">
        <h1>{esc(p['title'])}</h1>
        <div class="price-row">
          <span class="price">{esc(price)}</span>
          <span class="status">Currently unavailable</span>
        </div>
        <div class="unavailable-note">
          This item can't be ordered right now — the {SITE_NAME} shop is paused.
        </div>
{chr(10).join(opts)}
        <div class="desc">{clean_html(p.get('body_html'))}</div>
      </div>
    </div>"""

        plain = re.sub(r"<[^>]+>", " ", p.get("body_html") or "")
        plain = re.sub(r"\s+", " ", html.unescape(plain)).strip()[:160]
        write(f"products/{p['handle']}/index.html",
              shell(f"{p['title']} — {SITE_NAME}", body, 2,
                    desc=plain or PAUSED_MSG, current="shop"))

    # ---------- the promise ----------
    promise = f"""    <div class="prose">
      <h1>The {SITE_NAME} Promise</h1>
      <p>At {SITE_NAME}, we want to support change by combining style with purpose,
      creating a world where every purchase makes a meaningful impact.</p>
      <p>We pledge 50% of our profits to causes that inspire change, starting with
      supporting humanitarian efforts in Ukraine. Together, we can help provide
      essential aid to those in need.
      <a href="{CHARITY_URL}" target="_blank" rel="noopener noreferrer">Learn more about our current charity</a>.</p>
      <p>As our brand grows, we plan to support other meaningful causes and even
      give you the option to choose where your contribution goes.</p>
      <p><em>The shop is paused for now, so nothing is available to order — but the
      promise stands for whenever it opens again.</em></p>
      <div class="btn-row"><a class="btn" href="../../">Have a look at the range</a></div>
    </div>"""
    write("pages/the-very-nice-promise/index.html",
          shell(f"The {SITE_NAME} Promise", promise, 2,
                desc=TAGLINE, current="promise"))

    # ---------- contact ----------
    if CONTACT_EMAIL:
        reach = (f'<p>The contact form is off while the shop is paused, but you can '
                 f'still reach us at '
                 f'<a href="mailto:{esc(CONTACT_EMAIL)}">{esc(CONTACT_EMAIL)}</a>.</p>\n'
                 f'      <p>Nothing is available to order at the moment. If you\'re after '
                 f'something you saw here, get in touch and we\'ll let you know if it '
                 f'comes back.</p>')
    else:
        # No address configured yet — don't invite contact we can't receive.
        reach = ('<p>The contact form is off while the shop is paused, and nothing is '
                 'available to order at the moment.</p>\n'
                 '      <p>Check back another time — the range is still here to look at.</p>')

    contact = f"""    <div class="prose">
      <h1>Contact</h1>
      {reach}
      <div class="btn-row"><a class="btn" href="../../">Back to the shop</a></div>
    </div>"""
    write("pages/contact/index.html",
          shell(f"Contact — {SITE_NAME}", contact, 2,
                desc=f"Contact {SITE_NAME}.", current="contact"))

    # ---------- redirects for old Shopify paths ----------
    # Collection and blog URLs that no longer have a page of their own, but may
    # still be linked from elsewhere. Bounce them to the catalogue.
    for path in ("collections/frontpage", "collections/all", "blogs/news"):
        write(f"{path}/index.html", f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{SITE_NAME}</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="/">
<script>window.location.replace('/');</script>
<meta http-equiv="refresh" content="0; url=/">
</head>
<body></body>
</html>
""")

    # ---------- 404 ----------
    nf = """    <div class="prose">
      <h1>Page not found</h1>
      <p>That page isn't here any more — the shop has been slimmed down while
      it's paused.</p>
      <div class="btn-row"><a class="btn" href="/">Back to the shop</a></div>
    </div>"""
    write("404.html", shell(f"Not found — {SITE_NAME}", nf, 0))

    print(f"\nBuilt {len(products)} products.")
    if not CONTACT_EMAIL:
        print("NOTE: CONTACT_EMAIL is empty — set it at the top of this file "
              "and re-run to add a contact address.")


if __name__ == "__main__":
    build()
