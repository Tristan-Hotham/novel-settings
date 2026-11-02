# Where novels are set: mapping the real places of fiction in Wikidata

A world map and analysis of the narrative locations Wikidata records for 13,218 literary works, 7,300 of them novels, set in 4,057 real places: the cities fiction favours, London, Paris and New York over two centuries, how far authors travel from where they were born, the parts of the world that are barely written, and how much the picture depends on who has catalogued what.

Interactive page: https://maps.tristanhotham.com/novel-settings/
Paper: https://doi.org/10.5281/zenodo.23872997
Blog post: https://blog.tristanhotham.com/2026/10/31/novel-settings/

## Headline results

- Cities: London has 549 novels set at least partly there, New York 510, Paris 422; together they appear in 20% of all novels. Counting all literary works, Paris leads (877). Then Los Angeles 140, San Francisco 136, Rome 126, Madrid 104 and Pittsburgh 98. Mumbai has 4, Lagos 3.
- Over time: Paris is the setting of 44% of mapped novels first published 1830 to 1849; London leads 1910 to 1949, New York 1950 to 1989 (15% in 1950 to 1969), London again since 1990.
- Home and abroad: of 6,654 novels with an author birthplace and a setting country, 69% are set entirely in the present-day country of the author's birth. Median distance from birthplace to setting 343 km; 25% of settings within 50 km. The longest journey: Ngaio Marsh, Christchurch to Devon (19,174 km).
- Genres: crime and mystery (869 novels) is led by Paris, London and New York; science fiction is 3.5 times as likely as the average novel to be set in San Francisco. 25 works are set on the Moon.
- Continents: Europe has 10% of the world's people and 54% of the novels; Asia 60% and 9%; Africa 17% and 5%.
- Coverage: Denmark holds 476 distinct setting places (11.7% of all, more than any country) with 0.08% of world population; China and India together have 110. Serbia has 137. Works in Danish list 3.0 settings each, in English 1.1.
- Extremes: the most remote real setting is the South Pole (5,802 km from a city of a million); the most written-about street is Istedgade, Copenhagen (4 works).

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/04_build_site.py`; page data embedded, `data/points.json` loaded by the page). MapLibre GL JS. |
| `header.png` | Social card, 1200 x 630. |
| `data/works.csv` | All 13,218 works with an Earth setting: Wikidata ID, title, year, novel flag, forms, classes, genres, genre groups, countries of origin, languages, authors, sitelinks, English Wikipedia article, number of places. |
| `data/places.csv` | All 4,057 places: Wikidata ID, label, coordinates, level, fictional flag, classes, present-day country, continent, city area, km to the nearest city of a million, works and novels. |
| `data/work_places.csv` | Every work and place pair (16,926), with level, country and city area. |
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

- Population: every Wikidata item that is an instance of a subclass of literary work (Q7725634) with a narrative location (P840) whose item has coordinates (P625); QLever extract, 2026. 33 settings on the Moon or Mars are counted, not mapped.
- Novel: form of creative work (P7937) novel or novella, or a class whose label contains "novel"; except the 67 tales of the Decameron and the Odyssey (form given as novel), which stay literary works.
- Places: levels from Wikidata classes: city (1720), site or part of a city (1098), wider area (839), country (342), continent or ocean (58). Only the first three are points. Fictional and phantom places (15) are flagged. Country = present-day Natural Earth country of the point. City area = everything within 25 km of a Natural Earth place of 250,000+.
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

Hotham, T. (2026) Where novels are set: mapping the real places of fiction in Wikidata. Zenodo. https://doi.org/10.5281/zenodo.23872997

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
