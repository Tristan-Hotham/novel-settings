"""Build index.html from code/page_template.html. Every number in the text is a {{path|format}} token filled from
data/results.json; page data (results, site.json, world.json, cities) is embedded and data/points.json is loaded by the
page. Facts stated in words (orders, names, 'more than') are checked here. The full-screen map snippet
(code/fullscreen_snippet.html) is pasted before </body>. 10.5281/zenodo.23872997 and https://blog.tristanhotham.com/2026/10/31/novel-settings/ stay as placeholders for the publisher."""
import json
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")
SP, CO, G, HC, AF = R["spot"], R["continents"], R["genres"], R["home_country"], R["author_facts"]
T20 = R["trio20"]

# facts stated in words (page, blog, paper, collage)
assert [c["name"] for c in R["cities"][:10]] == ["London", "New York City", "Paris", "Los Angeles", "San Francisco", "Rome", "Madrid", "Pittsburgh", "Chicago", "Boston"]
assert [c["name"] for c in R["cities_all"][:3]] == ["Paris", "New York City", "London"]
assert SP["Pittsburgh"]["rank"] == 8 and SP["Mumbai"]["n"] < 10 and SP["Lagos"]["n"] < 10
assert AF["Benito Pérez Galdós"]["top_city"] == "Madrid" and AF["Rex Stout"]["top_city"] == "New York City" and AF["Georges Simenon"]["top_city"] == "Paris"
assert AF["Georges Simenon"]["born"] == "Belgium" and AF["Simon Scarrow"]["born"] == "Nigeria" and AF["Simon Scarrow"]["top_country"] == "Italy"
assert AF["Ngaio Marsh"]["born"] == "New Zealand" and AF["Ngaio Marsh"]["top_country"] == "United Kingdom" and AF["P L Travers"]["top_city_n"] == AF["P L Travers"]["novels"]
assert R["farthest"][0]["author"] == "Ngaio Marsh" and [a["author"] for a in R["authors_far"][:2]] == ["Ngaio Marsh", "P. L. Travers"]
# trio: Paris first in 1830 to 1849; London and Paris level 1890 to 1909; London leads 1910 to 1949; New York 1950 to 1989; London since 1990
best = lambda t: max(("London", "Paris", "New York"), key=lambda k: t[k + "_pct"])
assert T20[0]["from"] == 1830 and best(T20[0]) == "Paris" and T20[3]["London"] == T20[3]["Paris"]
assert best(T20[4]) == best(T20[5]) == "London" and best(T20[6]) == best(T20[7]) == "New York" and best(T20[8]) == best(T20[9]) == "London"
assert T20[6]["from"] == 1950 and T20[8]["from"] == 1990 and T20[8]["Paris_pct"] < 6
assert HC["UKR"]["abroad_pct"] == max(r["abroad_pct"] for r in R["home_by_country"]) and R["home_by_country"][1]["iso"] == "BEL"
assert HC["BEL"]["top_abroad"][0][0] == "France" and HC["NGA"]["top_abroad"][0][0] == "Italy"
cr = G["Crime and mystery"]
assert cr["n"] == max(g["n"] for g in R["genres_list"]) and [c[0] for c in cr["cities"][:3]] == ["Paris", "London", "New York City"]
assert {"Miami", "Oslo", "Edinburgh", "Venice"} <= {l[0] for l in cr["lift"][:4]}
assert G["Science fiction"]["lift"][0][0] == "San Francisco" and [c[0] for c in G["Science fiction"]["cities"][:2]] == ["New York City", "London"]
assert G["Fantasy"]["cities"][0][0] == "London" and [G["Historical"]["cities"][i][0] for i in (0, 1, 3)] == ["Paris", "London", "Rome"]
assert R["offworld"]["mars_works"] >= 1 and any(o["title"] == "The Martian" for o in R["offworld"]["examples"])
assert CO["Europe"]["novels_pct"] > 50 and CO["Asia"]["pop_pct"] > 55 and CO["Asia"]["novels_pct"] < 10
assert R["undermapped"][0]["name"] == "Bangladesh" and R["undermapped"][4]["name"] == "Pakistan"
assert R["bias_top"][0]["iso"] == "DNK" and R["bias_top"][1]["iso"] == "USA" and R["bias_top"][7]["iso"] == "SRB"
assert R["bias"]["CHN"]["pop_pct"] + R["bias"]["IND"]["pop_pct"] > 100 / 3 and R["bias"]["dnk_vs"]["chn_ind_places"] < R["bias"]["DNK"]["places"]
assert R["bias_lang"][6]["lang"] == "Danish" and R["bias_lang"][0]["lang"] == "English" and R["bias_lang"][7]["lang"] == "Serbian"
assert [m["title"] for m in R["most_linked"][:4]] == ["Don Quixote", "Nineteen Eighty-Four", "Animal Farm", "Dream of the Red Chamber"]
assert R["famous"]["ESP"]["title"] == "Don Quixote" and R["famous"]["GBR"]["title"] == "Nineteen Eighty-Four" and R["famous"]["CHN"]["title"] == "Dream of the Red Chamber"
assert R["famous"]["VEN"]["title"] == "Robinson Crusoe" and R["famous"]["EGY"]["title"] == "The Alchemist"
assert R["remote"][0]["label"] == "South Pole" and R["south"][0]["label"] == "South Pole" and R["north"][0]["label"] == "North Pole"
assert {w["title"] for w in R["remote"][0]["works"]} == {"An Antarctic Mystery", "Twenty Thousand Leagues Under the Sea"}
assert R["remote"][1]["label"] == "Marquesas Islands" and "Stevenson" in R["remote"][1]["works"][1]["author"]
assert all(r["iso"] in ("PYF", "FRA") for r in R["remote"][1:5])
assert R["north"][0]["works"][1]["author"] == "Jules Verne"
assert R["streets"][0]["city"] == "Copenhagen" and R["buildings"][0]["label"] == "Auschwitz" and any(w["title"] == "The Zone of Interest" for w in R["buildings"][0]["examples"])
assert {"Arkham", "R'lyeh", "Starfleet Academy", "221B Baker Street"} <= {f["label"] for f in R["fictional"]}
assert R["source"]["decameron"] > 50 and R["countries_none_n10m"] >= 1


def fill(tpl, keep=("DOI", "BLOG_URL")):
    neg = "|".join(re.escape(k) + r"\}\}" for k in keep)
    return re.sub(r"\{\{(?!" + neg + r")([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), tpl)


def build():
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl)
    left = re.findall(r"\{\{[^}]*\}\}", html)
    assert set(left) <= {"10.5281/zenodo.23872997", "https://blog.tristanhotham.com/2026/10/31/novel-settings/"}, left[:5]
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    html = html.replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*WORLD*/", open(f"{DATA}/world.json", encoding="utf-8").read())
    html = html.replace("/*CITIES*/", J([{"name": x["name"], "lat": x["lat"], "lon": x["lon"], "pop": x["pop"]} for x in jload(f"{DATA}/cities.json")]))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
        assert bad not in vis, bad
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–"):
            assert bad not in scr, bad
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
