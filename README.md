# v3rynice.com — static catalogue (shop paused)

Static replacement for the VERY NICE Shopify store, so the Shopify
subscription can be cancelled. The range stays browsable; nothing is
purchasable — no cart, no checkout, no Shopify JavaScript.

## Self-contained

Every product image and both logos are **committed to this repo**
(`assets/`). Nothing loads from `cdn.shopify.com`, so the site keeps working
after the store is closed. The only external requests are Google Fonts
(Inter) and the charity link on the Promise page.

## URL structure

Deliberately mirrors the old Shopify paths, so existing links and search
results keep resolving:

```
/                                     catalogue
/products/<handle>/                   product detail
/pages/the-very-nice-promise/         the Promise
/pages/contact/                       contact
```

## Rebuilding

Product content is generated from `tools/products.json` (captured from the
live store's `/products.json` before it was closed).

```bash
python3 tools/build.py
```

That regenerates every HTML file. Edit copy in `tools/build.py`, styling in
`assets/site.css`.

### Adding a contact email

Set `CONTACT_EMAIL` at the top of `tools/build.py` and re-run the build. While
it's empty the contact page deliberately avoids inviting mail nobody reads.

### If products come back

Flip the wording in `build.py` (`PAUSED_MSG`, the `.badge` / `.status` labels)
or, for a real reopening, point the catalogue at a fresh `products.json`.

## Local preview

```bash
python3 -m http.server 8000
```

Then open http://localhost:8000
