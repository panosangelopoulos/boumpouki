# Μπουμπούκι website

Static site for the Μπουμπούκι iOS app (landing, privacy, support; Greek + English), served by GitHub Pages at https://panosangelopoulos.github.io/boumpouki/.

## SEO pages

`python3 tools/build.py` generates the week pages (`evdomades/4.html`–`40.html` + index), `exetaseis-egkymosynis.html`,
`ypologismos-pit.html` and `sitemap.xml`, and rewrites the `<!--seo-->` block (canonical, hreflang, Open Graph,
Smart App Banner, JSON-LD) in the hand-written pages. Week content comes from `tools/weeks.json`, a copy of the app's
`ios/App/Resources/weeks.json`. Re-run after editing either. `img/og.png` is the 1200×630 share image.
