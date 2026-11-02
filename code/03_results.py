"""Every number used anywhere (data/results.json), the reusable data tables (data/*.csv) and the page data
(data/site.json, embedded; data/points.json, loaded by the page).

Definitions (see 01_parse.py and 02_geo.py):
  * work: a Wikidata literary work with at least one narrative location on Earth with coordinates;
  * novel: form novel or novella, or a class with 'novel' in its label;
  * setting: a work and place pair. 'Set in' a city, country or continent means at least one of the work's places is there;
  * point settings: places at city, site or region level (countries, continents and oceans are never points);
  * city: a city area (02_geo.py: places within 25 km of a Natural Earth city of 250,000+ grouped with it);
  * year: earliest publication year; decade = year rounded down to ten;
  * home and abroad: a novel is set at home if every one of its places with a country lies in the present-day country
    where one of its authors was born; abroad if at least one place lies outside all its authors' birth countries.
    Places at sea or with no country are left out of this test;
  * distance: great-circle km from a point setting to the nearest of the work's authors' birthplaces;
  * population: Natural Earth POP_EST (about 2019 to 2020)."""
import numpy as np, pandas as pd
from collections import Counter, defaultdict
from common import *

B = pd.read_pickle(f"{WORK}/works.pkl")
P = pd.read_pickle(f"{WORK}/places_geo.pkl").set_index("q", drop=False)
PR = pd.read_pickle(f"{WORK}/pairs.pkl")
AU = pd.read_pickle(f"{WORK}/authors_geo.pkl").set_index("q", drop=False)
CM = jload(f"{WORK}/countries.json"); HUBS = jload(f"{WORK}/hubs.json"); CHK = jload(f"{WORK}/checks.json"); OFF = jload(f"{WORK}/offworld.json")
cname = lambda i: CM.get(i, {}).get("name", i) if i else "no country"
pc = lambda a, b: round(100 * a / b, 2) if b else None
R = {}

B = B.set_index("q", drop=False)
E = B[B.n_places > 0].copy()                       # works with an Earth setting
NOV = set(E[E.novel].q)
for c in ("level", "iso", "hub", "cont", "fictional", "lon", "lat", "label", "remote_km", "types"):
    PR[c] = PR["loc"].map(P[c])
PR["novel"] = PR.book.isin(NOV)
PR["point"] = PR.level.isin(["city", "site", "region"])
PR["year"] = PR.book.map(B.year)

# ---------- source ----------
R["source"] = {"rows": CHK["rows"], "works_all": CHK["books_raw"], "works": len(E), "novels": len(NOV), "other": len(E) - len(NOV),
               "novel_form": CHK["novel_form"], "novel_type_only": CHK["novel_type_only"], "decameron": CHK["decameron_excluded"],
               "places": int(PR["loc"].nunique()), "places_novels": int(PR[PR.novel]["loc"].nunique()),
               "pairs": len(PR), "pairs_novels": int(PR.novel.sum()),
               "authors": CHK["authors"], "authors_birth": CHK["authors_with_birth"],
               "no_english_label": CHK["no_english_label"], "no_title": CHK["no_title_at_all"],
               "offworld_pairs": CHK["offworld_pairs"], "offworld_only": CHK["books_offworld_only"],
               "extract_year": EXTRACT_YEAR, "with_year": int(E.year.notna().sum()), "novels_with_year": int(E[E.novel].year.notna().sum()),
               "novels_with_author": int(E[E.novel].authors.map(len).gt(0).sum()),
               "places_per_work": round(len(PR) / len(E), 2), "places_per_novel": round(PR.novel.sum() / len(NOV), 2),
               "fictional_places": int(P.fictional.sum())}
lv = PR.drop_duplicates("loc").level.value_counts()
R["levels"] = {"places": {k: int(lv.get(k, 0)) for k in ("city", "site", "region", "country", "large")},
               "novel_pairs": {k: int(((PR.level == k) & PR.novel).sum()) for k in ("city", "site", "region", "country", "large")}}
R["levels"]["novels_with_point"] = int(PR[PR.novel & PR.point].book.nunique())
R["levels"]["novels_with_point_pct"] = pc(R["levels"]["novels_with_point"], len(NOV))
R["levels"]["novels_country_only"] = len(NOV) - R["levels"]["novels_with_point"]
fm = Counter(f for fs in E[~E.novel].forms for f in fs)
R["other_forms"] = [[k, int(v)] for k, v in fm.most_common(8)]
R["other_no_form"] = int((E[~E.novel].forms.map(len) == 0).sum())
s = R["source"]
assert s["works"] == 13218 and s["novels"] > 7000

# ---------- cities ----------
def hub_counts(mask):
    d = PR[mask & PR.hub.notna()].drop_duplicates(["book", "hub"])
    return d.groupby("hub").book.nunique().sort_values(ascending=False)


hn, ha = hub_counts(PR.novel), hub_counts(pd.Series(True, index=PR.index))
def hubrow(h, n):
    H = HUBS[h]; return {"hub": h, "name": H["name"], "iso": H["iso"], "country": cname(H["iso"]), "n": int(n), "all": int(ha.get(h, 0)),
                         "lon": round(H["lon"], 3), "lat": round(H["lat"], 3)}
R["cities"] = [hubrow(h, n) for h, n in hn.head(30).items()]
R["cities_all"] = [hubrow(h, ha[h]) | {"n": int(hn.get(h, 0))} for h in ha.head(30).index]
C = {r["name"]: r for r in R["cities"]}
R["n_cities"] = int(hn.size)
nov_point = R["levels"]["novels_with_point"]
for k in ("London", "Paris", "New York City"):
    C[k]["pct"] = pc(C[k]["n"], len(NOV))
R["city_top3_pct"] = pc(PR[PR.novel & PR.hub.isin([C[k]["hub"] for k in ("London", "Paris", "New York City")])].book.nunique(), len(NOV))
assert [r["name"] for r in R["cities"][:3]] and {"London", "Paris", "New York City"} <= {r["name"] for r in R["cities"][:4]}
# the most used single places (not grouped)
pn = PR[PR.novel].groupby("loc").book.nunique().sort_values(ascending=False)
R["places_top"] = [{"q": q, "label": P.at[q, "label"], "level": P.at[q, "level"], "n": int(n)} for q, n in pn.head(25).items()]

# ---------- countries ----------
def cn(mask):
    d = PR[mask & PR.iso.notna()].drop_duplicates(["book", "iso"]); return d.groupby("iso").book.nunique().sort_values(ascending=False)


cnv, cal = cn(PR.novel), cn(pd.Series(True, index=PR.index))
R["countries"] = [{"iso": i, "name": cname(i), "n": int(n), "all": int(cal.get(i, 0)), "pop_m": round(CM[i]["pop"] / 1e6, 2),
                   "per_m": round(n / (CM[i]["pop"] / 1e6), 2) if CM[i]["pop"] > 0 else None, "cont": CM[i]["cont"]} for i, n in cnv.items()]
R["n_countries"] = len(R["countries"])
R["countries_all"] = [{"iso": i, "name": cname(i), "n": int(n), "nov": int(cnv.get(i, 0))} for i, n in cal.head(30).items()]
CT = {r["iso"]: r for r in R["countries"]}
for i in ("USA", "GBR", "FRA", "ITA", "DEU", "IND", "CHN", "NGA", "DNK", "SRB", "RUS", "ESP", "JPN"):
    if i in CT: CT[i]["pct"] = pc(CT[i]["n"], len(NOV))
R["country"] = {i: CT[i] for i in CT}
R["usa_gbr_pct"] = pc(PR[PR.novel & PR.iso.isin(["USA", "GBR"])].book.nunique(), len(NOV))
R["countries_with_novel"] = len(cnv); R["countries_total"] = len([k for k in CM if CM[k]["pop"] > 0])
R["countries_none"] = sorted([CM[k]["name"] for k in CM if k not in cnv and CM[k]["pop"] >= 1e7])
R["countries_none_n10m"] = len(R["countries_none"])

# ---------- coverage bias: whole literary population ----------
pl = PR.drop_duplicates("loc")
tot_pl = len(pl); tot_pairs = len(PR); world_pop = sum(v["pop"] for v in CM.values())
bias = []
for i, g in pl.groupby("iso"):
    pp_ = PR[PR.iso == i]
    bias.append({"iso": i, "name": cname(i), "places": len(g), "places_pct": pc(len(g), tot_pl), "pairs": len(pp_), "works": int(pp_.book.nunique()),
                 "novels": int(pp_[pp_.novel].book.nunique()), "pop_pct": round(100 * CM[i]["pop"] / world_pop, 3),
                 "places_per_m": round(len(g) / (CM[i]["pop"] / 1e6), 1) if CM[i]["pop"] > 1e5 else None,
                 "sites": int((g.level == "site").sum()), "streets": int(g.types.map(lambda t: any(re.search(r"street|square|road|avenue|boulevard", x, re.I) for x in t)).sum())})
BI = pd.DataFrame(bias).sort_values("places", ascending=False)
BI.to_csv(f"{DATA}/coverage_by_country.csv", index=False)
R["bias_top"] = BI.head(15).to_dict("records")
BD = BI.set_index("iso")
R["bias"] = {i: BD.loc[i].to_dict() | {"iso": i} for i in ("DNK", "SRB", "USA", "FRA", "GBR", "DEU", "ITA", "CHN", "IND", "NGA", "IDN", "BRA", "PAK") if i in BD.index}
dpm = BI[BI.places_per_m.notna() & (BI.places >= 20)].sort_values("places_per_m", ascending=False)
R["bias_per_m"] = dpm.head(10)[["iso", "name", "places", "places_per_m"]].to_dict("records")
b = R["bias"]
b["dnk_vs"] = {"chn_ind_places": int(b["CHN"]["places"] + b["IND"]["places"]), "dnk_places": int(b["DNK"]["places"]),
               "dnk_x_pop": round(b["DNK"]["places_pct"] / b["DNK"]["pop_pct"], 1), "srb_x_pop": round(b["SRB"]["places_pct"] / b["SRB"]["pop_pct"], 1),
               "dnk_srb_places_pct": round(b["DNK"]["places_pct"] + b["SRB"]["places_pct"], 1)}
# by language of the work: places per work
LANGW = E.langs.explode().dropna()
lp = []
for lang in ("English", "French", "Italian", "German", "Spanish", "Russian", "Danish", "Serbian", "Swedish", "Japanese"):
    ws = set(LANGW[LANGW == lang].index)
    d = PR[PR.book.isin(ws)]
    lp.append({"lang": lang, "works": len(ws), "pairs": len(d), "places": int(d["loc"].nunique()), "per_work": round(len(d) / len(ws), 2) if ws else None})
R["bias_lang"] = lp
LP = {r["lang"]: r for r in lp}
dk_works = set(LANGW[LANGW == "Danish"].index)
d = PR[PR.book.isin(dk_works)]
R["danish"] = {"works": len(dk_works), "places": int(d["loc"].nunique()), "places_in_dnk": int(d[d.iso == "DNK"]["loc"].nunique()),
               "top_work": None, "top_work_places": None}
tw = d.groupby("book").size().sort_values(ascending=False)
R["danish"]["top_work"] = B.at[tw.index[0], "title"] or tw.index[0]; R["danish"]["top_work_places"] = int(tw.iloc[0]); R["danish"]["top_work_year"] = B.at[tw.index[0], "year"]
R["danish"]["dnk_places_from_danish_pct"] = pc(R["danish"]["places_in_dnk"], b["DNK"]["places"])
sr_works = set(LANGW[LANGW == "Serbian"].index); d = PR[PR.book.isin(sr_works)]
R["serbian"] = {"works": len(sr_works), "places": int(d["loc"].nunique()), "novels": len(sr_works & NOV),
                "years": [int(E.loc[list(sr_works)].year.min()), int(E.loc[list(sr_works)].year.quantile(.9))]}
sy = E.loc[list(sr_works)].year.dropna(); R["serbian"]["pre1930_pct"] = pc((sy < 1930).sum(), len(sy))
R["serbian"]["srb_places_from_serbian_pct"] = pc(PR[PR.book.isin(sr_works) & (PR.iso == "SRB")]["loc"].nunique(), b["SRB"]["places"])
# the most places per work
mp = PR.groupby("book").size().sort_values(ascending=False)
R["most_places"] = [{"title": B.at[q, "title"] or q, "q": q, "n": int(n), "year": None if pd.isna(B.at[q, "year"]) else int(B.at[q, "year"]), "langs": B.at[q, "langs"]} for q, n in mp.head(8).items()]

# ---------- London, Paris, New York by decade ----------
TRIOH = {"London": "London|GBR", "Paris": "Paris|FRA", "New York": "New York|USA"}
nd = PR[PR.novel & PR.point & PR.year.notna()].copy(); nd["dec"] = (nd.year // 10 * 10).astype(int)
trio = []
for dec in range(1800, 2030, 10):
    a = nd[nd.dec == dec]; den = a.book.nunique()
    row = {"dec": dec, "n": int(den)}
    for k, h in TRIOH.items():
        row[k] = int(a[a.hub == h].book.nunique()); row[k + "_pct"] = pc(row[k], den)
    trio.append(row)
R["trio"] = trio
t20 = []
for a in range(1830, 2030, 20):
    x = nd[(nd.dec >= a) & (nd.dec < a + 20)]; den = x.book.nunique(); row = {"from": a, "to": min(a + 19, 2026), "n": int(den)}
    for k, h in TRIOH.items():
        row[k] = int(x[x.hub == h].book.nunique()); row[k + "_pct"] = pc(row[k], den)
    t20.append(row)
R["trio20"] = t20
TD = {t["dec"]: t for t in trio}
def era_share(k, a, z):
    a_ = nd[(nd.dec >= a) & (nd.dec <= z)]; return pc(a_[a_.hub == TRIOH[k]].book.nunique(), a_.book.nunique())
R["trio_eras"] = {f"{k}_{a}": era_share(k, a, z) for k in TRIOH for a, z in ((1800, 1899), (1900, 1949), (1950, 1999), (2000, 2029))}
R["trio_eras"]["n_1800"] = int(nd[(nd.dec >= 1800) & (nd.dec <= 1899)].book.nunique())
R["trio_eras"]["n_2000"] = int(nd[nd.dec >= 2000].book.nunique())
ny_lead = [t["dec"] for t in trio if t["n"] >= 40 and t["New York"] > t["London"] and t["New York"] > t["Paris"]]
R["trio_ny_first_lead"] = ny_lead[0] if ny_lead else None
R["trio_ny_lead_decs"] = ny_lead
R["trio_london_lead_decs"] = [t["dec"] for t in trio if t["n"] >= 40 and t["London"] >= max(t["Paris"], t["New York"])]
R["trio_paris_lead_decs"] = [t["dec"] for t in trio if t["n"] >= 40 and t["Paris"] > max(t["London"], t["New York"])]
pd.DataFrame(trio).to_csv(f"{DATA}/london_paris_newyork_by_decade.csv", index=False)

# ---------- home and abroad ----------
abroad, dists = [], []
for q in NOV:
    w = B.loc[q]; au = [a for a in w.authors if a in AU.index and isinstance(AU.at[a, "biso"], str)]
    if not au: continue
    bis = {AU.at[a, "biso"] for a in au}
    pp_ = PR[(PR.book == q)]
    isos = [i for i in pp_.iso if isinstance(i, str)]
    if not isos: continue
    out = [i for i in isos if i not in bis]
    abroad.append({"q": q, "abroad": int(bool(out)), "home_any": int(len(out) < len(isos)), "biso": sorted(bis)[0], "n_bis": len(bis), "year": w.year,
                   "set_isos": sorted(set(isos))})
    for r in pp_[pp_.point & ~pp_.fictional].itertuples():
        d = min(float(km(AU.at[a, "blon"], AU.at[a, "blat"], r.lon, r.lat)) for a in au)
        a0 = min(au, key=lambda a: float(km(AU.at[a, "blon"], AU.at[a, "blat"], r.lon, r.lat)))
        dists.append({"q": q, "loc": r.loc, "km": d, "author": a0, "biso": AU.at[a0, "biso"], "iso": r.iso, "year": w.year})
AB = pd.DataFrame(abroad); DI = pd.DataFrame(dists)
R["home"] = {"n": len(AB), "abroad": int(AB.abroad.sum()), "abroad_pct": pc(AB.abroad.sum(), len(AB)), "home_pct": pc((AB.abroad == 0).sum(), len(AB)),
             "mixed": int(((AB.abroad == 1) & (AB.home_any == 1)).sum()), "only_abroad": int(((AB.abroad == 1) & (AB.home_any == 0)).sum()),
             "pairs": len(DI), "median_km": round(float(DI.km.median())), "mean_km": round(float(DI.km.mean())),
             "within_50": pc((DI.km <= 50).sum(), len(DI)), "within_500": pc((DI.km <= 500).sum(), len(DI)), "over_5000": pc((DI.km > 5000).sum(), len(DI)),
             "over_10000": int((DI.km > 10000).sum())}
R["home"]["only_abroad_pct"] = pc(R["home"]["only_abroad"], len(AB))
# by decade of publication
AB["dec"] = (AB.year // 10 * 10)
hd = []
for a, z, lab in ((1800, 1849, "1800 to 1849"), (1850, 1899, "1850 to 1899"), (1900, 1949, "1900 to 1949"), (1950, 1999, "1950 to 1999"), (2000, 2029, "2000 on")):
    x = AB[(AB.year >= a) & (AB.year <= z)]; dd = DI[(DI.year >= a) & (DI.year <= z)]
    hd.append({"era": lab, "n": len(x), "abroad_pct": pc(x.abroad.sum(), len(x)), "median_km": round(float(dd.km.median())) if len(dd) else None})
R["home_eras"] = hd
# by birth country
bc = []
for i, g in AB.groupby("biso"):
    if len(g) < 40: continue
    dd = DI[DI.biso == i]
    bc.append({"iso": i, "name": cname(i), "n": len(g), "abroad_pct": pc(g.abroad.sum(), len(g)), "median_km": round(float(dd.km.median())) if len(dd) else None,
               "top_abroad": [[cname(k), int(v)] for k, v in Counter(x for s_ in g[g.abroad == 1].set_isos for x in s_ if x != i).most_common(3)]})
BC = sorted(bc, key=lambda r: -r["abroad_pct"])
R["home_by_country"] = BC
HB = {r["iso"]: r for r in BC}
R["home_country"] = HB
pd.DataFrame(BC).drop(columns=["top_abroad"]).to_csv(f"{DATA}/home_abroad_by_birth_country.csv", index=False)
# farthest single journeys
fz = DI.sort_values("km", ascending=False).drop_duplicates("q").head(10)
R["farthest"] = [{"title": B.at[r.q, "title"] or r.q, "q": r.q, "km": round(r.km), "author": AU.at[r.author, "label"], "place": P.at[r.loc, "label"],
                  "place_country": cname(r.iso), "born": cname(r.biso), "year": None if pd.isna(r.year) else int(r.year)} for r in fz.itertuples()]
# authors who travel furthest: at least 3 novels with a located point setting
ag = DI.groupby("author").agg(n=("q", "nunique"), pairs=("km", "size"), med=("km", "median"), mx=("km", "max")).reset_index()
ag = ag[ag.n >= 3].sort_values("med", ascending=False)
R["authors_far"] = [{"author": AU.at[r.author, "label"], "q": r.author, "novels": int(r.n), "median_km": round(r.med), "born": cname(AU.at[r.author, "biso"])} for r in ag.head(12).itertuples()]
R["authors_near"] = [{"author": AU.at[r.author, "label"], "novels": int(r.n), "median_km": round(r.med), "born": cname(AU.at[r.author, "biso"])} for r in ag.sort_values(["med", "n"], ascending=[True, False]).head(8).itertuples()]
R["authors_far_n"] = len(ag)
# the most prolific authors on the map
an = Counter(a for q in NOV for a in B.at[q, "authors"])
R["authors_top"] = [{"author": AU.at[a, "label"], "q": a, "novels": int(n)} for a, n in an.most_common(12)]

# ---------- genres ----------
gr = []
for g_ in GN:
    ws = set(E[E.novel & E["g_" + g_]].q)
    d = PR[PR.book.isin(ws)]
    hc = d[d.hub.notna()].drop_duplicates(["book", "hub"]).groupby("hub").book.nunique().sort_values(ascending=False)
    cc = d[d.iso.notna()].drop_duplicates(["book", "iso"]).groupby("iso").book.nunique().sort_values(ascending=False)
    lift = []
    for h, n in hc.items():
        if n >= 8:
            lift.append((h, n, round((n / len(ws)) / (hn.get(h, 0) / len(NOV)), 2)))
    gr.append({"genre": g_, "n": len(ws), "pct": pc(len(ws), len(NOV)), "cities": [[HUBS[h]["name"], int(n)] for h, n in hc.head(8).items()],
               "countries": [[cname(i), int(n)] for i, n in cc.head(8).items()],
               "lift": [[HUBS[h]["name"], int(n), l] for h, n, l in sorted(lift, key=lambda x: -x[2])[:6]],
               "usa_pct": pc(cc.get("USA", 0), len(ws)), "gbr_pct": pc(cc.get("GBR", 0), len(ws)),
               "point_pct": pc(d[d.point].book.nunique(), len(ws)), "large_pct": pc(d[d.level.isin(["large", "country"])].book.nunique(), len(ws))})
R["genres"] = {g["genre"]: g for g in gr}; R["genres_list"] = gr
cr = R["genres"]["Crime and mystery"]
R["crime_top"] = cr["cities"][:5]
# historical fiction: publication year
hist = E[E.novel & E["g_Historical"]]
R["genres"]["Historical"]["median_year"] = int(hist.year.median())
R["genres"]["Historical"]["ancient"] = int(PR[PR.book.isin(hist.q) & PR["loc"].isin(P[P.types.map(lambda t: any(re.search(r"ancient|historical period|Roman province|civilization|polis", x, re.I) for x in t))].q)].book.nunique())

# ---------- continents ----------
ct = []
nov_c = PR[PR.novel & PR.cont.notna()].drop_duplicates(["book", "cont"])
all_c = PR[PR.cont.notna()].drop_duplicates(["book", "cont"])
den_n = nov_c.book.nunique(); den_a = all_c.book.nunique()
cpop = defaultdict(float)
for k, v in CM.items():
    if v["cont"] in CONTS: cpop[v["cont"]] += v["pop"]
wp = sum(cpop.values())
for c_ in CONTS:
    n = int(nov_c[nov_c.cont == c_].book.nunique()); a = int(all_c[all_c.cont == c_].book.nunique())
    ct.append({"cont": c_, "novels": n, "novels_pct": pc(n, den_n), "works": a, "works_pct": pc(a, den_a), "pop_pct": round(100 * cpop[c_] / wp, 2),
               "per_10m": round(n / (cpop[c_] / 1e7), 1) if cpop[c_] > 1e6 else None,
               "ratio": round((n / den_n) / (cpop[c_] / wp), 2) if cpop[c_] > 1e6 else None})
R["continents"] = {r["cont"]: r for r in ct}; R["continents_list"] = ct; R["continents_den"] = den_n
CO = R["continents"]
R["cont_eur_vs_asia"] = round(CO["Europe"]["per_10m"] / CO["Asia"]["per_10m"], 1)
R["cont_na_vs_africa"] = round(CO["North America"]["per_10m"] / CO["Africa"]["per_10m"], 1)
pd.DataFrame(ct).to_csv(f"{DATA}/continents.csv", index=False)
# under-mapped big countries: fewest novels per 10 million people, population 50 million or more
um = [r for r in R["countries"] if r["pop_m"] >= 50]
for r in um: r["per_10m"] = round(r["n"] / r["pop_m"] * 10, 2)
R["undermapped"] = sorted(um, key=lambda r: r["per_10m"])[:10]
R["overmapped"] = sorted([r for r in R["countries"] if r["pop_m"] >= 1] , key=lambda r: -r["per_m"])[:10]

# ---------- the most famous novel set in each country ----------
fam = []
for i, g in PR[PR.novel & PR.iso.notna()].groupby("iso"):
    ws = B.loc[g.book.unique()].sort_values(["links", "year"], ascending=[False, True])
    w = ws.iloc[0]
    fam.append({"iso": i, "country": cname(i), "title": w.title or w.q, "q": w.q, "links": int(w.links), "year": None if pd.isna(w.year) else int(w.year),
                "author": ", ".join(AU.at[a, "label"] for a in w.authors if a in AU.index) or "", "enwiki": w.enwiki, "n": int(ws.shape[0])})
FA = pd.DataFrame(fam).sort_values("links", ascending=False)
FA.to_csv(f"{DATA}/most_famous_novel_by_country.csv", index=False)
R["famous"] = {r["iso"]: r for r in fam}
R["famous_top"] = FA.head(12).to_dict("records")
mostlinks = B.loc[list(NOV)].sort_values("links", ascending=False)
R["most_linked"] = [{"title": r.title or r.q, "links": int(r.links), "year": None if pd.isna(r.year) else int(r.year)} for r in mostlinks.head(10).itertuples()]

# ---------- extremes ----------
real = P[~P.fictional & ~P.water & P.level.isin(["city", "site", "region"]) & P.q.isin(PR["loc"])].copy()
real["works"] = real.q.map(PR.groupby("loc").book.nunique())
rm = real.sort_values("remote_km", ascending=False)
def wl(q):
    ws = PR[PR["loc"] == q].book.unique()
    return [{"title": B.at[w, "title"] or w, "year": None if pd.isna(B.at[w, "year"]) else int(B.at[w, "year"]),
             "author": ", ".join(AU.at[a, "label"] for a in B.at[w, "authors"] if a in AU.index)} for w in ws[:4]]
R["remote"] = [{"label": r.label, "q": r.q, "km": int(r.remote_km), "lat": round(r.lat, 2), "lon": round(r.lon, 2), "level": r.level, "iso": r.iso,
                "works": wl(r.q)} for r in rm.head(10).itertuples()]
south = real.sort_values("lat").head(5); north = real.sort_values("lat", ascending=False).head(5)
R["south"] = [{"label": r.label, "lat": round(r.lat, 2), "works": wl(r.q)} for r in south.itertuples()]
R["north"] = [{"label": r.label, "lat": round(r.lat, 2), "works": wl(r.q)} for r in north.itertuples()]
ata = PR[(PR.iso == "ATA") | (PR.label == "Antarctica")]
R["antarctica"] = {"works": int(ata.book.nunique()), "novels": int(ata[ata.novel].book.nunique())}
STREET_RE = re.compile(r"street|\broad\b|avenue|boulevard|square|thoroughfare|pedestrian zone", re.I)
BUILD_RE = re.compile(r"building|\bhouse\b|hotel|palace|castle|ch[aâ]teau|church|cathedral|basilica|abbey|monastery|tower|skyscraper|museum|theat|station|prison|\binn\b|\bpub\b|caf[eé]|manor|mansion|villa|hospital|school|university|college", re.I)
NOTSITE = re.compile(r"neighbo|borough|district|quarter|suburb|ward|(?<!gay )village|community|city|town|municipal", re.I)
def site_top(rx):
    st = P[(P.level == "site") & P.types.map(lambda t: any(rx.search(x) for x in t) and not any(NOTSITE.search(x) for x in t)) & P.q.isin(PR["loc"])].copy()
    st["works"] = st.q.map(PR.groupby("loc").book.nunique()).fillna(0).astype(int)
    st["novels"] = st.q.map(PR[PR.novel].groupby("loc").book.nunique()).fillna(0).astype(int)
    st = st.sort_values(["works", "novels"], ascending=False)
    return st, [{"label": r.label or r.q, "q": r.q, "works": int(r.works), "novels": int(r.novels), "types": r.types[:3], "city": HUBS[r.hub]["name"] if r.hub in HUBS else "",
                 "iso": r.iso, "fictional": bool(r.fictional), "examples": wl(r.q)} for r in st.head(10).itertuples()]
st, R["streets"] = site_top(STREET_RE)
R["n_streets"] = len(st); R["streets_dnk"] = int((st.iso == "DNK").sum()); R["streets_dnk_pct"] = pc(R["streets_dnk"], len(st))
R["streets_top10_dnk"] = sum(1 for r in R["streets"] if r["iso"] == "DNK")
bd, R["buildings"] = site_top(BUILD_RE)
R["n_buildings"] = len(bd)
R["offworld"] = {"pairs": len(OFF), "moon_works": len({o["book"] for o in OFF if o["globe"] == "the Moon"}), "mars_works": len({o["book"] for o in OFF if o["globe"] == "Mars"}),
                 "examples": [{"title": o["title"], "place": o["place"], "globe": o["globe"]} for o in OFF][:12]}
R["fictional"] = [{"label": r.label, "works": int(PR[PR["loc"] == r.q].book.nunique()), "lat": round(r.lat, 2), "lon": round(r.lon, 2)} for r in P[P.fictional & P.q.isin(PR["loc"])].itertuples()]

# ---------- publication years ----------
yrs = E.year.dropna().astype(int)
R["years"] = {"median_novel": int(E[E.novel].year.median()), "since1900_pct": pc((E[E.novel].year >= 1900).sum(), E[E.novel].year.notna().sum()),
              "since2000_pct": pc((E[E.novel].year >= 2000).sum(), E[E.novel].year.notna().sum()), "oldest_novel": None}
on = E[E.novel & E.year.notna()].sort_values("year").iloc[0]
R["years"]["oldest_novel"] = {"title": on.title, "year": int(on.year)}
dec = (E[E.novel].year.dropna() // 10 * 10).astype(int).value_counts().sort_index()
R["novels_by_decade"] = [{"dec": int(k), "n": int(v)} for k, v in dec.items() if 1700 <= k <= 2020]
R["meta"] = {"page": PAGE, "repo": REPO, "doi": DOI, "blog": BLOG, "slug": SLUG}

# ---------- clean data out ----------
def era_of(y):
    if y is None or pd.isna(y): return None
    for i, (_, a, z) in enumerate(ERAS):
        if a <= y <= z: return i


aulab = lambda ws: "; ".join(AU.at[a, "label"] or a for a in ws if a in AU.index)
wo = E.copy()
wo["authors_names"] = wo.authors.map(aulab)
wo["genre_groups"] = [";".join(g_ for g_ in GN if r["g_" + g_]) for _, r in wo.iterrows()]
for c_ in ("types", "genres", "countrys", "langs", "forms"):
    wo[c_] = wo[c_].map(lambda x: "; ".join(x))
wo[["q", "title", "label", "year", "novel", "forms", "types", "genres", "genre_groups", "countrys", "langs", "authors_names", "links", "enwiki", "n_places"]] \
    .rename(columns={"q": "wikidata", "label": "english_label", "countrys": "origin_countries", "langs": "languages", "authors_names": "authors", "links": "sitelinks", "n_places": "places"}) \
    .sort_values("wikidata").to_csv(f"{DATA}/works.csv", index=False)
po = P[P.q.isin(PR["loc"])].copy()
po["works"] = po.q.map(PR.groupby("loc").book.nunique()); po["novels"] = po.q.map(PR[PR.novel].groupby("loc").book.nunique()).fillna(0).astype(int)
po["city"] = po.hub.map(lambda h: HUBS[h]["name"] if h in HUBS else "")
po["country"] = po.iso.map(cname); po["types"] = po.types.map(lambda x: "; ".join(x))
po[["q", "label", "lon", "lat", "level", "fictional", "types", "country", "iso", "cont", "city", "remote_km", "works", "novels"]] \
    .rename(columns={"q": "wikidata", "iso": "country_iso3", "cont": "continent", "remote_km": "km_to_nearest_town"}).sort_values("works", ascending=False).to_csv(f"{DATA}/places.csv", index=False)
PR[["book", "loc", "novel", "level", "iso", "hub"]].assign(city=PR.hub.map(lambda h: HUBS[h]["name"] if h in HUBS else "")).drop(columns="hub") \
    .rename(columns={"book": "work", "loc": "place", "iso": "country_iso3"}).to_csv(f"{DATA}/work_places.csv", index=False)
DI.assign(km=DI.km.round(0)).rename(columns={"q": "work", "loc": "place", "biso": "birth_country_iso3", "iso": "setting_country_iso3"}).to_csv(f"{DATA}/novel_distances.csv", index=False)
pd.DataFrame([hubrow(h, n) for h, n in hn.items()]).drop(columns=["hub"]).rename(columns={"n": "novels", "all": "works"}).to_csv(f"{DATA}/cities.csv", index=False)

# ---------- distance histogram ----------
EDGES = [0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20100]
R["dist_hist"] = {"edges": EDGES, "n": [int(((DI.km >= a) & (DI.km < b)).sum()) for a, b in zip(EDGES[:-1], EDGES[1:])]}
assert sum(R["dist_hist"]["n"]) == len(DI)

# ---------- spot facts used in the text ----------
HN, rank = {}, {}
for i, (h, n) in enumerate(hn.items()):
    if HUBS[h]["name"] not in HN:                     # the best-used city of that name
        HN[HUBS[h]["name"]] = (h, int(n)); rank[HUBS[h]["name"]] = i + 1
R["spot"] = {nm: {"n": HN[nm][1], "rank": rank[nm], "all": int(ha.get(HN[nm][0], 0)), "pop_m": round(HUBS[HN[nm][0]]["pop"] / 1e6, 1)}
             for nm in ("London", "New York City", "Paris", "Pittsburgh", "Chicago", "Boston", "Tokyo", "Hong Kong", "Buenos Aires", "Cairo", "Mumbai", "Lagos",
                        "Copenhagen", "Toulouse", "Madrid", "Rome", "Los Angeles", "San Francisco", "Dublin", "Kolkata", "Jakarta", "Beijing", "Shanghai")
             if nm in HN}
af = {}
for a in ("Q128790", "Q513883", "Q234392", "Q189869", "Q337351", "Q9711", "Q228901"):
    ws = [q for q in NOV if a in B.at[q, "authors"]]
    d = PR[PR.book.isin(ws) & PR.hub.notna()].drop_duplicates(["book", "hub"]).groupby("hub").book.nunique().sort_values(ascending=False)
    ci = PR[PR.book.isin(ws) & PR.iso.notna()].drop_duplicates(["book", "iso"]).groupby("iso").book.nunique().sort_values(ascending=False)
    af[AU.at[a, "label"].replace(".", "").replace("  ", " ")] = {"novels": len(ws), "born": cname(AU.at[a, "biso"]), "top_city": HUBS[d.index[0]]["name"] if len(d) else None,
                             "top_city_n": int(d.iloc[0]) if len(d) else 0, "top_country": cname(ci.index[0]) if len(ci) else None, "top_country_n": int(ci.iloc[0]) if len(ci) else 0}
R["author_facts"] = af

# ---------- figure points: city areas and areas, with novels and all works ----------
mp_ = []
for h, g in PR[PR.hub.notna()].groupby("hub"):
    H = HUBS[h]; mp_.append({"kind": "city", "name": H["name"], "lon": round(H["lon"], 3), "lat": round(H["lat"], 3), "novels": int(g[g.novel].book.nunique()), "works": int(g.book.nunique())})
for q, g in PR[(PR.level == "region") & ~PR.fictional].groupby("loc"):
    p = P.loc[q]; mp_.append({"kind": "area", "name": p.label or q, "lon": round(p.lon, 3), "lat": round(p.lat, 3), "novels": int(g[g.novel].book.nunique()), "works": int(g.book.nunique())})
pd.DataFrame(mp_).sort_values("works", ascending=False).to_csv(f"{DATA}/map_points.csv", index=False)

# ---------- page data ----------
WL = sorted(E.q, key=lambda q: -B.at[q, "links"])            # works, most linked first
WI = {q: i for i, q in enumerate(WL)}
AUL = sorted({a for q in WL for a in B.at[q, "authors"] if a in AU.index})
AI_ = {a: i for i, a in enumerate(AUL)}
gmask = lambda r: sum(1 << k for k, g_ in enumerate(GN) if r["g_" + g_])
works = []
for q in WL:
    r = B.loc[q]
    slug = r.enwiki.rsplit("/wiki/", 1)[-1] if r.enwiki else ""
    works.append([q, r.title, None if pd.isna(r.year) else int(r.year), [AI_[a] for a in r.authors if a in AI_], int(r.links), slug, int(r.novel), gmask(r)])
authors = [[a, AU.at[a, "label"] or a, None if np.isnan(AU.at[a, "blon"]) else round(float(AU.at[a, "blon"]), 3),
            None if np.isnan(AU.at[a, "blat"]) else round(float(AU.at[a, "blat"]), 3), AU.at[a, "biso"] if isinstance(AU.at[a, "biso"], str) else ""] for a in AUL]
HL = sorted(PR.hub.dropna().unique(), key=lambda h: -ha.get(h, 0)); HI = {h: i for i, h in enumerate(HL)}
pts = []
PI = {}
for q, g in PR.groupby("loc"):
    p = P.loc[q]
    if p.level in ("country", "large"): continue
    PI[q] = len(pts)
    pts.append([q, p.label or q, round(float(p.lon), 4), round(float(p.lat), 4), {"city": 0, "site": 1, "region": 2}[p.level], int(p.fictional),
                HI.get(p.hub, -1), p.iso or "", sorted(WI[b] for b in g.book.unique())])
# whole-country and large-area settings, by country (for the country panel)
whole = defaultdict(list)
for r in PR[PR.level.isin(["country"]) & PR.iso.notna()].itertuples():
    whole[r.iso].append(WI[r.book])
large = defaultdict(list)
for r in PR[PR.level == "large"].itertuples():
    large[r.label].append(WI[r.book])
jsave({"genres": GN, "eras": [e[0] for e in ERAS], "works": works, "authors": authors, "points": pts,
       "hubs": [[HUBS[h]["name"], round(HUBS[h]["lon"], 3), round(HUBS[h]["lat"], 3), HUBS[h]["iso"] or ""] for h in HL],
       "whole": {k: sorted(set(v)) for k, v in whole.items()}, "large": {k: sorted(set(v)) for k, v in large.items()}}, f"{DATA}/points.json")
site = {"genres": GENRES, "eras": ERAS, "trio": TRIO, "cname": {k: v["name"] for k, v in CM.items()},
        "cpos": {k: [v["lx"], v["ly"], v["pop"]] for k, v in CM.items()},
        "ccount": {r["iso"]: [r["n"], r["all"]] for r in R["countries"]},
        "famous": {k: [v["title"], v["author"], v["year"], v["links"], v["enwiki"].rsplit("/wiki/", 1)[-1] if v["enwiki"] else "", v["q"]] for k, v in R["famous"].items()},
        "remote": R["remote"][:3], "conts": CONTS, "ccol": CCOL}
jsave(site, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print("results ok", {k: os.path.getsize(f"{DATA}/{k}") // 1024 for k in ("site.json", "points.json", "results.json")})
