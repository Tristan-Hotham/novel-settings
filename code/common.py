"""Shared paths, groupings and helpers for the novel-settings project.

Raw inputs (read in place, never modified), all in raw/: Wikidata extracts made with QLever on 2026-11-01.
Wikidata is CC0. The population is every item that is an instance of a subclass of "literary work" (Q7725634) and has a
narrative location (P840) whose item has coordinates (P625).
  works_settings.tsv  book, bookLabel, loc, locLabel, coord (WKT POINT(lon lat), or a globe IRI + Point for places on the
                      Moon or Mars), date (P577), author (P50), authorLabel, acoord (coordinates of the author's place of
                      birth), links (sitelinks), lang (P407). One row per combination, so many rows per book.
  type.tsv (P31), genre.tsv (P136), country.tsv (P495 country of origin), lang.tsv (P407), form.tsv (P7937 form of
  creative work), loccountry.tsv (P17 of each location), loctype.tsv (P31 of each location): item, value, English label.
  links.tsv (book, sitelink count) and enwiki.tsv (book, English Wikipedia article URL).
  /home/claude/newdata/raw/geo/ne_50m_admin_0_countries.geojson, ne_10m_admin_0_countries.geojson,
  ne_10m_populated_places_simple.geojson, ne_50m_land.geojson (Natural Earth, public domain)
"""
import json, gzip, os, re, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("NS_RAW", os.path.join(ROOT, "raw"))
GEO = os.environ.get("NS_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("NS_FONTS", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
WORK = os.path.join(os.environ.get("NSTMP", "/dev/shm/novelsettings"), "work")   # intermediates live in memory, not in the repo
for d in (DATA, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "novel-settings"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
DOI = "10.5281/zenodo.23872997"                # filled in by the publisher
BLOG = "https://blog.tristanhotham.com/2026/10/31/novel-settings/"          # filled in by the publisher
EXTRACT_DATE = "2026-11-01"    # QLever extract (not shown in public copy, which uses the year only)
EXTRACT_YEAR = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")

# Novel: form of creative work (P7937) is novel or novella, or any instance-of class whose English label contains "novel"
NOVEL_FORMS = {"novel", "novella"}
NOVEL_TYPE_RE = re.compile(r"novel", re.I)
# Exception: Wikidata types each of the hundred tales of Boccaccio's Decameron as a "novella in the Decameron". They are
# tales inside one book, not novels, so that class alone does not make a work a novel.
NOVEL_TYPE_EXCLUDE = {"novella in the Decameron"}
# One hand correction: Wikidata gives the Odyssey's form as novel. It is an epic poem, so it stays a literary work only.
NOT_NOVEL = {"Q35160": "Odyssey"}

# Genre groups, by regular expression on Wikidata's English genre labels (P136).
GENRES = [
    ("Crime and mystery", r"crime|detective|mystery|noir|police procedural|hardboiled|giallo|whodunit", "#B23A2E"),
    ("Science fiction", r"science fiction|cyberpunk|space opera|dystopi|post-apocalyptic|steampunk|time travel", "#2F5FA7"),
    ("Fantasy", r"fantasy", "#7B57A8"),
    ("Historical", r"\bhistorical (fiction|novel|romance|mystery|drama|crime|fantasy|thriller|adventure)", "#B07A12"),
    ("Horror and gothic", r"horror|gothic", "#3B3B3B"),
    ("Children and young adult", r"children|young adult|juvenile", "#2E9A8C"),
]
GN = [g for g, _, _ in GENRES]
GCOL = {g: c for g, _, c in GENRES}

# Publication eras (year of the earliest publication date, P577)
ERAS = [("Before 1800", -9999, 1799), ("1800 to 1899", 1800, 1899), ("1900 to 1945", 1900, 1945),
        ("1946 to 1999", 1946, 1999), ("2000 on", 2000, 9999)]

# Three cities compared over time (hub ids are Natural Earth place names; see 02_geo.py)
TRIO = [("London", "#C8322B"), ("Paris", "#2F5FA7"), ("New York", "#E0A11B")]

# Continents (Natural Earth CONTINENT of the setting's present-day country)
CONTS = ["Europe", "North America", "Asia", "Africa", "South America", "Oceania", "Antarctica"]
CCOL = {"Europe": "#2F5FA7", "North America": "#C8322B", "Asia": "#E0A11B", "Africa": "#2E9A8C", "South America": "#7B57A8",
        "Oceania": "#D46A8C", "Antarctica": "#8C8478"}


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from text (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def norm(s):
    s = unicodedata.normalize("NFKD", str(s))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "k": return f"{float(v) / 1000:.1f}"
    raise ValueError(f)


def read_tsv(name):
    """QLever TSV: '?col' headers, IRIs in <>, labels as "text"@en. Returns strings with IRIs cut to the Q id."""
    import pandas as pd
    df = pd.read_csv(os.path.join(RAW, name), sep="\t", dtype=str, keep_default_na=False, quoting=3)
    df.columns = [c.lstrip("?") for c in df.columns]
    for c in df.columns:
        s = df[c].str.replace(r"^<http://www\.wikidata\.org/entity/(Q\d+)>$", r"\1", regex=True)
        s = s.str.replace(r'^"(.*)"@[a-z-]+$', r"\1", regex=True).str.replace(r'^"(.*)"\^\^<[^>]*>$', r"\1", regex=True).str.replace(r'^"(.*)"$', r"\1", regex=True)
        df[c] = s.str.replace(r'\\"', '"', regex=True).str.strip()
    return df


def km(lon1, lat1, lon2, lat2):
    """Great-circle distance in km (numpy-friendly)."""
    import numpy as np
    p1, p2, l1, l2 = map(np.radians, (lat1, lat2, lon1, lon2))
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin((l2 - l1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))
