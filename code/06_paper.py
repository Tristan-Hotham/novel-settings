"""Build the paper: fill code/paper_template.tex from data/results.json, add tables, compile with xelatex.
Output: release/paper/<NAME>.pdf and .tex (figures f_*.png sit beside them). The DOI stays as the 10.5281/zenodo.23872997 placeholder."""
import subprocess
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(ROOT, "release", "paper"); NAME = "Hotham_Where_Novels_Are_Set"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")

# statements made in words in the paper only
HB = R["home_by_country"]
assert [r["iso"] for r in HB[:3]] == ["UKR", "BEL", "AUS"]
assert [c[0] for c in R["genres"]["Historical"]["countries"][:3]] == ["United States", "United Kingdom", "Italy"]
assert [c[0] for c in R["genres"]["Historical"]["cities"][:3]] == ["Paris", "London", "New York City"]
assert 18 < R["city_top3_pct"] < 22                                                    # "about a fifth"
assert [r["name"] for r in R["undermapped"][:5]] == ["Bangladesh", "Philippines", "Democratic Republic of the Congo", "Myanmar", "Pakistan"]
assert R["remote"][1]["iso"] == "PYF" and R["north"][0]["label"] == "North Pole"


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "pc": return f"{round(float(v))}\\%"
    if f == "pc1": return f"{float(v):.1f}\\%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    return tex(str(v))


rows = "".join(f"{i + 1} & {tex(c['name'])} & {tex(c['country'])} & {c['n']:,} & {c['all']:,}\\\\\n" for i, c in enumerate(R["cities"][:20]))
TC = ("\\begin{table}[tbp]\\centering\\small\\caption{The twenty city areas with the most novels set at least partly in them, and all literary works.}\\label{tab:cities}"
      "\\begin{tabular}{rllrr}\\toprule & City area & Country & Novels & All works\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(r['name'])} & {r['n']:,} & {r['abroad_pct']:.1f}\\% & {r['median_km']:,} & {tex(', '.join(f'{a} {n}' for a, n in r['top_abroad']))}\\\\\n" for r in HB)
TH = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Novels by the present-day country of the author's birthplace (at least 40): share set at least partly abroad, median distance from birthplace to point settings, and the main foreign settings.}\\label{tab:home}"
      "\\begin{tabular}{lrrrp{6cm}}\\toprule Born in & Novels & Abroad & Median km & Main foreign settings\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(c['cont'])} & {c['novels']:,} & {c['novels_pct']:.1f}\\% & {c['works']:,} & {c['pop_pct']:.1f}\\% & {c['per_10m'] if c['per_10m'] is not None else 'n/a'}\\\\\n" for c in R["continents_list"])
TO = ("\\begin{table}[tbp]\\centering\\small\\caption{Novels and literary works set at least partly in each continent, share of world population, and novels per 10 million people (not given for Antarctica).}\\label{tab:conts}"
      "\\begin{tabular}{lrrrrr}\\toprule Continent & Novels & Share & Works & Population & Per 10m\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
F = sorted(R["famous"].values(), key=lambda f: (-f["n"], f["country"]))[:40]
rows = "".join(f"{tex(f['country'])} & {f['n']:,} & {tex(f['title'])} & {tex(f['author'])} & {f['year'] or ''} & {f['links']}\\\\\n" for f in F)
TF = ("{\\footnotesize\\setlength{\\tabcolsep}{4pt}\\begin{longtable}{lrp{5.2cm}p{3.6cm}rr}\\caption{The best-known novel (by Wikipedia language editions) set at least partly in each of the forty countries with the most mapped novels.}\\label{tab:famous}\\\\"
      "\\toprule Country & Novels & Best-known novel & Author & Year & Links\\\\\\midrule\\endfirsthead\\toprule Country & Novels & Best-known novel & Author & Year & Links\\\\\\midrule\\endhead\n" + rows + "\\bottomrule\\end{longtable}}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{(?!TABLE_|meta\.doi)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
for k, v in (("CITIES", TC), ("HOME", TH), ("CONTS", TO), ("FAMOUS", TF)):
    t = t.replace("{{TABLE_%s}}" % k, v)
t = t.replace("\\href{https://doi.org/{{meta.doi}}}{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
t = t.replace("\\url{https://doi.org/{{meta.doi}}}", "https://doi.org/\\{\\{DOI\\}\\}")
assert "{{" not in t and "--" not in t and "\u2014" not in t and "\u2013" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:4]
for bad in ("DSIT", "DCMS", "civil serv"):
    assert bad not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
