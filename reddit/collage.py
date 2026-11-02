"""r/dataisbeautiful collage for novel-settings: 2400 x 3200 px, light background. Numbers from data/results.json.
Labels sit on open sea or on the paper around the globe, with a halo; they never touch land or a circle, and no leader
line crosses a label."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figstyle import *
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.patches import Circle
from matplotlib.lines import Line2D

R = jload(f"{DATA}/results.json")
MP = pd.read_csv(f"{DATA}/map_points.csv")
BGc = "#F7F5F0"; SEAc = "#E9EFF2"; LANDc = "#E2DDD1"
HALO = [pe.withStroke(linewidth=4, foreground=SEAc)]
HALOP = [pe.withStroke(linewidth=4, foreground=BGc)]
s, sp, co, hm = R["source"], R["spot"], R["continents"], R["home"]
TC = dict(TRIO)

fig = plt.figure(figsize=(12, 16.0), dpi=200, facecolor=BGc)
fig.text(.045, 0.9844, "Where novels are set", fontproperties=DISP, fontsize=48, color=FG, va="top")
fig.text(.045, 0.9375, f"The real settings of {s['novels']:,} novels in Wikidata. London, New York and Paris dominate; Asia, home to\n"
         f"{co['Asia']['pop_pct']:.0f}% of the world's people, gets {co['Asia']['novels_pct']:.0f}% of the novels. Most authors stay close to where they were born.",
         fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.45)

# ---- map
ax = fig.add_axes([0, 0.5062, 1, 0.3844])
outline(ax, fc=SEAc, ec="#C9CDD0", lw=.8); world(ax, lw=.3, land=LANDc, ec=BGc)
K = 5.2e5 / np.sqrt(MP.novels.max())
rad = lambda n: max(K * np.sqrt(n), 3.2e4)
BUB = []
for r in MP[(MP.kind == "area") & (MP.novels > 0)].sort_values("novels", ascending=False).itertuples():
    x, y = proj(r.lon, r.lat); rr = rad(r.novels)
    ax.add_patch(Circle((float(x), float(y)), rr, fc="none", ec=COOL, lw=.7, alpha=.75, zorder=3)); BUB.append((float(x), float(y), rr))
for r in MP[(MP.kind == "city") & (MP.novels > 0)].sort_values("novels", ascending=False).itertuples():
    x, y = proj(r.lon, r.lat); rr = rad(r.novels)
    ax.add_patch(Circle((float(x), float(y)), rr, fc=HOT, ec="#fff", lw=.4, alpha=.85, zorder=4)); BUB.append((float(x), float(y), rr))

from shapely.geometry import shape as _shape, box as _box, Point as _Pt, LineString as _LS, Polygon as _Poly
from shapely.ops import unary_union, nearest_points
from shapely.prepared import prep as _prep
LAND_MARGIN = 25e3
_land = []
for f in jload(f"{GEO}/ne_50m_land.geojson")["features"]:
    g = _shape(f["geometry"]); gs = g.geoms if g.geom_type == "MultiPolygon" else [g]
    for q in gs:
        xy = np.array(q.exterior.coords); x, y = EE.transform(np.clip(xy[:, 0], -179.99, 179.99), np.clip(xy[:, 1], -89.9, 89.9))
        _land.append(_Poly(np.column_stack([x, y])).buffer(0))
LAND = unary_union(_land).buffer(LAND_MARGIN); LANDP = _prep(LAND)
BUBG = _prep(unary_union([_Pt(x, y).buffer(r + 2e4) for x, y, r in BUB if r > 3.3e4] + [_Pt(x, y).buffer(4e4) for x, y, r in BUB if r <= 3.3e4]))
fig.canvas.draw(); REN = fig.canvas.get_renderer()
PLACED, LINES = [], []


def tbox(t):
    bb = t.get_window_extent(REN)
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([[bb.x0 - 4, bb.y0 - 3], [bb.x1 + 4, bb.y1 + 3]])
    return _box(x0, y0, x1, y1)


def bad(b):
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    if not _box(x0 + 1e5, y0 + 1e5, x1 - 1e5, y1 - 1e5).contains(b): return True
    return LANDP.intersects(b) or BUBG.intersects(b) or any(b.intersects(o) for _, _, o in PLACED) or any(b.intersects(l) for _, l in LINES)


def place(name, txt, lon0, lat0, target, ha="center", col=FG, size=10.5, w="medium", lead_gap=2.0e5, maxr=40):
    t = ax.text(0, 0, txt, ha=ha, va="center", fontsize=size, color=col, family=MONO, linespacing=1.15, zorder=10, path_effects=HALO, fontweight=w)
    tx, ty = proj(target[0], target[1]); c = _Pt(float(tx), float(ty)); tr = rad(target[2])
    cands = [(lon0 + dx, lat0 + dy) for r in range(0, maxr + 1) for dx in range(-r, r + 1) for dy in range(-r, r + 1) if max(abs(dx), abs(dy)) == r]
    for lon, lat in cands:
        if abs(lat) > 80: continue
        x, y = proj(((lon + 180) % 360) - 180, lat); t.set_position((float(x), float(y))); b = tbox(t)
        if bad(b): continue
        ln = None
        if b.distance(c) - tr > lead_gap:
            pb, _ = nearest_points(b, c); d = np.hypot(pb.x - c.x, pb.y - c.y)
            e = (c.x + (pb.x - c.x) * tr / d, c.y + (pb.y - c.y) * tr / d); ln = _LS([(pb.x, pb.y), e])
            if any(ln.intersects(o) for _, _, o in PLACED) or any(ln.crosses(l) for _, l in LINES): continue
        PLACED.append((name, t, b))
        if ln is not None:
            LINES.append((name, ln)); ax.plot(*ln.xy, color=FG, lw=.75, zorder=9)
        return
    raise RuntimeError("no clean spot for " + name)


def city(nm):
    r = MP[(MP.kind == "city") & (MP.name == nm)].sort_values("novels", ascending=False).iloc[0]; return (r.lon, r.lat, r.novels)


place("London", f"LONDON\n{sp['London']['n']:,}", -18, 60, city("London"), size=11.5, w="medium")
place("Paris", f"PARIS\n{sp['Paris']['n']:,}", -16, 44, city("Paris"), size=11.5, w="medium")
place("NY", f"NEW YORK\n{sp['New York City']['n']:,}", -60, 33, city("New York City"), size=11.5, w="medium")
place("LA", f"LOS ANGELES {sp['Los Angeles']['n']}\nSAN FRANCISCO {sp['San Francisco']['n']}", -140, 33, city("Los Angeles"), ha="right", size=10)
place("Tokyo", f"TOKYO {sp['Tokyo']['n']}", 152, 33, city("Tokyo"), size=10)
place("Mumbai", f"MUMBAI {sp['Mumbai']['n']}", 64, 12, city("Mumbai"), size=10)
place("Lagos", f"LAGOS {sp['Lagos']['n']}", 1, -2, city("Lagos"), size=10)
place("BA", f"BUENOS AIRES {sp['Buenos Aires']['n']}", -44, -40, city("Buenos Aires"), size=10)
for nm, t, b in PLACED:
    assert not LANDP.intersects(b) and not BUBG.intersects(b), nm
    assert not any(b.intersects(o) for n2, _, o in PLACED if n2 != nm), nm
for nm, l in LINES:
    assert not any(l.intersects(o) for n2, _, o in PLACED if n2 != nm), nm
    assert not any(l.crosses(o) for n2, o in LINES if n2 != nm), nm
print("labels ok:", len(PLACED), "leaders:", [n for n, _ in LINES])

# size key on the paper, bottom left corner outside the globe
kx0, ky0 = -1.64e7, -8.3e6
for i, n in enumerate((10, 100, 500)):
    r = rad(n); xc = kx0 + i * 1.25e6 + (0 if i < 2 else .3e6)
    ax.add_patch(Circle((xc, ky0 + r), r, fc="none", ec=FG, lw=.9, zorder=9))
    kt = ax.text(xc - (0 if i < 2 else 5e5), ky0 - 4e5, f"{n}" + (" novels" if i == 2 else ""), ha="center" if i < 2 else "left", fontsize=9, color=FG, zorder=10)
    fig.canvas.draw(); assert not LANDP.intersects(tbox(kt)), "size key"

LEG = [Line2D([], [], ls="", marker="o", ms=10, mfc=HOT, mec="#fff", label="city, town or single site (places within 25 km of a big city merged)"),
       Line2D([], [], ls="", marker="o", ms=10, mfc="none", mec=COOL, label="wider area: state, region or island, drawn at its Wikidata point")]
LP = SERP.copy(); LP.set_size(11.5)
fig.text(.045, 0.4938, f"Circle area: novels set at least partly there. Novels that name only a whole country ({R['levels']['novels_country_only']:,}) are not drawn.", fontsize=9.6, color=MUT, va="top")
fig.legend(handles=LEG, loc="upper left", bbox_to_anchor=(.035, 0.4781), ncol=1, frameon=False, prop=LP, handletextpad=.4, labelspacing=.5)

# ---- numbers row
nums = [(f"{s['novels']:,}", NAVY, f"novels with a real setting,\nin {s['places_novels']:,} places"),
        (f"{sp['London']['n']}", HOT, f"set in London, the most;\nMumbai has {sp['Mumbai']['n']}"),
        (f"{hm['median_km']} km", "#B07A12", "median distance from the\nauthor's birthplace"),
        (f"{co['Asia']['novels_pct']:.0f}%", COOL, f"set in Asia, home to\n{co['Asia']['pop_pct']:.0f}% of the world's people")]
for i, (big, col, small) in enumerate(nums):
    xx = .045 + i * .235
    fig.text(xx, 0.4219, big, fontproperties=DISP, fontsize=34, color=col, va="top")
    fig.text(xx, 0.3844, small, family=MONO, fontsize=10.5, color=FG, va="top", linespacing=1.4)

# ---- trio lines
T = pd.DataFrame(R["trio20"])
a = fig.add_axes([.075, 0.1, .5, 0.228]); a.set_facecolor(BGc)
xs = np.arange(len(T))
for k, c in TRIO:
    a.plot(xs, T[k + "_pct"], "-o", color=c, lw=2.6, ms=5)
spines(a); a.grid(axis="y", color=RULE, lw=.8); a.set_axisbelow(True); a.set_ylim(0, 50); a.set_xlim(-.4, len(T) - .6)
a.set_xticks(xs); a.set_xticklabels([str(f) for f in T["from"]], fontsize=8.5, rotation=0); a.tick_params(axis="y", labelsize=9)
a.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
a.set_title("Share of novels set in each city, by 20-year publication period", family=MONO, fontsize=11.5, color=FG, loc="left", pad=8)
a.text(.35, 41.5, f"Paris {T.Paris_pct[0]:.0f}% in 1830 to 1849", color=TC["Paris"], fontsize=10, path_effects=HALOP)
a.text(6, 19.5, "New York\nleads 1950 to 1989", color="#A37000", fontsize=9.5, ha="center", path_effects=HALOP)
a.text(8.9, 14.5, "London\nsince 1990", color=TC["London"], fontsize=9.5, ha="center", path_effects=HALOP)

# ---- continents vs population
b2 = fig.add_axes([.69, 0.1, .27, 0.228]); b2.set_facecolor(BGc)
CL = [c for c in R["continents_list"] if c["cont"] != "Antarctica"]; yy = np.arange(len(CL))[::-1]
b2.barh(yy + .2, [c["novels_pct"] for c in CL], height=.38, color=HOT)
b2.barh(yy - .2, [c["pop_pct"] for c in CL], height=.38, color="#B9B2A6")
for y_, c in zip(yy, CL):
    b2.text(c["novels_pct"] + 1, y_ + .2, f"{c['novels_pct']:.0f}%", va="center", fontsize=8.5, color=HOT)
    b2.text(c["pop_pct"] + 1, y_ - .2, f"{c['pop_pct']:.0f}%", va="center", fontsize=8.5, color=MUT)
b2.set_yticks(yy); b2.set_yticklabels([c["cont"].replace("North America", "N. America").replace("South America", "S. America") for c in CL], fontsize=9)
b2.set_xlim(0, 75); b2.set_xticks([]); spines(b2); b2.spines["bottom"].set_visible(False); b2.tick_params(axis="y", length=0)
b2.set_title("Novels vs people", family=MONO, fontsize=11.5, color=FG, loc="left", pad=8)
fig.legend(handles=[Line2D([], [], color=c, lw=2.6, marker="o", ms=5, label=k) for k, c in TRIO] +
           [Line2D([], [], ls="", marker="s", ms=9, mfc=HOT, mec=HOT, label="share of novels"), Line2D([], [], ls="", marker="s", ms=9, mfc="#B9B2A6", mec="#B9B2A6", label="share of people")],
           loc="upper left", bbox_to_anchor=(.07, .077), ncol=5, frameon=False, fontsize=9.5, handletextpad=.4, columnspacing=1.3)

fig.text(.045, .006, f"Source: Wikidata (CC0), narrative location (P840) of every literary work with coordinates, queried with QLever in {s['extract_year']}; outlines and populations: Natural Earth.\n"
         f"Novel = form novel or novella, or a class named novel. City = places within 25 km of a city of 250,000+. Wikidata coverage is uneven: Denmark alone\n"
         f"has {R['bias']['DNK']['places']} setting places, China and India {R['bias']['dnk_vs']['chn_ind_places']} together.  Analysis and chart: Tristan Hotham, Python and matplotlib  ·  maps.tristanhotham.com/novel-settings",
         family=MONO, fontsize=8.2, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "where_novels_are_set.png")
fig.savefig(out, facecolor=BGc, dpi=200)
print("ok", out)
