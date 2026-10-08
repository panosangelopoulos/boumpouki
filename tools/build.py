#!/usr/bin/env python3
"""Generate the SEO pages and refresh the <head> of the hand-written pages.

    python3 tools/build.py

Writes evdomades/ (week 4–40 pages + index), exetaseis-egkymosynis.html, ypologismos-pit.html, sitemap.xml
and rewrites the block between <!--seo--> and <!--/seo--> in index/privacy/support (el + en).
tools/weeks.json is a copy of the app's ios/App/Resources/weeks.json; copy it again when the app content changes.
"""
import html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://panosangelopoulos.github.io/boumpouki/"
APP_ID = "6820213082"
APP_URL = f"https://apps.apple.com/gr/app/id{APP_ID}"
LASTMOD = "2026-10-08"
E = html.escape

WEEKS = sorted(json.loads((ROOT / "tools/weeks.json").read_text()), key=lambda w: w["w"])
for _w in WEEKS:
    _w["emoji"] = _w.get("emoji") or "🌱"  # some fruits have no emoji (the app shows an icon instead)

# Same as PrenatalTest.schedule in the app (ios/Shared/Pregnancy.swift).
TESTS = [
    ("Πρώτος υπέρηχος & αιματολογικές", 6, 8, "6η–8η εβδομάδα",
     "Επιβεβαιώνει τη θέση της κύησης, τον καρδιακό παλμό και την ηλικία κύησης. Συνήθως γίνονται και γενική αίματος, ομάδα αίματος & Rhesus, έλεγχος για λοιμώξεις και γενική ούρων."),
    ("Αυχενική διαφάνεια + PAPP-A", 11, 14, "11η–14η εβδομάδα",
     "Υπέρηχος και αιματολογικός έλεγχος (βιοχημικός δείκτης) που εκτιμούν τον κίνδυνο για χρωμοσωμικές ανωμαλίες. Είναι έλεγχος πιθανότητας, όχι διάγνωση."),
    ("Υπέρηχος βʹ επιπέδου", 20, 24, "20η–24η εβδομάδα",
     "Λεπτομερής έλεγχος της ανατομίας του μωρού, του πλακούντα και του αμνιακού υγρού."),
    ("Καμπύλη σακχάρου", 24, 28, "24η–28η εβδομάδα",
     "Έλεγχος για διαβήτη κύησης: αιμοληψία νηστική και μετά την κατανάλωση διαλύματος γλυκόζης. Ρώτα τον γιατρό σου πόσες ώρες νηστείας χρειάζονται."),
    ("Υπέρηχος ανάπτυξης & Doppler", 28, 32, "28η–32η εβδομάδα",
     "Εκτιμά την ανάπτυξη και το βάρος του μωρού, τη θέση του πλακούντα και τη ροή αίματος."),
    ("Καλλιέργεια στρεπτόκοκκου (GBS)", 35, 37, "35η–37η εβδομάδα",
     "Απλή λήψη δείγματος από κόλπο και ορθό. Αν είναι θετική, συνήθως δίνεται αντιβίωση κατά τον τοκετό."),
    ("Καρδιοτοκογράφημα (ΚΤΓ)", 37, 42, "από την 37η εβδομάδα, κάθε εβδομάδα",
     "Καταγράφει τον καρδιακό ρυθμό του μωρού και τις συσπάσεις της μήτρας για περίπου 20–30 λεπτά."),
]

DISCLAIMER = ('<div class="disclaimer"><strong>Ιατρική σημείωση.</strong> Γενικές, ενημερωτικές πληροφορίες· '
              'κάθε εγκυμοσύνη είναι διαφορετική. Δεν είναι ιατρική συμβουλή και δεν αντικαθιστά τον γιατρό ή τη μαία σου. '
              'Για οποιαδήποτε ανησυχία, μίλα με τον γιατρό σου. Σε επείγον, κάλεσε το 166 ή το 112.</div>')

APP_CTA = ('<div class="cta"><img src="{p}icon.png" alt="" width="56" height="56"><div><strong>Όλα αυτά στο iPhone σου</strong>'
           '<p>Το Μπουμπούκι σού δείχνει κάθε μέρα σε ποια εβδομάδα είσαι, τι «χτίζει» το μωρό, ποια εξέταση έρχεται '
           'και ποια χαρτιά θέλει ο e-ΕΦΚΑ. Δωρεάν, χωρίς διαφημίσεις.</p>'
           f'<a class="badge dark" href="{APP_URL}">Κατέβασέ το δωρεάν στο App Store</a></div></div>')


def trimester(w):
    return 1 if w < 14 else 2 if w < 28 else 3


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "</script>"


def breadcrumbs(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": BASE + u} for i, (n, u) in enumerate(items)]}


def seo_block(path, title, desc, lang="el", alt=None, extra=()):
    """Canonical, hreflang, Open Graph, Twitter, Smart App Banner and JSON-LD for one page.
    alt: {"el": path, "en": path} when the page has a translation."""
    url = BASE + path.replace("index.html", "")
    out = [f'<link rel="canonical" href="{url}">']
    if alt:
        for l, p in alt.items():
            out.append(f'<link rel="alternate" hreflang="{l}" href="{BASE + p.replace("index.html", "")}">')
        out.append(f'<link rel="alternate" hreflang="x-default" href="{BASE + alt["el"].replace("index.html", "")}">')
    out += [
        f'<meta name="apple-itunes-app" content="app-id={APP_ID}">',
        '<meta name="theme-color" content="#2F5D4A">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{"Μπουμπούκι" if lang == "el" else "Boumpouki"}">',
        f'<meta property="og:locale" content="{"el_GR" if lang == "el" else "en_US"}">',
        f'<meta property="og:title" content="{E(title)}">',
        f'<meta property="og:description" content="{E(desc)}">',
        f'<meta property="og:url" content="{url}">',
        f'<meta property="og:image" content="{BASE}img/og.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]
    out += [jsonld(x) for x in extra]
    return "<!--seo-->\n" + "\n".join(out) + "\n<!--/seo-->"


def page(path, title, desc, body, extra=(), alt=None):
    depth = path.count("/")
    p = "../" * depth
    return f"""<!doctype html>
<html lang="el">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="icon" href="{p}favicon.png">
<link rel="apple-touch-icon" href="{p}icon.png">
{seo_block(path, title, desc, alt=alt, extra=extra)}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Commissioner:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{p}style.css">
</head>
<body>
<div class="wrap">
<header class="top"><a class="brand" href="{p}index.html"><img src="{p}icon.png" alt="">Μπουμπούκι</a><nav><a href="{p}evdomades/index.html">Εβδομάδες</a><a href="{p}exetaseis-egkymosynis.html">Εξετάσεις</a><a href="{p}ypologismos-pit.html">Υπολογισμός ΠΗΤ</a></nav></header>
<main>
{body}
{APP_CTA.format(p=p)}
</main>
<footer>© 2026 Panagiotis Angelopoulos · <a href="{p}privacy.html">Απόρρητο</a> · <a href="{p}support.html">Υποστήριξη</a><br>Το Μπουμπούκι δίνει γενικές πληροφορίες και δεν αντικαθιστά τον γιατρό ή τη μαία σου.</footer>
</div>
</body>
</html>
"""


def week_page(i, w):
    n = w["w"]
    path = f"evdomades/{n}.html"
    title = f"{n}η εβδομάδα εγκυμοσύνης: μέγεθος μωρού, εξελίξεις, συμπτώματα · Μπουμπούκι"
    desc = (f"{n}η εβδομάδα κύησης: το μωρό έχει το μέγεθος {w['size']} ({w['length']}, {w['weight']}). "
            f"{w['note']}. Τι αλλάζει στο σώμα σου και τι να ρωτήσεις τον γιατρό.")
    tests = [t for t in TESTS if t[1] <= n <= t[2]]
    b = [f'<nav class="crumbs"><a href="../index.html">Αρχική</a> › <a href="index.html">Εβδομάδες</a> › {n}η εβδομάδα</nav>',
         f'<section class="hero week"><span class="emoji" aria-hidden="true">{w["emoji"]}</span>'
         f'<p class="eyebrow">{"ΑΒΓ"[trimester(n) - 1]}ʹ τρίμηνο</p>'
         f'<h1>{n}η εβδομάδα εγκυμοσύνης</h1>'
         f'<p>Το μωρό έχει περίπου το μέγεθος {E(w["size"])}.</p>'
         f'<div class="stats"><div><b>{E(w["length"])}</b><span>μήκος</span></div><div><b>{E(w["weight"])}</b><span>βάρος</span></div>'
         f'<div><b>{40 - n}</b><span>εβδομάδες ως την ΠΗΤ</span></div></div></section>',
         f'<h2>Τι «χτίζει» το μωρό την {n}η εβδομάδα</h2><div class="grid">']
    for x in w["building"]:
        b.append(f'<div class="card"><h3>{E(x["t"])}</h3><p><strong>{E(x["s"])}.</strong> {E(x["d"])}</p></div>')
    b.append("</div>")
    if w.get("done"):
        b.append('<h2>Έχει ήδη ολοκληρωθεί</h2><ul class="chips">' + "".join(f"<li>{E(d)}</li>" for d in w["done"]) + "</ul>")
    if w.get("next"):
        b.append(f'<p><strong>Ακολουθεί:</strong> {E(w["next"]["t"])} ({E(w["next"]["when"])}).</p>')
    if w.get("body"):
        b.append(f'<h2>Το σώμα σου στην {n}η εβδομάδα</h2>')
        b += [f'<div class="card"><h3>{E(x["t"])}</h3><p>{E(x["d"])}</p></div>' for x in w["body"]]
    if tests:
        b.append('<h2>Εξετάσεις αυτή την περίοδο</h2>')
        b += [f'<div class="card"><h3>{E(t[0])} <small>· {t[3]}</small></h3><p>{E(t[4])}</p></div>' for t in tests]
        b.append('<p><a href="../exetaseis-egkymosynis.html">Όλο το πρόγραμμα εξετάσεων εγκυμοσύνης</a></p>')
    if w.get("q"):
        b.append(f'<div class="note"><h3 style="margin-top:0">Ερώτηση για τον γιατρό σου</h3><p>{E(w["q"])}</p></div>')
    if w.get("p"):
        b.append(f'<div class="note"><h3 style="margin-top:0">Για τον/τη σύντροφο</h3><p>{E(w["p"])}</p></div>')
    b.append(DISCLAIMER)
    prev_ = WEEKS[i - 1]["w"] if i > 0 else None
    next_ = WEEKS[i + 1]["w"] if i + 1 < len(WEEKS) else None
    b.append('<nav class="pager">' + (f'<a href="{prev_}.html">← {prev_}η εβδομάδα</a>' if prev_ else "<span></span>")
             + (f'<a href="{next_}.html">{next_}η εβδομάδα →</a>' if next_ else "") + "</nav>")
    extra = [breadcrumbs([("Μπουμπούκι", ""), ("Εβδομάδες", "evdomades/"), (f"{n}η εβδομάδα", path)]),
             {"@context": "https://schema.org", "@type": "MedicalWebPage", "name": title, "description": desc,
              "inLanguage": "el", "url": BASE + path, "dateModified": LASTMOD, "audience": {"@type": "Patient"},
              "about": {"@type": "MedicalCondition", "name": "Εγκυμοσύνη"},
              "isPartOf": {"@type": "WebSite", "name": "Μπουμπούκι", "url": BASE}}]
    return path, page(path, title, desc, "\n".join(b), extra)


def weeks_index():
    path = "evdomades/index.html"
    title = "Εγκυμοσύνη εβδομάδα προς εβδομάδα: από την 4η ως την 40ή εβδομάδα · Μπουμπούκι"
    desc = "Η εγκυμοσύνη εβδομάδα με την εβδομάδα: μέγεθος του μωρού σε φρούτο, μήκος και βάρος, τι αναπτύσσεται, τι αλλάζει στο σώμα σου και ποιες εξετάσεις έρχονται."
    b = ['<nav class="crumbs"><a href="../index.html">Αρχική</a> › Εβδομάδες</nav>',
         '<h1>Η εγκυμοσύνη εβδομάδα προς εβδομάδα</h1>',
         '<p>Διάλεξε εβδομάδα για να δεις τι «χτίζει» το μωρό, πόσο μεγάλο είναι, τι μπορεί να νιώθεις και ποια εξέταση πλησιάζει. '
         'Δεν ξέρεις σε ποια εβδομάδα είσαι; <a href="../ypologismos-pit.html">Υπολόγισέ το εδώ</a>.</p>']
    for t, (a, z) in zip("ΑΒΓ", [(0, 13), (14, 27), (28, 40)]):
        b.append(f'<h2>{t}ʹ τρίμηνο</h2><div class="weeks">')
        b += [f'<a href="{w["w"]}.html"><span aria-hidden="true">{w["emoji"]}</span><b>{w["w"]}η εβδομάδα</b><small>{E(w["fruit"])} · {E(w["note"])}</small></a>'
              for w in WEEKS if a <= w["w"] <= z]
        b.append("</div>")
    b.append(DISCLAIMER)
    extra = [breadcrumbs([("Μπουμπούκι", ""), ("Εβδομάδες", "evdomades/")]),
             {"@context": "https://schema.org", "@type": "ItemList", "itemListElement": [
                 {"@type": "ListItem", "position": k + 1, "url": f"{BASE}evdomades/{w['w']}.html", "name": f"{w['w']}η εβδομάδα εγκυμοσύνης"}
                 for k, w in enumerate(WEEKS)]}]
    return path, page(path, title, desc, "\n".join(b), extra)


def tests_page():
    path = "exetaseis-egkymosynis.html"
    title = "Εξετάσεις εγκυμοσύνης ανά εβδομάδα: το πρόγραμμα στην Ελλάδα · Μπουμπούκι"
    desc = "Ποιες εξετάσεις κάνεις στην εγκυμοσύνη και πότε: πρώτος υπέρηχος, αυχενική διαφάνεια, υπέρηχος βʹ επιπέδου, καμπύλη σακχάρου, υπέρηχος ανάπτυξης, GBS, ΚΤΓ."
    b = ['<nav class="crumbs"><a href="index.html">Αρχική</a> › Εξετάσεις εγκυμοσύνης</nav>',
         '<h1>Εξετάσεις εγκυμοσύνης ανά εβδομάδα</h1>',
         '<p>Το συνηθισμένο πρόγραμμα προγεννητικού ελέγχου στην Ελλάδα, με τις εβδομάδες που γίνεται κάθε εξέταση. '
         'Ο γιατρός σου μπορεί να προσθέσει ή να αλλάξει εξετάσεις ανάλογα με την εγκυμοσύνη σου.</p>',
         '<ol class="timeline">']
    faq = []
    for name, a, z, when, about in TESTS:
        b.append(f'<li><h2>{E(name)}</h2><p class="when">{when}</p><p>{E(about)}</p>'
                 f'<p><a href="evdomades/{a}.html">Τι γίνεται στην {a}η εβδομάδα</a></p></li>')
        faq.append({"@type": "Question", "name": f"Πότε γίνεται: {name};",
                    "acceptedAnswer": {"@type": "Answer", "text": f"Συνήθως {when}. {about}"}})
    b.append("</ol>")
    b.append('<h2>Χαρτιά και επιδόματα</h2><p>Από την 32η εβδομάδα κάνεις αίτηση για το επίδομα μητρότητας στον e-ΕΦΚΑ '
             '(119 ημέρες: 56 πριν και 63 μετά τον τοκετό) με βεβαίωση πιθανής ημερομηνίας τοκετού από τον γιατρό. '
             'Μετά τη γέννηση ακολουθούν ληξιαρχική πράξη, ΑΜΚΑ μωρού και επίδομα γέννησης. Οι διαδικασίες αλλάζουν· '
             'επιβεβαίωσέ τες στο <a href="https://www.gov.gr">gov.gr</a> και στον <a href="https://www.efka.gov.gr">e-ΕΦΚΑ</a>. '
             'Τελευταίος έλεγχος: Οκτώβριος 2026.</p>')
    b.append(DISCLAIMER)
    extra = [breadcrumbs([("Μπουμπούκι", ""), ("Εξετάσεις εγκυμοσύνης", path)]),
             {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq}]
    return path, page(path, title, desc, "\n".join(b), extra)


def calculator_page():
    path = "ypologismos-pit.html"
    title = "Υπολογισμός ΠΗΤ: πιθανή ημερομηνία τοκετού & εβδομάδα κύησης · Μπουμπούκι"
    desc = "Υπολόγισε την πιθανή ημερομηνία τοκετού (ΠΗΤ) από την τελευταία περίοδο και δες σε ποια εβδομάδα εγκυμοσύνης είσαι σήμερα."
    b = ['<nav class="crumbs"><a href="index.html">Αρχική</a> › Υπολογισμός ΠΗΤ</nav>',
         '<h1>Υπολογισμός πιθανής ημερομηνίας τοκετού (ΠΗΤ)</h1>',
         '<p>Βάλε την πρώτη μέρα της τελευταίας σου περιόδου. Η ΠΗΤ είναι αυτή η ημερομηνία συν 280 ημέρες (40 εβδομάδες).</p>',
         '<form class="calc" onsubmit="return false"><label for="lmp">Πρώτη μέρα τελευταίας περιόδου</label>'
         '<input type="date" id="lmp" required><div id="out" aria-live="polite"></div></form>',
         '<h2>Πώς υπολογίζεται</h2><p>Ο υπολογισμός ακολουθεί τον κανόνα του Naegele: πρώτη μέρα τελευταίας περιόδου + 280 ημέρες, '
         'για κύκλο περίπου 28 ημερών. Η εβδομάδα κύησης μετρά τις ολοκληρωμένες εβδομάδες από την τελευταία περίοδο, '
         'άρα τις πρώτες δύο εβδομάδες δεν είσαι ακόμα έγκυος. Αν ο γιατρός σου διόρθωσε την ΠΗΤ με τον πρώτο υπέρηχο, '
         'ισχύει εκείνη. Μόνο περίπου 1 στα 20 μωρά γεννιέται ακριβώς την ΠΗΤ.</p>',
         DISCLAIMER,
         """<script>
(function(){
var i=document.getElementById('lmp'),o=document.getElementById('out'),D=864e5;
var f=new Intl.DateTimeFormat('el-GR',{weekday:'long',day:'numeric',month:'long',year:'numeric'});
function go(){
  if(!i.value){o.innerHTML='';return}
  var p=i.value.split('-'),l=Date.UTC(+p[0],p[1]-1,+p[2]),n=new Date(),t=Date.UTC(n.getFullYear(),n.getMonth(),n.getDate());
  var due=new Date(l+280*D),days=Math.round((t-l)/D),w=Math.floor(days/7),d=days%7;
  var h='<p class="big">ΠΗΤ: <b>'+f.format(due)+'</b></p>';
  if(days<0)h+='<p>Η ημερομηνία είναι στο μέλλον.</p>';
  else if(days>300)h+='<p>Η ημερομηνία είναι πάνω από 42 εβδομάδες πριν.</p>';
  else{h+='<p>Σήμερα: <b>'+w+'η εβδομάδα και '+d+' '+(d==1?'ημέρα':'ημέρες')+'</b> · '+(w<14?'Αʹ':w<28?'Βʹ':'Γʹ')+' τρίμηνο · '+Math.max(0,280-days)+' ημέρες ως την ΠΗΤ.</p>';
    var c=Math.min(Math.max(w,4),40);h+='<p><a href="evdomades/'+c+'.html">Τι γίνεται στην '+c+'η εβδομάδα →</a></p>';}
  o.innerHTML=h;
}
i.addEventListener('input',go);i.max=new Date().toISOString().slice(0,10);
})();
</script>"""]
    extra = [breadcrumbs([("Μπουμπούκι", ""), ("Υπολογισμός ΠΗΤ", path)]),
             {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                 {"@type": "Question", "name": "Πώς υπολογίζεται η πιθανή ημερομηνία τοκετού;",
                  "acceptedAnswer": {"@type": "Answer", "text": "Πρώτη μέρα της τελευταίας περιόδου + 280 ημέρες (40 εβδομάδες), για κύκλο περίπου 28 ημερών. Αν ο γιατρός διόρθωσε την ΠΗΤ με υπέρηχο, ισχύει εκείνη."}},
                 {"@type": "Question", "name": "Σε ποια εβδομάδα εγκυμοσύνης είμαι;",
                  "acceptedAnswer": {"@type": "Answer", "text": "Μέτρησε τις ολοκληρωμένες εβδομάδες από την πρώτη μέρα της τελευταίας περιόδου. Για παράδειγμα, 170 ημέρες είναι 24 εβδομάδες και 2 ημέρες."}}]}]
    return path, page(path, title, desc, "\n".join(b), extra)


# Hand-written pages: (path, translation pair, title, description, extra JSON-LD)
APP_LD = {"@context": "https://schema.org", "@type": "MobileApplication", "name": "Μπουμπούκι",
          "alternateName": ["Boumpouki", "Μπουμπούκι: Εγκυμοσύνη"], "operatingSystem": "iOS 17 ή νεότερο",
          "applicationCategory": "HealthApplication", "inLanguage": "el", "url": BASE,
          "image": BASE + "icon.png", "screenshot": [BASE + f"img/{n}.jpg" for n in ("01-today", "02-week", "03-checkups")],
          "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}, "installUrl": APP_URL, "sameAs": [APP_URL],
          "author": {"@type": "Person", "name": "Panagiotis Angelopoulos"},
          "description": "Ελληνική εφαρμογή εγκυμοσύνης για iPhone: εβδομάδα με την εβδομάδα, εξετάσεις κύησης, χαρτιά e-ΕΦΚΑ, μετρητής κινήσεων και συσπάσεων. Δωρεάν, χωρίς διαφημίσεις."}
SITE_LD = {"@context": "https://schema.org", "@type": "WebSite", "name": "Μπουμπούκι", "url": BASE, "inLanguage": ["el", "en"]}
HAND = [
    ("index.html", {"el": "index.html", "en": "en/index.html"},
     "Μπουμπούκι · Εφαρμογή εγκυμοσύνης στα ελληνικά, εβδομάδα με την εβδομάδα",
     "Ελληνική εφαρμογή εγκυμοσύνης για iPhone: τι «χτίζει» το μωρό κάθε εβδομάδα, εξετάσεις κύησης, χαρτιά e-ΕΦΚΑ, μετρητής κινήσεων και συσπάσεων. Δωρεάν, χωρίς διαφημίσεις και tracking.",
     [APP_LD, SITE_LD]),
    ("en/index.html", {"el": "index.html", "en": "en/index.html"},
     "Boumpouki · Greek pregnancy app, week by week",
     "A calm, private, Greek-language pregnancy app for iPhone: week by week, Greek prenatal tests, e-EFKA paperwork, kick counter and contraction timer. Free, no ads, no tracking.",
     [dict(APP_LD, inLanguage="el", operatingSystem="iOS 17 or later", description="Greek-language pregnancy companion for iPhone: week by week, Greek prenatal test schedule, e-EFKA paperwork, kick counter and contraction timer. Free, no ads.")]),
    ("privacy.html", {"el": "privacy.html", "en": "en/privacy.html"}, None, None, []),
    ("en/privacy.html", {"el": "privacy.html", "en": "en/privacy.html"}, None, None, []),
    ("support.html", {"el": "support.html", "en": "en/support.html"}, None, None, []),
    ("en/support.html", {"el": "support.html", "en": "en/support.html"}, None, None, []),
]


def faq_from_details(src):
    qa = re.findall(r"<details><summary>(.*?)</summary>(.*?)</details>", src, re.S)
    strip = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()
    return {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": strip(q), "acceptedAnswer": {"@type": "Answer", "text": strip(a)}} for q, a in qa]} if qa else None


def refresh_hand(path, alt, title, desc, extra):
    f = ROOT / path
    s = f.read_text()
    if title:
        s = re.sub(r"<title>.*?</title>", f"<title>{E(title)}</title>", s, 1)
        s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{E(desc)}">', s, 1)
    t = html.unescape(re.search(r"<title>(.*?)</title>", s).group(1))
    d = html.unescape(re.search(r'<meta name="description" content="([^"]*)">', s).group(1))
    if "support" in path and (faq := faq_from_details(s)):
        extra = extra + [faq]
    block = seo_block(path, t, d, "en" if path.startswith("en/") else "el", alt, extra)
    if "<!--seo-->" in s:
        s = re.sub(r"<!--seo-->.*?<!--/seo-->", lambda _: block, s, 1, re.S)
    else:
        s = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">', lambda _: block, s, 1)
    f.write_text(s)


def main():
    pages = [weeks_index(), tests_page(), calculator_page()] + [week_page(i, w) for i, w in enumerate(WEEKS)]
    (ROOT / "evdomades").mkdir(exist_ok=True)
    for path, text in pages:
        (ROOT / path).write_text(text)
    for h in HAND:
        refresh_hand(*h)
    urls = [("", "1.0"), ("en/", "0.6"), ("evdomades/", "0.9"), ("exetaseis-egkymosynis.html", "0.8"),
            ("ypologismos-pit.html", "0.8")] + [(f"evdomades/{w['w']}.html", "0.7") for w in WEEKS] + \
           [("support.html", "0.3"), ("en/support.html", "0.2"), ("privacy.html", "0.2"), ("en/privacy.html", "0.2")]
    (ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"<url><loc>{BASE}{u}</loc><lastmod>{LASTMOD}</lastmod><priority>{p}</priority></url>\n" for u, p in urls)
        + "</urlset>\n")
    print(f"{len(pages)} generated pages, {len(HAND)} refreshed, {len(urls)} sitemap URLs")


if __name__ == "__main__":
    main()
