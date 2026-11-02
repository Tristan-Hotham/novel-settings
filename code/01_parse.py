"""Read the Wikidata extracts and build one record per work, per setting place, per work and setting pair, and per author.

Works. A work's year is the year of its earliest publication date (P577); a date before year 1 or after 2026 is kept as
written (BCE years are negative). Title: the English label, else the title of its English Wikipedia article, else empty
(the page shows the Wikidata ID). Sitelinks: links.tsv. A work is a novel if its form of creative work (P7937) is novel or
novella, or if any class it is an instance of (P31) has "novel" in its English label (graphic novel, light novel
series, unfinished novel...), except Wikidata's class for the tales of the Decameron (common.NOVEL_TYPE_EXCLUDE). Genres: P136 English labels, grouped as in common.GENRES.
Places. Coordinates are WKT points. Places whose coordinates are on another globe (the Moon, Mars) are kept apart and
counted; places with no usable coordinates are dropped. Where a place has more than one coordinate the first in file order
is used.
Authors. P50; birthplace coordinates from the author's place of birth (P19). Where an author has more than one birthplace
coordinate, the most frequent (then the first) is used."""
import numpy as np, pandas as pd
from collections import Counter
from common import *

W = read_tsv("works_settings.tsv")
chk = {"rows": len(W), "books_raw": int(W.book.nunique()), "locs_raw": int(W["loc"].nunique()), "authors_raw": int(W.author.replace("", np.nan).nunique()),
       "extract_date": EXTRACT_DATE}
T = {n: read_tsv(f"{n}.tsv") for n in ("type", "genre", "country", "lang", "form", "loccountry", "loctype")}
LK = read_tsv("links.tsv"); EN = read_tsv("enwiki.tsv")
for n, d in T.items():
    chk[f"{n}_rows"] = len(d)

# ---------- coordinates ----------
pt = W.coord.str.extract(r"^POINT\(([-\d.eE]+) ([-\d.eE]+)\)$")
W["lon"] = pd.to_numeric(pt[0], errors="coerce"); W["lat"] = pd.to_numeric(pt[1], errors="coerce")
W["globe"] = W.coord.str.extract(r"entity/(Q\d+)>\s*Point")[0].fillna("")
GLOBES = {"Q405": "the Moon", "Q111": "Mars"}
off = W[W.globe != ""].drop_duplicates(["book", "loc"])
chk["offworld_pairs"] = len(off); chk["offworld_by_globe"] = off.globe.map(lambda g: GLOBES.get(g, g)).value_counts().to_dict()
offworld = [{"book": r.book, "title": r.bookLabel, "loc": r["loc"], "place": r.locLabel, "globe": GLOBES.get(r.globe, r.globe)} for _, r in off.iterrows()]
bad = W[W.lon.isna() & (W.globe == "")]
chk["no_coord_rows"] = len(bad); chk["no_coord_locs"] = sorted(bad.locLabel.unique().tolist())
E = W[W.lon.notna()].copy()
assert E.lat.between(-90, 90).all() and E.lon.between(-180, 180).all()

# ---------- places ----------
LT = T["loctype"].groupby("loc").vLabel.apply(lambda s: sorted(set(x for x in s if x))).to_dict()
LTQ = T["loctype"].groupby("loc").v.apply(lambda s: sorted(set(s))).to_dict()
LC = T["loccountry"].groupby("loc").apply(lambda g: list(dict.fromkeys(zip(g.v, g.vLabel)))).to_dict()
P = E.drop_duplicates("loc")[["loc", "locLabel", "lon", "lat"]].rename(columns={"loc": "q", "locLabel": "label"})
P["types"] = P.q.map(lambda q: LT.get(q, [])); P["tq"] = P.q.map(lambda q: LTQ.get(q, []))
P["wdc"] = P.q.map(lambda q: LC.get(q, []))
multi = E.groupby("loc")[["lon", "lat"]].nunique().max(axis=1)
chk["places_multi_coord"] = int((multi > 1).sum())

# ---------- works ----------
def first_year(s):
    ys = [int(m) for d in s if d for m in [re.match(r"^(-?\d{1,4})-", d)] if m for m in [m.group(1)]]
    return min(ys) if ys else None


g = W.groupby("book")
B = pd.DataFrame({"q": list(g.groups.keys())})
B["label"] = B.q.map(g.bookLabel.first())
B["year"] = B.q.map(g.date.apply(lambda s: first_year(set(s))))
lk = dict(zip(LK.book, pd.to_numeric(LK.n, errors="coerce")))
B["links"] = B.q.map(lambda q: int(lk.get(q, 0) or 0))
enw = dict(zip(EN.book, EN.a.str.strip("<>")))
B["enwiki"] = B.q.map(lambda q: enw.get(q, ""))
B["title"] = [l if l else (re.sub(r"_", " ", __import__("urllib.parse").parse.unquote(u.rsplit("/", 1)[-1])) if u else "") for l, u in zip(B.label, B.enwiki)]
chk["no_english_label"] = int((B.label == "").sum()); chk["no_title_at_all"] = int((B.title == "").sum())
agg = lambda d: d.groupby("book").vLabel.apply(lambda s: sorted(set(x for x in s if x))).to_dict()
aggq = lambda d: d.groupby("book").v.apply(lambda s: sorted(set(s))).to_dict()
for n in ("type", "genre", "country", "lang", "form"):
    m = agg(T[n]); B[n + "s"] = B.q.map(lambda q: m.get(q, []))
mq = aggq(T["country"]); B["origin_q"] = B.q.map(lambda q: mq.get(q, []))
B["novel_form"] = B.forms.map(lambda fs: bool(set(fs) & NOVEL_FORMS))
B["novel_type"] = B.types.map(lambda ts: any(NOVEL_TYPE_RE.search(t) and t not in NOVEL_TYPE_EXCLUDE for t in ts))
B["decameron"] = B.types.map(lambda ts: any(t in NOVEL_TYPE_EXCLUDE for t in ts)) & ~B.novel_form
B["novel"] = (B.novel_form | B.novel_type) & ~B.q.isin(NOT_NOVEL)
assert all(B.loc[B.q == q, "title"].iloc[0] == t for q, t in NOT_NOVEL.items())
for name, rx, _ in GENRES:
    r = re.compile(rx, re.I)
    B["g_" + name] = B.genres.map(lambda gs: any(r.search(x) for x in gs))
chk["decameron_excluded"] = int((B.decameron & ~B.novel_type).sum()); chk["novel_form"] = int(B.novel_form.sum()); chk["novel_type_only"] = int((B.novel_type & ~B.novel_form).sum())
chk["novel_type_only_types"] = Counter(t for ts in B[B.novel_type & ~B.novel_form].types for t in ts if NOVEL_TYPE_RE.search(t)).most_common(12)

# ---------- authors ----------
A = W[W.author.str.match(r"^Q\d+$")].copy()          # blank nodes (author 'unknown value') are not authors
chk["author_rows_unknown"] = int(((W.author != "") & ~W.author.str.match(r"^Q\d+$")).sum())
apt = A.acoord.str.extract(r"^POINT\(([-\d.eE]+) ([-\d.eE]+)\)$")
A["blon"] = pd.to_numeric(apt[0], errors="coerce"); A["blat"] = pd.to_numeric(apt[1], errors="coerce")
au = []
for q, d in A.groupby("author", sort=False):
    c = Counter((round(a, 6), round(b, 6)) for a, b in zip(d.blon, d.blat) if not np.isnan(a))
    best = c.most_common(1)[0][0] if c else (np.nan, np.nan)
    au.append({"q": q, "label": d.authorLabel.iloc[0], "blon": best[0], "blat": best[1], "n_birth_coords": len(c)})
AU = pd.DataFrame(au)
chk["authors"] = len(AU); chk["authors_with_birth"] = int(AU.blon.notna().sum()); chk["authors_multi_birth"] = int((AU.n_birth_coords > 1).sum())
BA = A.groupby("book").author.apply(lambda s: list(dict.fromkeys(s))).to_dict()
B["authors"] = B.q.map(lambda q: BA.get(q, []))

# ---------- pairs (Earth only) ----------
PR = E.drop_duplicates(["book", "loc"])[["book", "loc"]].reset_index(drop=True)
B["n_places"] = B.q.map(PR.groupby("book").size()).fillna(0).astype(int)
B["offworld"] = B.q.isin(off.book)
chk["books_earth"] = int((B.n_places > 0).sum()); chk["books_offworld_only"] = int(((B.n_places == 0) & B.offworld).sum())
chk["books_nothing"] = int(((B.n_places == 0) & ~B.offworld).sum())

B.to_pickle(f"{WORK}/works.pkl"); P.to_pickle(f"{WORK}/places.pkl"); PR.to_pickle(f"{WORK}/pairs.pkl"); AU.to_pickle(f"{WORK}/authors.pkl")
jsave(offworld, f"{WORK}/offworld.json")
jsave(chk, f"{WORK}/checks.json", indent=1)
print({k: v for k, v in chk.items() if not isinstance(v, (list, dict))})
print("novels", int(B.novel.sum()), "works", len(B), "places", len(P), "pairs", len(PR), "offworld", chk["offworld_by_globe"])
