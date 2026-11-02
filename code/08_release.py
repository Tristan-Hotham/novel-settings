"""Blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.23872997, https://doi.org/10.5281/zenodo.23872997 and https://blog.tristanhotham.com/2026/10/31/novel-settings/ stay as placeholders for the publisher."""
import json as _json, shutil, zipfile, importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release"); NAME = "Hotham_Where_Novels_Are_Set"

# the page build checks the shared facts; these are statements written in words in the blog and alt text only
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "04_build_site.py")); spec.loader.exec_module(importlib.util.module_from_spec(spec))
assert 23 < R["home"]["within_50"] < 27                                                     # "a quarter of all settings"
H = R["dist_hist"]["n"]; assert H.index(max(H)) == 8 and H[0] > H[1]                         # peaks under 1 km and at 200 to 500 km
assert R["genres"]["Horror and gothic"]["cities"][0][0] == "London" and R["genres"]["Children and young adult"]["cities"][0][0] == "London"
assert [b["name"] for b in R["bias_top"][2:7]] == ["Germany", "France", "Italy", "United Kingdom", "Spain"]
assert "ITA" in R["home_country"] and R["home_country"]["USA"]["abroad_pct"] < 25

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG\||DOI_URL\}\}|BLOG_URL\}\}|DOI\}\})([^}|]+)(\|(\w+))?\}\}", lambda m: fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u), post, re.M) for u in used) and "wp:image" not in post
from PIL import Image
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{[^|}]+\}\}", post)) <= {"https://doi.org/10.5281/zenodo.23872997"}, set(re.findall(r"\{\{[^|}]+\}\}", post))
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
s, sp = R["source"], R["spot"]
meta = {"title": "Where novels are set: a map of fiction's real places",
        "slug": "novel-settings",
        "excerpt": f"I mapped the real settings of {s['novels']:,} novels in Wikidata. London, New York and Paris dominate, most authors stay within a few hundred kilometres of where they were born, and Denmark has more mapped places than China and India together.",
        "seo_description": f"A map of where {s['novels']:,} novels are set: London, Paris and New York over two centuries, how far authors travel, and the unwritten world.",
        "tags": ["literature", "novels", "maps", "data visualisation", "Wikidata", "literary geography", "London", "Paris", "New York"],
        "header_alt": f"Title card reading 'Where novels are set' in black, red and blue on pale paper, beside a world map with red circles for the settings of novels, the largest on London, Paris and New York, a dense cluster over Europe and only scattered small circles across Asia, Africa and South America. Text: {s['novels']:,} novels set in {s['places_novels']:,} real places, from Wikidata."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/novel-settings_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for d in ("code", "data", "raw"):
        for fn in sorted(os.listdir(os.path.join(ROOT, d))):
            if fn.endswith(".pyc") or fn == "__pycache__":
                continue
            z.write(os.path.join(ROOT, d, fn), f"novel-settings/{d}/{fn}")
    for fn in ("README.md", "LICENSE"):
        z.write(os.path.join(ROOT, fn), f"novel-settings/{fn}")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), "novel-settings/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&")
zmeta = {"title": "Where Novels Are Set: Mapping the Real Places of Fiction in Wikidata",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {BLOG}.</p><p>Settings data: Wikidata (CC0), queried with QLever in {EXTRACT_YEAR}.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["literary geography", "novels", "narrative location", "fictional settings", "Wikidata", "distant reading", "digital humanities", "open data", "maps"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://www.wikidata.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj and "DSIT" not in sj and "DCMS" not in sj
jsave(zmeta, f"{Z}/metadata.json", indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
