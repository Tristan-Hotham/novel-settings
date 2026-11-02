"""Geography: world outlines for the page and figures (Natural Earth 1:50m), country names, continents and populations,
a level, a present-day country and a city for every setting place, and a birth country for every author.

Levels, from the place's Wikidata classes (P31 labels in loctype.tsv), in this order:
- large: a continent, ocean, sea, subcontinent or world region (Europe, the Atlantic, the Balkans as a 'cultural area').
  No country; never drawn as a point.
- country: the place is a Natural Earth country (by Wikidata ID), is itself the country (P17) of some other place, or is
  a country, state, empire, kingdom, colony, dynasty, civilisation or historical period. Its point is a centroid or a
  capital, so it is never drawn as a point. Countries smaller than 1,500 km2 (Monaco, Singapore, Malta...) count as cities.
- city: a city, town, village, municipality, commune or other settlement (unless it is also typed as a part of a city).
- site: a part of a city (neighbourhood, borough, district, quarter, suburb, ward) or a single site (street, square,
  building, house, hotel, palace, church, park, station, school, prison, camp...) or a point feature (mountain, cape,
  waterfall, beach). Places with no class are sites.
- region: anything larger and vaguer: a region, province, county, state of a country, island, archipelago, peninsula,
  valley, desert, forest, river, lake or national park. Drawn as a point (its Wikidata coordinate), marked as an area.
Fictional: any class with 'fictional' in its label (221B Baker Street, Arkham, R'lyeh). Kept, flagged, and left out of
claims about real places.
Country: the present-day Natural Earth (1:10m) country the point falls in, or the nearest within 0.3 degrees; for
country-level places with a Natural Earth Wikidata ID, that country; else the place's Wikidata country (P17) if it maps to a
Natural Earth country; else none (open sea).
City: every city- or site-level place is grouped with the nearest Natural Earth populated place of 250,000 people or more
within HUB_KM (25 km), else it stands alone. So Baker Street, Bloomsbury and Hampstead count for London.
Fictional also covers phantom islands (Maria Theresa Reef).
Remoteness: great-circle distance from the place to the nearest Natural Earth city of 1,000,000 people or more. Seas,
bays, straits and circles of latitude are flagged as water and left out of the remoteness ranking.
Authors: birth country = present-day country of the birthplace coordinates, by the same point test."""
import math
import numpy as np, pandas as pd
from collections import Counter, defaultdict
from shapely.geometry import shape, mapping, Point
from shapely.strtree import STRtree
from common import *

HUB_KM = 25
iso_of = lambda p: p["ISO_A3_EH"] if p.get("ISO_A3_EH") not in ("-99", None) else p["ADM0_A3"]
FIXISO = {"CNM": "CYP", "ESB": "CYP", "WSB": "CYP", "PSX": "PSE", "SAH": "ESH", "SOL": "SOM", "KAB": "KAZ", "CYN": "CYP", "BJN": "COL",
          "SER": "COL", "SCR": "CHN", "USG": "CUB", "KAS": "IND"}


def rnd(c, k=2):
    if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
        return [round(c[0], k), round(c[1], k)]
    return [rnd(x, k) for x in c]


W50 = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")
feats, meta = [], {}
for f in W50["features"]:
    p = f["properties"]; iso = FIXISO.get(iso_of(p), iso_of(p))
    g = shape(f["geometry"]).simplify(0.04, preserve_topology=True)
    if g.is_empty:
        continue
    gm = mapping(g)
    feats.append({"type": "Feature", "properties": {"iso": iso}, "geometry": {"type": gm["type"], "coordinates": rnd(gm["coordinates"])}})
    if iso in meta:
        continue
    nm = (p["NAME_EN"] or p["NAME"]).replace("People's Republic of China", "China").replace("United States of America", "United States")
    nm = {"The Bahamas": "Bahamas", "Republic of the Congo": "Congo", "Kingdom of the Netherlands": "Netherlands", "The Gambia": "Gambia",
          "Federated States of Micronesia": "Micronesia", "Republic of Ireland": "Ireland"}.get(nm, nm)
    meta[iso] = {"name": nm, "cont": p["CONTINENT"], "pop": float(p["POP_EST"] or 0), "lx": round(p["LABEL_X"], 2), "ly": round(p["LABEL_Y"], 2)}
jsave({"type": "FeatureCollection", "features": feats}, f"{DATA}/world.json")

W10 = jload(f"{GEO}/ne_10m_admin_0_countries.geojson")
QID, geoms, AREA = {}, [], defaultdict(float)
for f in W10["features"]:
    p = f["properties"]; iso = FIXISO.get(iso_of(p), iso_of(p))
    if p.get("WIKIDATAID"):
        QID[p["WIKIDATAID"]] = iso
    g = shape(f["geometry"]).buffer(0); geoms.append((iso, g))
    c = g.representative_point(); AREA[iso] += g.area * 12364 * math.cos(math.radians(c.y))     # rough km2
    if iso not in meta:
        meta[iso] = {"name": p["NAME_EN"] or p["NAME"], "cont": p["CONTINENT"], "pop": float(p["POP_EST"] or 0), "lx": round(c.x, 2), "ly": round(c.y, 2)}
meta["ATA"]["cont"] = "Antarctica"
# a few Wikidata IDs for countries that Natural Earth files under another ID
QID.update({"Q21": "GBR", "Q22": "GBR", "Q25": "GBR", "Q26": "GBR", "Q35": "DNK", "Q55": "NLD", "Q29999": "NLD", "Q756617": "DNK", "Q148": "CHN", "Q1246": "KOS"})
tree = STRtree([g for _, g in geoms])


def at(lon, lat):
    pt = Point(lon, lat)
    hit = [geoms[i][0] for i in tree.query(pt) if geoms[i][1].covers(pt)]
    if hit:
        return hit[0]
    near = [(geoms[i][1].distance(pt), geoms[i][0]) for i in tree.query(pt.buffer(0.3))]
    near = [x for x in near if x[0] < 0.3]
    return min(near)[1] if near else None


# ---------- levels ----------
RX = lambda s: re.compile(s, re.I)
LARGE_RE = RX(r"^(continent|supercontinent|part of the world|subcontinent|ocean|sea|marginal sea|adjacent sea|inland sea|geopolitical group|"
              r"transcontinental region|region of the world|group|macroregion|world region|geography term|term)$")
LARGE_NAME = RX(r"^((North|South|East|West|Central|Southern|Northern|Eastern|Western|Sub-Saharan|Southeast|South-East)(ern)? (Africa|Asia|Europe|America)|"
                r"Scandinavia|Balkans|Middle East|Far East|Near East|Latin America|Arctic|Levant|Orient|Western world|Americas|Oceania|Polynesia|Melanesia|Micronesia)$")
COUNTRY_RE = RX(r"(?<!english )(?<!english\s)\bcountry\b(?! house)|sovereign state|state with limited recognition|kingdom|empire|realm|\brepublic\b(?! of russia)|"
                r"\bcolony\b|colonial power|protectorate|\bfederation\b|^nation$|nation state|confederation|dynasty|historical period|civilization|"
                r"regime|puppet state|rump state|grand duchy|sultanate|dependent territory|unitary state|monarchy|communist state|secular state|"
                r"social state|Rechtsstaat|historical unrecognized state|occupied territory|countship|historical nationality|viceroyalty|"
                r"historical Chinese state|confessional state|state of the Holy Roman Empire|^state$|federal republic")
SUB_RE = RX(r"neighbo|borough|city district|district of (vienna|moscow|budapest|paris)|\bquarter\b|quartier|suburb|\bward\b|area of london|locality of|"
            r"ortsteil|ortsbezirk|colonia|dzielnica|arrondissement|gay village|little italy|old town|historic district|stadtteil|city quarter|"
            r"neighborhood|kelurahan|chōchō|cadastral|Gemarkung|unparished area|district of (copenhagen|berlin)|quarter in|part of|"
            r"locality of|NRHP district|ghetto")
CITY_RE = RX(r"\bcity\b|\btown\b|municipalit|\bcommune\b|\bcomune\b|village|hamlet|settlement|capital|metropolis|megacity|\bpolis\b|"
             r"^locality$|urban area|burgh|frazione|\bdesa\b|kecamatan|şəhər|conurbation|agrotown|Lutherstadt|seaport|county seat|"
             r"market town|spa town|resort town|ghost town|\bcommunity\b|populated place|city-state|chef-lieu|seat of government|"
             r"\bseat\b|census-designated place|Hanseatic|polis|charter city|global city|largest city|big city|tourist destination|"
             r"administrative centre|oblast seat|regional center|district town|cycling city|Option municipality|Einheitsgemeinde|"
             r"municipality|planned community|mining community|satellite city|coastal spa|onsen|emporium|single entity of population")
SITE_RE = RX(r"street|\broad\b|avenue|boulevard|thoroughfare|square|bridge|building|\bhouse\b|hotel|castle|palace|ch[aâ]teau|church|cathedral|"
             r"basilica|mosque|temple|shrine|synagogue|monastery|abbey|convent|museum|station|\bpark\b|garden|school|university|college|"
             r"gymnasium|folkeskole|institute|prison|\bcamp\b|cemetery|necropolis|theat|opera house|caf[eé]|restaurant|\bbar\b|\binn\b|tower|"
             r"skyscraper|\bfort\b|fortress|barracks|airport|aerodrome|airbase|\bport\b|harbou?r|\bzoo\b|hospital|clinic|mansion|villa|manor|"
             r"estate|\bfarm\b|\bmine\b|beach|cave|waterfall|monument|stadium|venue|library|archaeological site|ruins|tell|sculpture|fountain|"
             r"structure|landmark|shopping|office|residen|smithy|observatory|gate|canal|pedestrian zone|amusement|theme park|business park|"
             r"\bmountain\b|^hill$|volcano|\bcape\b|headland|highest point|mountain pass|glacier|crater|lighthouse|pier|wharf|market|"
             r"concentration camp|extermination camp|battlefield|battle|siege|educational|organization|organisation|publisher|business|"
             r"spring|springs|onsen|tanjun|sanctuary|cultural heritage|cultural property|heritage|historic site|ensemble|complex|"
             r"brewery|factory|plant|club|rapid transit|railway|metro|underground")
REGION_RE = RX(r"region|province|state|county|prefecture|oblast|canton|department|governorate|federal subject|autonomous|district|island|"
               r"archipelago|peninsula|mountain range|range|desert|valley|forest|river|stream|lake|bay|coast|national park|plain|basin|delta|"
               r"fjord|strait|sound|firth|narrows|channel|marsh|swamp|bog|wetland|moor|heath|landscape|territory|territorial|area|riviera|"
               r"ecoregion|protected|reserve|nature|mountains|massif|plateau|highland|steppe|tundra|ice cap|crown dependenc|polder|island group|"
               r"alpine|upland|lowland|gulf|lagoon|estuary|watershed|drainage|endorheic|horst|planitia|vallis|wine|parish|electoral|constituency|"
               r"council|lieutenancy|regency|administrative|entity|division|subdivision|local government|enclave|exclave|panhandle|colony|"
               r"dependency|realm|subregion|tourism region|metropolitan|statistical|historical province|land\b|islands")


def level(q, types, label):
    t = types
    if (LARGE_NAME.search(label or "") or any(LARGE_RE.search(x) for x in t)) and not any(CITY_RE.search(x) for x in t) and q not in QID:
        return "large"
    cty = [x for x in t if COUNTRY_RE.search(x)]
    if cty and q not in QID and q not in COUNTRY_QS and set(c.lower() for c in cty) <= {"historical country"} and \
            any(re.search(r"county|province|region of|state of", x, re.I) for x in t):
        cty = []                         # an old kingdom that is now a county or province (Kent, Sussex) is a region
    if q in QID or q in COUNTRY_QS or cty:
        if any(re.search(r"city-state|city state", x, re.I) for x in t):
            return "city"
        if not any(CITY_RE.search(x) for x in t) or q in QID:
            return "country"
    sub = [x for x in t if SUB_RE.search(x)]
    strong_city = [x for x in t if CITY_RE.search(x) and not SUB_RE.search(x)]
    if strong_city and (not sub or any(re.search(r"^(city|big city|town|village|capital|national capital|largest city|global city|metropolis|megacity)$|"
                                                 r"\b(city|town|capital|county seat|municipality|commune|comune)\b", x, re.I) for x in strong_city)):
        return "city"
    if sub or any(SITE_RE.search(x) for x in t):
        return "site"
    if any(REGION_RE.search(x) for x in t):
        return "region"
    return "site" if not t else "other"


P = pd.read_pickle(f"{WORK}/places.pkl")
COUNTRY_QS = {q for cs in P.wdc for q, _ in cs}      # items that are the country (P17) of some place
P["fictional"] = P.types.map(lambda t: any("fictional" in x.lower() or "phantom" in x.lower() for x in t))
P["level"] = [level(q, t, l) for q, t, l in zip(P.q, P.types, P.label)]
oth = Counter(x for t, l in zip(P.types, P.level) if l == "other" for x in t)
print("unclassified place classes:", oth.most_common(40))
P.loc[P.level == "other", "level"] = "site"
P["iso"] = None
for i, r in P.iterrows():
    if r.level == "large":
        continue
    if r.level in ("country", "city") and r.q in QID:
        P.at[i, "iso"] = QID[r.q]; continue
    iso = at(r.lon, r.lat)
    if iso is None:
        wd = [QID[q] for q, _ in r.wdc if q in QID]
        iso = wd[0] if wd else None
    P.at[i, "iso"] = iso
# small countries count as cities
small = (P.level == "country") & P.iso.map(lambda i: AREA.get(i, 1e9) < 1500)
P.loc[small, "level"] = "city"
P["cont"] = P.iso.map(lambda i: meta.get(i, {}).get("cont") if i else None)
P.loc[P.cont == "Seven seas (open ocean)", "cont"] = None
print("levels", P.level.value_counts().to_dict(), "no country", int(P.iso.isna().sum()), "small countries as cities", int(small.sum()))

# ---------- cities (hubs) ----------
PP = jload(f"{GEO}/ne_10m_populated_places_simple.geojson")["features"]
pp = pd.DataFrame([{"name": re.sub(r"\s+", " ", f["properties"]["name"]), "iso": FIXISO.get(f["properties"]["adm0_a3"], f["properties"]["adm0_a3"]),
                    "lon": f["properties"]["longitude"], "lat": f["properties"]["latitude"], "pop": int(f["properties"]["pop_max"] or 0),
                    "cap": int(f["properties"]["adm0cap"] or 0)} for f in PP])
BIG = pp[pp["pop"] >= 250000].reset_index(drop=True)
hub = []
for r in P.itertuples():
    if r.level not in ("city", "site"):
        hub.append(None); continue
    if r.q in QID:                       # a small country counts as its own city
        hub.append(f"{r.label}|{r.q}"); continue
    d = km(r.lon, r.lat, BIG.lon.values, BIG.lat.values); j = int(np.argmin(d))
    hub.append(f"{BIG.name[j]}|{BIG.iso[j]}" if d[j] <= HUB_KM else f"{r.label}|{r.q}")
P["hub"] = hub
M1 = pp[pp["pop"] >= 1000000]
dmin = np.array([km(lo, la, M1.lon.values, M1.lat.values).min() for lo, la in zip(P.lon, P.lat)])
P["remote_km"] = dmin.round(0)
P["water"] = P.types.map(lambda t: any(re.search(r"\b(bay|sea|ocean|strait|body of water|circle of latitude|gulf|channel|sound|ocean bank|submarine canyon)\b", x, re.I) for x in t))
HUBS = {f"{r.name}|{r.iso}": {"name": r.name, "iso": r.iso, "lon": r.lon, "lat": r.lat, "pop": r.pop} for r in BIG.itertuples()}
for r in P.itertuples():
    if r.hub and r.hub not in HUBS:
        HUBS[r.hub] = {"name": r.label or r.q, "iso": r.iso, "lon": r.lon, "lat": r.lat, "pop": 0}
# a hub is named after its best-used city-level place (London, New York City, Copenhagen), else Natural Earth's name
PRn = pd.read_pickle(f"{WORK}/pairs.pkl").groupby("loc").size()
best = P[(P.level == "city") & (P.label != "")].assign(n=P.q.map(PRn).fillna(0)).sort_values("n", ascending=False).drop_duplicates("hub")
for r in best.itertuples():
    if r.hub in HUBS and km(r.lon, r.lat, HUBS[r.hub]["lon"], HUBS[r.hub]["lat"]) < HUB_KM:
        HUBS[r.hub]["name"] = r.label
jsave(HUBS, f"{WORK}/hubs.json")

# ---------- authors ----------
AU = pd.read_pickle(f"{WORK}/authors.pkl")
AU["biso"] = [at(lo, la) if not np.isnan(lo) else None for lo, la in zip(AU.blon, AU.blat)]
print("authors with birth country", int(AU.biso.notna().sum()), "of", int(AU.blon.notna().sum()), "with coordinates")

# ---------- outlines and label positions ----------
cities = [{"name": r.name, "lat": round(r.lat, 3), "lon": round(r.lon, 3), "pop": r.pop} for r in pp.itertuples() if r.pop >= 250000 or r.cap == 1]
cities.sort(key=lambda c: -c["pop"])
jsave(cities, f"{DATA}/cities.json")
for k in meta:
    meta[k]["area"] = round(AREA.get(k, 0))
jsave(meta, f"{WORK}/countries.json")
P.to_pickle(f"{WORK}/places_geo.pkl"); AU.to_pickle(f"{WORK}/authors_geo.pkl")
print("countries", len(meta), "cities", len(cities), "world", os.path.getsize(f"{DATA}/world.json") // 1024, "KB", "hubs", P.hub.nunique())
