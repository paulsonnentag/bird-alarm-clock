#!/usr/bin/env python3
"""Builds Vogelwecker/Resources/catalog.json.

The catalog only contains metadata + URLs (iNaturalist photos, xeno-canto
recordings). The app downloads the media itself on first launch.

Usage:  XC_API_KEY=... python3 tools/build_catalog.py
"""
import json, os, re, sys, time, urllib.parse, urllib.request

UA = {"User-Agent": "vogelwecker-catalog-builder/1.0 (personal project)"}
XC_KEY = os.environ.get("XC_API_KEY") or sys.exit("XC_API_KEY missing")
OUT = os.path.join(os.path.dirname(__file__), "..", "Vogelwecker", "Resources", "catalog.json")

# (German name, scientific name, habitats) — ordered roughly by how common /
# easy the bird is. New birds are introduced in this order.
BIRDS = [
    ("Amsel", "Turdus merula", ["garten", "wald"]),
    ("Kohlmeise", "Parus major", ["garten", "wald"]),
    ("Rotkehlchen", "Erithacus rubecula", ["garten", "wald"]),
    ("Buchfink", "Fringilla coelebs", ["garten", "wald"]),
    ("Blaumeise", "Cyanistes caeruleus", ["garten", "wald"]),
    ("Haussperling", "Passer domesticus", ["garten"]),
    ("Zaunkönig", "Troglodytes troglodytes", ["garten", "wald"]),
    ("Ringeltaube", "Columba palumbus", ["garten", "feld"]),
    ("Star", "Sturnus vulgaris", ["garten", "feld"]),
    ("Kuckuck", "Cuculus canorus", ["wald", "feld"]),
    ("Zilpzalp", "Phylloscopus collybita", ["garten", "wald"]),
    ("Grünfink", "Chloris chloris", ["garten"]),
    ("Mönchsgrasmücke", "Sylvia atricapilla", ["garten", "wald"]),
    ("Elster", "Pica pica", ["garten", "feld"]),
    ("Rabenkrähe", "Corvus corone", ["garten", "feld"]),
    ("Singdrossel", "Turdus philomelos", ["garten", "wald"]),
    ("Hausrotschwanz", "Phoenicurus ochruros", ["garten"]),
    ("Buntspecht", "Dendrocopos major", ["garten", "wald"]),
    ("Stieglitz", "Carduelis carduelis", ["garten", "feld"]),
    ("Kleiber", "Sitta europaea", ["garten", "wald"]),
    ("Feldlerche", "Alauda arvensis", ["feld"]),
    ("Goldammer", "Emberiza citrinella", ["feld"]),
    ("Eichelhäher", "Garrulus glandarius", ["wald", "garten"]),
    ("Grünspecht", "Picus viridis", ["garten", "wald"]),
    ("Bachstelze", "Motacilla alba", ["garten", "wasser", "feld"]),
    ("Nachtigall", "Luscinia megarhynchos", ["garten", "wald"]),
    ("Türkentaube", "Streptopelia decaocto", ["garten"]),
    ("Fitis", "Phylloscopus trochilus", ["wald"]),
    ("Tannenmeise", "Periparus ater", ["wald", "garten"]),
    ("Schwanzmeise", "Aegithalos caudatus", ["garten", "wald"]),
    ("Gimpel", "Pyrrhula pyrrhula", ["garten", "wald"]),
    ("Feldsperling", "Passer montanus", ["garten", "feld"]),
    ("Mauersegler", "Apus apus", ["garten"]),
    ("Rauchschwalbe", "Hirundo rustica", ["feld", "garten"]),
    ("Gartenrotschwanz", "Phoenicurus phoenicurus", ["garten", "wald"]),
    ("Sumpfmeise", "Poecile palustris", ["wald", "garten"]),
    ("Gartenbaumläufer", "Certhia brachydactyla", ["garten", "wald"]),
    ("Dohle", "Coloeus monedula", ["garten", "feld"]),
    ("Misteldrossel", "Turdus viscivorus", ["wald"]),
    ("Wintergoldhähnchen", "Regulus regulus", ["wald"]),
    ("Girlitz", "Serinus serinus", ["garten"]),
    ("Pirol", "Oriolus oriolus", ["wald"]),
    ("Waldkauz", "Strix aluco", ["wald"]),
    ("Mäusebussard", "Buteo buteo", ["feld", "wald"]),
    ("Stockente", "Anas platyrhynchos", ["wasser"]),
]

OPEN_LICENSES = {"cc0", "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa", "cc-by-nd", "cc-by-nc-nd"}
NEAR = {"Germany", "Austria", "Switzerland", "Netherlands", "Belgium", "Luxembourg", "Denmark",
        "Poland", "Czech Republic", "France", "United Kingdom", "Sweden"}


def get(url):
    for attempt in range(5):
        try:
            return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60))
        except Exception as e:  # rate limits etc.
            print("  retry", attempt, e, file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(url)


def seconds(length):
    parts = [int(p) for p in length.split(":")]
    s = 0
    for p in parts:
        s = s * 60 + p
    return s


def photos_for(sci):
    res = get("https://api.inaturalist.org/v1/taxa?rank=species&per_page=10&q=" + urllib.parse.quote(sci))["results"]
    exact = [t for t in res if t["name"].lower() == sci.lower()]
    taxon = exact[0] if exact else res[0]  # iNat may use a newer name (synonym)
    if not exact:
        print(f"  note: iNaturalist calls {sci} '{taxon['name']}'", file=sys.stderr)
    full = get(f"https://api.inaturalist.org/v1/taxa/{taxon['id']}")["results"][0]
    photos = []
    for tp in full.get("taxon_photos", []):
        p = tp["photo"]
        if p.get("license_code") not in OPEN_LICENSES:
            continue
        url = p.get("medium_url") or p["url"]
        url = re.sub(r"/(square|small|medium|thumb)\.", "/medium.", url)
        photos.append({
            "url": url.replace("/medium.", "/large."),
            "attribution": p.get("attribution", ""),
            "license": p["license_code"],
            "source": f"https://www.inaturalist.org/photos/{p['id']}",
        })
        if len(photos) == 3:
            break
    return taxon["id"], full.get("preferred_common_name") or full.get("english_common_name") or "", photos


def recording_for(sci):
    q = urllib.parse.quote(f'sp:"{sci.lower()}" q:A')
    recs = get(f"https://xeno-canto.org/api/3/recordings?query={q}&per_page=500&key={XC_KEY}")["recordings"]

    def score(r):
        t = r["type"].lower()
        length = seconds(r["length"])
        s = 0
        s += 40 if "song" in t else (20 if "call" in t else 0)
        s += 20 if not r.get("also") or r["also"] == [""] else 0   # no other species in background
        s += 15 if r["cnt"] in NEAR else 0
        s += 15 if 20 <= length <= 75 else (5 if 10 <= length <= 120 else -100)
        s -= 30 if "playback" in (r.get("playback-used") or "").lower() and r["playback-used"].lower() == "yes" else 0
        return s

    recs.sort(key=score, reverse=True)
    r = recs[0]
    lic = r["lic"]
    if lic.startswith("//"):
        lic = "https:" + lic
    return {
        "id": f"XC{r['id']}",
        "url": r["file"],
        "type": r["type"],
        "recordist": r["rec"],
        "country": r["cnt"],
        "license": lic,
        "length": seconds(r["length"]),
        "source": f"https://xeno-canto.org/{r['id']}",
    }


def main():
    out = []
    for de, sci, habitats in BIRDS:
        print(de, file=sys.stderr)
        taxon_id, en, photos = photos_for(sci)
        rec = recording_for(sci)
        if not photos:
            print("  !! no open-licensed photos", file=sys.stderr)
        out.append({
            "id": sci.lower().replace(" ", "-"),
            "scientificName": sci,
            "nameDE": de,
            "nameEN": en,
            "habitats": habitats,
            "inatTaxonId": taxon_id,
            "wikiTitleDE": de,
            "photos": photos,
            "sound": rec,
        })
        time.sleep(1.2)  # be polite to iNaturalist
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump({"version": 1, "birds": out}, f, ensure_ascii=False, indent=1)
    print("wrote", OUT, len(out), "birds", file=sys.stderr)


if __name__ == "__main__":
    main()
