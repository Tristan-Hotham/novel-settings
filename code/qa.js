// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server 8798; set PORT to change).
// MapLibre comes from a local npm copy (the CDN is not reachable from the build container); relief tiles and fonts are blocked.
// NOLIB=1 also blocks MapLibre to check that the page degrades gracefully.
const { chromium } = require("playwright");
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
(async () => {
  const fs = require("fs"); fs.mkdirSync("qa", { recursive: true });
  const b = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  const errs = [];
  const sizes = process.env.ONLY ? [[process.env.ONLY, process.env.ONLY === "phone" ? 390 : 1280, 860]] : [["desktop", 1280, 900], ["phone", 390, 844]];
  for (const [nm, vw, vh] of sizes) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic/, r => r.abort());
    if (process.env.NOLIB) await p.route(/maplibre-gl/, r => r.abort());
    else {
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.js/, r => r.fulfill({ path: ML + "/maplibre-gl.js", contentType: "application/javascript" }));
      await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.css/, r => r.fulfill({ path: ML + "/maplibre-gl.css", contentType: "text/css" }));
    }
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource/.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + (process.env.PORT || 8798) + "/index.html", { waitUntil: "networkidle" });
    await p.waitForTimeout(2500);
    const tag = process.env.NOLIB ? "nolib_" : "";
    await p.screenshot({ path: `qa/${tag}${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(700); await p.locator(sel).screenshot({ path: `qa/${tag}${nm}_${f}.png` }); };
    await shot("#atlas", "map");
    if (!process.env.NOLIB) {
      await p.fill("#q", "Ulysses"); await p.waitForTimeout(500); await p.keyboard.press("Enter"); await p.waitForTimeout(2500); await shot("#atlas", "search_ulysses");
      await p.fill("#q", "Ngaio Marsh"); await p.waitForTimeout(500); await p.keyboard.press("Enter"); await p.waitForTimeout(2500); await shot("#atlas", "author_marsh");
      await p.click("#side .back"); await p.waitForTimeout(400);
      await p.click('#genreRow .btn[data-v="0"]'); await p.click('#eraRow .btn[data-v="2"]'); await p.waitForTimeout(1200); await shot("#atlas", "crime_1900");
      await p.click('#genreRow .btn[data-v="-1"]'); await p.click('#eraRow .btn[data-v="-1"]');
      await p.click('#focusRow .btn:nth-child(3)'); await p.waitForTimeout(1800);
      await p.click("#cityChart svg rect:nth-of-type(3)", { force: true }).catch(() => {});
      await p.waitForTimeout(3000); await shot("#atlas", "popup_london");
      await p.click(".lyrBtn"); await p.waitForTimeout(300); await shot("#map", "layers_panel"); await p.click(".lyrBtn");
      await p.click('#kindRow .btn[data-k="0"]'); await p.waitForTimeout(800); await shot("#atlas", "all_works");
    }
    for (const c of ["cityChart", "trioChart", "distChart", "abroadChart", "genreChart", "contChart", "biasChart", "famousTable"]) await shot("#" + c, c);
    if (nm === "phone" && !process.env.NOLIB) {
      await p.click("#theme"); await p.waitForTimeout(1500); await shot("#atlas", "dark_map"); await shot("#trioChart", "dark_trio");
      await p.locator("#atlas").scrollIntoViewIfNeeded(); await p.click(".mfs-btn"); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` });
    }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
