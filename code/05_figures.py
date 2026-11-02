"""Header card, blog figures (release/blog/b_*.png, 1800 px wide) and paper figures (release/paper/f_*.png).
Numbers from data/results.json and data/map_points.csv."""
import pandas as pd
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from figstyle import *

R = jload(f"{DATA}/results.json")
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
for d in (BL, PA):
    for fn in os.listdir(d):
        if fn.endswith(".png"): os.remove(os.path.join(d, fn))
HALO = [pe.withStroke(linewidth=3.5, foreground=SEA)]
HALOB = [pe.withStroke(linewidth=3.5, foreground=BG)]
MP = pd.read_csv(f"{DATA}/map_points.csv")
TC = dict(TRIO)


def both(fig, name, blog=True):
    """Paper at 200 dpi; blog at 1800 px wide."""
    fig.savefig(os.path.join(PA, "f_" + name + ".png"), dpi=200, facecolor=fig.get_facecolor())
    if blog:
        fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=1800 / fig.get_size_inches()[0], facecolor=fig.get_facecolor())
    plt.close(fig)


def settings_map(ax, k=1.0, labels=True, col=HOT, lw=.3):
    outline(ax, fc=SEA, ec="#C9CDD0"); world(ax, ec=BG, lw=lw)
    K = k * 7.0e5 / np.sqrt(MP.novels.max())
    a = MP[(MP.kind == "area") & (MP.novels > 0)].sort_values("novels", ascending=False)
    x, y = proj(a.lon.values, a.lat.values)
    ax.scatter(x, y, s=(K * np.sqrt(a.novels.values) / 2.2e4) ** 2, fc="none", ec=COOL, lw=.8, alpha=.75, zorder=3)
    c = MP[(MP.kind == "city") & (MP.novels > 0)].sort_values("novels", ascending=False)
    x, y = proj(c.lon.values, c.lat.values)
    ax.scatter(x, y, s=(K * np.sqrt(c.novels.values) / 2.2e4) ** 2, fc=col, ec="#fff", lw=.5, alpha=.82, zorder=4)
    return K


def europe_inset(fig, rect, K, labels=True, col=HOT, fs=8.5):
    """Europe at a larger scale (plate carree with cos 48 degrees), same circle scale x 2.6."""
    ax = fig.add_axes(rect); ax.set_facecolor(SEA)
    cx = np.cos(np.radians(48))
    for iso, _, ring in SHAPES:
        if ring[:, 0].max() < -30 or ring[:, 0].min() > 60 or ring[:, 1].max() < 25: continue
        ax.add_patch(MPoly(np.column_stack([ring[:, 0] * cx, ring[:, 1]]), closed=True, fc=LAND, ec=BG, lw=.5))
    ext = (-11, 31, 35.5, 60.5)
    ax.set_xlim(ext[0] * cx, ext[1] * cx); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color("#AEB4B8")
    s2 = 1.0
    a = MP[(MP.kind == "area") & (MP.novels > 0)]
    ax.scatter(a.lon * cx, a.lat, s=(s2 * K * np.sqrt(a.novels) / 2.2e4) ** 2, fc="none", ec=COOL, lw=.8, alpha=.75, zorder=3)
    c = MP[(MP.kind == "city") & (MP.novels > 0)].sort_values("novels", ascending=False)
    ax.scatter(c.lon * cx, c.lat, s=(s2 * K * np.sqrt(c.novels) / 2.2e4) ** 2, fc=col, ec="#fff", lw=.5, alpha=.82, zorder=4)
    if labels:
        for nm, lon, lat, ha in (("London", 3.0, 55.2, "left"), ("Paris", -5.0, 46.6, "right"), ("Rome", 12.6, 38.9, "center"), ("Madrid", -10.6, 38.2, "left")):
            r = c[c.name == nm].iloc[0]
            ax.text(lon * cx, lat, f"{nm}\n{r.novels:,}", ha=ha, va="center", fontsize=fs, color=FG, path_effects=HALO, zorder=6)
    ax.text(ext[0] * cx + .3, ext[3] - .5, "Europe, enlarged (same circle scale)", fontsize=fs, color=MUT, va="top", path_effects=HALO)
    return ax


# ---------- world map of settings ----------
fig = plt.figure(figsize=(12, 6.8), facecolor=BG); ax = fig.add_axes([0, 0, 1, .89])
K = settings_map(ax)
LAB = {"New York City": (9e5, 2e5, "left"), "Los Angeles": (-7e5, -3e5, "right"),
       "San Francisco": (-8e5, 4e5, "right"), "Pittsburgh": (2e5, 9e5, "center"), "Buenos Aires": (6e5, -3e5, "left"), "Hong Kong": (5e5, -3e5, "left"),
       "Mumbai": (-5e5, -4e5, "right"), "Tokyo": (5e5, 0, "left"), "Cairo": (4e5, -4e5, "left"), "Lagos": (-4e5, -4e5, "right")}
for nm, (dx, dy, ha) in LAB.items():
    r = MP[(MP.kind == "city") & (MP.name == nm)]
    if not len(r): continue
    r = r.iloc[0]; x, y = proj(r.lon, r.lat)
    ax.text(x + dx, y + dy, f"{nm}\n{r.novels:,}", ha=ha, va="center", fontsize=9, color=FG, path_effects=HALO, zorder=6)
fig.text(.02, .962, f"Where {R['source']['novels']:,} novels in Wikidata are set. Circle area: novels set at least partly there", fontsize=10.5, color=FG)
ms = lambda n, k=1: k * K * np.sqrt(n) / 2.2e4
eu = europe_inset(fig, [.015, .06, .27, .37], K)
fig.legend(handles=[Line2D([], [], ls="", marker="o", ms=9, mfc=HOT, mec="#fff", label="city, town or site (places within 25 km of a city merged)"),
                    Line2D([], [], ls="", marker="o", ms=9, mfc="none", mec=COOL, label="wider area (state, island, region)")],
           loc="upper left", ncol=2, frameon=False, fontsize=8.8, bbox_to_anchor=(.012, .945))
for i, n in enumerate((10, 100, 500)):
    xk = 11.2e6 + i * 1.3e6 + (0 if i < 2 else .5e6); r_ = K * np.sqrt(n) / 2.2e4
    ax.scatter([xk], [-7.0e6], s=r_ ** 2, fc=HOT, ec="#fff", lw=.5, zorder=6, clip_on=False)
    ax.text(xk, -8.15e6, f"{n}" + (" novels" if n == 500 else ""), ha="center", fontsize=8.8, color=FG)
both(fig, "map")

# ---------- top cities ----------
CI = R["cities"][:20]
fig = plt.figure(figsize=(11, 6.6), facecolor=BG); ax = fig.add_axes([.2, .06, .76, .84]); ax.set_facecolor(BG)
nm = [c["name"] for c in CI][::-1]; v = [c["n"] for c in CI][::-1]; va = [c["all"] for c in CI][::-1]
ax.barh(nm, va, color="none", ec=MUT, lw=.8, height=.72, label="all literary works")
ax.barh(nm, v, color=HOT, height=.72, label="novels")
for i, (a, b) in enumerate(zip(v, va)):
    ax.text(max(a, b) + 8, i, f"{a:,}" + (f"  ({b:,} works)" if b > a else ""), va="center", fontsize=9)
spines(ax); ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=10)
ax.set_xlim(0, max(va) * 1.22)
ax.legend(loc="lower right", frameon=False, fontsize=10)
ax.set_title("City areas with the most novels set there (bars) and all literary works (outlines)", loc="left", fontsize=11.5, color=FG)
both(fig, "cities")

# ---------- London, Paris, New York by twenty-year period ----------
T = pd.DataFrame(R["trio20"])
fig = plt.figure(figsize=(11, 5.2), facecolor=BG); ax = fig.add_axes([.08, .16, .9, .74]); ax.set_facecolor(BG)
xs = np.arange(len(T))
for k, c in TRIO:
    ax.plot(xs, T[k + "_pct"], "-o", color=c, lw=2.8, ms=6, label=k)
spines(ax); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
ax.set_ylabel("% of novels with a mapped place"); ax.set_ylim(0, 50); ax.set_xlim(-.3, len(T) - .7)
ax.set_xticks(xs); ax.set_xticklabels([f"{r['from']} to {r['to']}\n{r['n']:,} novels" for r in T.to_dict("records")], fontsize=9)
ax.legend(loc="upper right", frameon=False, fontsize=11, ncol=3)
ax.set_title("Share of novels set in each city, by publication period", loc="left", fontsize=11.5)
both(fig, "trio")

# ---------- home and abroad ----------
DI = pd.read_csv(f"{DATA}/novel_distances.csv")
H = [r for r in R["home_by_country"] if r["n"] >= 40]
H = sorted(H, key=lambda r: -r["abroad_pct"])[:18]
fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 5.8), facecolor=BG, gridspec_kw={"width_ratios": [1, 1.05]})
fig.subplots_adjust(left=.07, right=.97, wspace=.42, top=.86, bottom=.12)
a1.hist(DI.km.clip(lower=.5), bins=np.logspace(-0.3, np.log10(20100), 34), color=COOL, ec=BG, lw=.5)
a1.set_xscale("log"); a1.set_facecolor(BG); spines(a1)
a1.set_xticks([1, 10, 100, 1000, 10000]); a1.set_xticklabels(["1", "10", "100", "1,000", "10,000"])
a1.set_xlabel("km from the author's birthplace to the setting"); a1.set_ylabel("novel and place pairs")
med = R["home"]["median_km"]; a1.axvline(med, color=FG, lw=1, ls="--")
a1.text(med * 1.15, a1.get_ylim()[1] * .93, f"median\n{med:,} km", fontsize=9.5, va="top")
a1.set_title("How far from home", loc="left", fontsize=11.5)
nm = [r["name"] for r in H][::-1]; v = [r["abroad_pct"] for r in H][::-1]
a2.barh(nm, v, color=HOT, height=.68); a2.set_facecolor(BG); spines(a2); a2.set_xlim(0, 108); a2.tick_params(axis="y", length=0, labelsize=9.5)
for i, r in enumerate(H[::-1]):
    a2.text(r["abroad_pct"] + 1.5, i, f"{r['abroad_pct']:.0f}%  (n={r['n']:,})", va="center", fontsize=8.5)
a2.set_xticks([]); a2.spines["bottom"].set_visible(False)
a2.set_title("Novels set at least partly abroad,\nby the author's country of birth", loc="left", fontsize=11.5)
both(fig, "home")

# ---------- continents vs population ----------
CL = [c for c in R["continents_list"] if c["cont"] != "Antarctica"]
fig = plt.figure(figsize=(11, 4.8), facecolor=BG); ax = fig.add_axes([.16, .12, .8, .74]); ax.set_facecolor(BG)
y = np.arange(len(CL))[::-1]
ax.barh(y + .19, [c["novels_pct"] for c in CL], height=.36, color=HOT, label="share of novels set there")
ax.barh(y - .19, [c["pop_pct"] for c in CL], height=.36, color="#B9B2A6", label="share of world population")
for yy, c in zip(y, CL):
    ax.text(c["novels_pct"] + .8, yy + .19, f"{c['novels_pct']:.0f}%", va="center", fontsize=9.5, color=HOT)
    ax.text(c["pop_pct"] + .8, yy - .19, f"{c['pop_pct']:.0f}%", va="center", fontsize=9.5, color=MUT)
ax.set_yticks(y); ax.set_yticklabels([c["cont"] for c in CL]); spines(ax); ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=11)
ax.set_xlim(0, 70); ax.legend(loc="lower right", frameon=False, fontsize=10)
ax.set_title("Where novels are set, against where people live", loc="left", fontsize=11.5)
both(fig, "conts")

# ---------- coverage bias: distinct places ----------
BT = R["bias_top"][:12]
fig = plt.figure(figsize=(11, 5.6), facecolor=BG); ax = fig.add_axes([.2, .08, .76, .8]); ax.set_facecolor(BG)
nm = [b["name"] for b in BT][::-1]; v = [b["places"] for b in BT][::-1]
cols = [HOT if b["iso"] in ("DNK", "SRB") else "#8C8478" for b in BT][::-1]
ax.barh(nm, v, color=cols, height=.7)
for i, b in enumerate(BT[::-1]):
    ax.text(b["places"] + 6, i, f"{b['places']:,} places  ·  {b['pop_pct']:.2f}% of world population", va="center", fontsize=9, color=FG)
spines(ax); ax.set_xticks([]); ax.spines["bottom"].set_visible(False); ax.tick_params(axis="y", length=0, labelsize=10.5); ax.set_xlim(0, max(v) * 1.75)
ax.set_title("Distinct setting places in each country, all literary works", loc="left", fontsize=11.5)
both(fig, "bias")

# ---------- genres: top cities ----------
G = R["genres_list"][:6]
fig, axs = plt.subplots(2, 3, figsize=(12, 6.6), facecolor=BG); fig.subplots_adjust(left=.11, right=.98, wspace=.85, hspace=.42, top=.9, bottom=.04)
for ax, g in zip(axs.flat, G):
    rows = g["cities"][:6][::-1]; ax.set_facecolor(BG)
    ax.barh([r[0] for r in rows], [r[1] for r in rows], color=GCOL[g["genre"]], height=.66)
    for i, r in enumerate(rows): ax.text(r[1] + max(x[1] for x in rows) * .03, i, str(r[1]), va="center", fontsize=9)
    ax.set_title(f"{g['genre']}\n{g['n']:,} novels", loc="left", fontsize=10.5); spines(ax); ax.set_xticks([]); ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=9.5); ax.set_xlim(0, max(x[1] for x in rows) * 1.25)
both(fig, "genres")

# ---------- novels per decade (paper only) ----------
ND = pd.DataFrame(R["novels_by_decade"]); ND = ND[ND.dec >= 1750]
fig = plt.figure(figsize=(11, 3.8), facecolor=BG); ax = fig.add_axes([.07, .15, .9, .74]); ax.set_facecolor(BG)
ax.bar(ND.dec + 5, ND.n, width=8.4, color=NAVY); spines(ax); ax.set_ylabel("novels"); ax.grid(axis="y", color=RULE); ax.set_axisbelow(True)
ax.set_title("Novels in the data by decade of first publication", loc="left", fontsize=11)
both(fig, "decades", blog=False)

# ---------- header card 1200 x 630 ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([.36, .14, .64, .78]); settings_map(ax, k=.8, lw=.2)
fig.text(.04, .86, "Where", fontproperties=DISP, fontsize=58, color=FG, va="top")
fig.text(.04, .70, "novels", fontproperties=DISP, fontsize=58, color=HOT, va="top")
fig.text(.04, .54, "are set", fontproperties=DISP, fontsize=58, color=COOL, va="top")
fig.text(.04, .35, f"{R['source']['novels']:,} novels set in {R['source']['places_novels']:,} real\nplaces, from Wikidata. London, New York and Paris\nlead; most of the world is barely written.", fontproperties=SERP, fontsize=14, color=FG, va="top", linespacing=1.35)
fig.text(.04, .04, "maps.tristanhotham.com/novel-settings", fontsize=11, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
plt.close(fig)
print("figures done", sorted(os.listdir(BL)), sorted(x for x in os.listdir(PA) if x.endswith(".png")))
