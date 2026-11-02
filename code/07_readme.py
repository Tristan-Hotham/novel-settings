"""README.md, LICENSE and reddit/post.md, with numbers from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json")
s, sp, hm, co, b, lv = R["source"], R["spot"], R["home"], R["continents"], R["bias"], R["levels"]
T20 = R["trio20"]
N = lambda v: f"{round(v):,}"
readme = f"""# Where novels are set: mapping the real places of fiction in Wikidata

A world map and analysis of the narrative locations Wikidata records for {N(s['works'])} literary works, {N(s['novels'])} of them novels, set in {N(s['places'])} real places: the cities fiction favours, London, Paris and New York over two centuries, how far authors travel from where they were born, the parts of the world that are barely written, and how much the picture depends on who has catalogued what.

Interactive page: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}

## Headline results

- Cities: London has {sp['London']['n']} novels set at least partly there, New York {sp['New York City']['n']}, Paris {sp['Paris']['n']}; together they appear in {R['city_top3_pct']:.0f}% of all novels. Counting all literary works, Paris leads ({sp['Paris']['all']}). Then Los Angeles {sp['Los Angeles']['n']}, San Francisco {sp['San Francisco']['n']}, Rome {sp['Rome']['n']}, Madrid {sp['Madrid']['n']} and Pittsburgh {sp['Pittsburgh']['n']}. Mumbai has {sp['Mumbai']['n']}, Lagos {sp['Lagos']['n']}.
- Over time: Paris is the setting of {T20[0]['Paris_pct']:.0f}% of mapped novels first published 1830 to 1849; London leads 1910 to 1949, New York 1950 to 1989 ({T20[6]['New York_pct']:.0f}% in 1950 to 1969), London again since 1990.
- Home and abroad: of {N(hm['n'])} novels with an author birthplace and a setting country, {hm['home_pct']:.0f}% are set entirely in the present-day country of the author's birth. Median distance from birthplace to setting {N(hm['median_km'])} km; {hm['within_50']:.0f}% of settings within 50 km. The longest journey: Ngaio Marsh, Christchurch to {R['farthest'][0]['place']} ({N(R['farthest'][0]['km'])} km).
- Genres: crime and mystery ({R['genres']['Crime and mystery']['n']} novels) is led by Paris, London and New York; science fiction is {R['genres']['Science fiction']['lift'][0][2]:.1f} times as likely as the average novel to be set in San Francisco. {R['offworld']['moon_works']} works are set on the Moon.
- Continents: Europe has {co['Europe']['pop_pct']:.0f}% of the world's people and {co['Europe']['novels_pct']:.0f}% of the novels; Asia {co['Asia']['pop_pct']:.0f}% and {co['Asia']['novels_pct']:.0f}%; Africa {co['Africa']['pop_pct']:.0f}% and {co['Africa']['novels_pct']:.0f}%.
- Coverage: Denmark holds {b['DNK']['places']} distinct setting places ({b['DNK']['places_pct']:.1f}% of all, more than any country) with {b['DNK']['pop_pct']:.2f}% of world population; China and India together have {b['dnk_vs']['chn_ind_places']}. Serbia has {b['SRB']['places']}. Works in Danish list {R['bias_lang'][6]['per_work']:.1f} settings each, in English {R['bias_lang'][0]['per_work']:.1f}.
- Extremes: the most remote real setting is the {R['remote'][0]['label']} ({N(R['remote'][0]['km'])} km from a city of a million); the most written-about street is {R['streets'][0]['label']}, {R['streets'][0]['city']} ({R['streets'][0]['works']} works).

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/points.json` loaded by the page). MapLibre GL JS. |
| `header.png` | Social card, 1200 x 630. |
| `data/works.csv` | All {N(s['works'])} works with an Earth setting: Wikidata ID, title, year, novel flag, forms, classes, genres, genre groups, countries of origin, languages, authors, sitelinks, English Wikipedia article, number of places. |
| `data/places.csv` | All {N(s['places'])} places: Wikidata ID, label, coordinates, level, fictional flag, classes, present-day country, continent, city area, km to the nearest city of a million, works and novels. |
| `data/work_places.csv` | Every work and place pair ({N(s['pairs'])}), with level, country and city area. |
| `data/novel_distances.csv` | Novel and point-setting pairs with the distance from the nearest author's birthplace. |
| `data/cities.csv` | City areas with novels and works. |
| `data/london_paris_newyork_by_decade.csv` | Novels with a mapped place per decade and the number and share set in each of the three cities. |
| `data/home_abroad_by_birth_country.csv` | Share of novels set abroad and median distance, by present-day country of the author's birthplace. |
| `data/continents.csv` | Novels and works by continent, with population shares. |
| `data/coverage_by_country.csv` | Distinct places, settings, works and novels by country, with population share. |
| `data/most_famous_novel_by_country.csv` | The best-known novel (by sitelinks) set at least partly in each country. |
| `data/map_points.csv` | City areas and wider areas with novels and works (for the figures). |
| `data/results.json` | Every number used in the page, paper, blog, collage and post. |
| `data/site.json`, `data/points.json`, `data/world.json`, `data/cities.json` | Page data. |
| `raw/` | The Wikidata extracts (QLever TSV, CC0). |
| `code/` | Scripts, run in order (below), and the page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures (`paper/`), blog post, figures and meta (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |
| `qa/` | Screenshots of the page at desktop and phone widths. |

## Method in brief

- Population: every Wikidata item that is an instance of a subclass of literary work (Q7725634) with a narrative location (P840) whose item has coordinates (P625); QLever extract, {s['extract_year']}. {s['offworld_pairs']} settings on the Moon or Mars are counted, not mapped.
- Novel: form of creative work (P7937) novel or novella, or a class whose label contains "novel"; except the {s['decameron']} tales of the Decameron and the Odyssey (form given as novel), which stay literary works.
- Places: levels from Wikidata classes: city ({lv['places']['city']}), site or part of a city ({lv['places']['site']}), wider area ({lv['places']['region']}), country ({lv['places']['country']}), continent or ocean ({lv['places']['large']}). Only the first three are points. Fictional and phantom places ({s['fictional_places']}) are flagged. Country = present-day Natural Earth country of the point. City area = everything within 25 km of a Natural Earth place of 250,000+.
- Home and abroad: the present-day country of the author's birthplace coordinates (P19). Distance to the nearest author's birthplace, point settings only.
- Caveats: this maps what Wikidata records; coverage depends on volunteers and projects (Denmark, Serbia, Pittsburgh), English labels and Wikipedia; settings are partial; birthplace is not nationality.

## How to rerun

Needs Python 3 with numpy, pandas, shapely, pyproj, matplotlib, Pillow and fontTools, xelatex and pdftotext; node with Playwright (and a local maplibre-gl 4.7.1) for `code/qa.js`. Raw inputs are in `raw/`; Natural Earth in `/home/claude/newdata/raw/geo/` (paths in `code/common.py`). Intermediate files go to `/dev/shm/novelsettings/work` (set `NSTMP` to change).

```
python3 code/01_parse.py        # works, places, pairs, authors
python3 code/02_geo.py          # outlines, place levels, countries, city areas, author birth countries
python3 code/03_results.py      # results.json, data tables, page data
python3 code/04_build_site.py   # index.html (with checks of facts stated in words)
python3 code/05_figures.py      # header, blog and paper figures
python3 code/06_paper.py        # paper PDF
python3 reddit/collage.py       # collage
python3 code/07_readme.py       # README, LICENSE, Reddit post
python3 code/08_release.py      # blog post, Zenodo files
```

## Sources and licences

- Wikidata, https://www.wikidata.org/. CC0. Queried with QLever.
- Natural Earth countries, land and populated places (https://www.naturalearthdata.com/). Public domain.
- Relief tiles on the page: Esri World Hillshade.

## Citation

Hotham, T. (2026) Where novels are set: mapping the real places of fiction in Wikidata. Zenodo. https://doi.org/{DOI}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)

lic = open("/home/claude/studies/meteorite-falls/LICENSE", encoding="utf-8").read().split("\n\n\nThis licence covers")[0]
lic += """


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, paper and blog post, the figures and the derived data
files in data/ are released under CC BY 4.0. The settings data come from
Wikidata (https://www.wikidata.org/), which is CC0; the extracts in raw/ are
Wikidata data and are likewise CC0. Natural Earth is public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)

post = f"""## Title

[OC] I mapped where {N(s['novels'])} novels are set. London ({sp['London']['n']}), New York ({sp['New York City']['n']}) and Paris ({sp['Paris']['n']}) dominate; Mumbai, a city of {sp['Mumbai']['pop_m']:.0f} million, has {sp['Mumbai']['n']}

## Body

Wikidata records the real narrative locations of thousands of books, so I put every literary work with a mapped setting on one map: {N(s['works'])} works, {N(s['novels'])} of them novels, in {N(s['places'])} places. Three cities appear in {R['city_top3_pct']:.0f}% of the novels. Paris led in the age of Balzac ({T20[0]['Paris_pct']:.0f}% of mapped novels published 1830 to 1849), New York from 1950 to 1989, London since 1990. Authors mostly stay home: the median distance from an author's birthplace to the setting is {N(hm['median_km'])} km. Europe has {co['Europe']['pop_pct']:.0f}% of the world's people and {co['Europe']['novels_pct']:.0f}% of the novels; Asia {co['Asia']['pop_pct']:.0f}% and {co['Asia']['novels_pct']:.0f}%. Big caveat, and part of the story: this maps what volunteers have catalogued. Denmark alone has {b['DNK']['places']} setting places, more than China and India together ({b['dnk_vs']['chn_ind_places']}), thanks to a very thorough Danish effort, and Pittsburgh ranks eighth in the world. Interactive map with search by book or author, genre and period filters, and lines from each author's birthplace: {PAGE}

## Source comment

Source: Wikidata (CC0), narrative location (P840) with coordinates for every literary work, plus authors' birthplaces (P19), publication dates, genres and forms, queried with QLever. Novel = form novel or novella, or a class named novel. City areas merge places within 25 km of a city of 250,000+. Outlines and populations: Natural Earth.

Tools: Python (pandas, shapely, pyproj, matplotlib); MapLibre for the interactive map.

Interactive version: {PAGE}
Paper: https://doi.org/{DOI}
Blog post: {BLOG}
"""
for t in (readme, post):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in t.replace("```", "").replace("|---|---|", ""), bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("readme, licence, post ok")
