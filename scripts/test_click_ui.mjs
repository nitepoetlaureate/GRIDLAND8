/**
 * Browser smoke test: scan Philly, enable live layers, verify click surfaces show data.
 * Requires: make backend + npm run dev on http://127.0.0.1:5173
 */
import { chromium } from "playwright";

const URL = process.env.GRIDLAND_URL || "http://127.0.0.1:5173";
const TIMEOUT = 180_000;
const SCAN_TIMEOUT = 150_000;

function pass(msg) {
  console.log(`  OK   ${msg}`);
}
function fail(msg) {
  console.log(`  FAIL ${msg}`);
  return msg;
}

async function waitForApi(page, pathPart, timeout = 60_000) {
  return page.waitForResponse(
    (r) => r.url().includes(pathPart) && r.status() === 200,
    { timeout },
  );
}

async function hook(page, fn) {
  return page.evaluate(fn);
}

async function main() {
  const errors = [];
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  page.setDefaultTimeout(TIMEOUT);

  try {
    console.log("=== UI load + auto-scan ===");
    const discoverP = waitForApi(page, "/api/discover");
    const contextP = waitForApi(page, "/api/context");
    await page.goto(URL, { waitUntil: "domcontentloaded" });
    await page.waitForFunction(
      () => window.__gridlandTest?.viewer && document.getElementById("status"),
      { timeout: 90_000 },
    );
    await discoverP;
    await contextP;
    await page.waitForFunction(
      () => {
        const s = document.getElementById("status")?.textContent || "";
        const c = document.getElementById("counts")?.textContent || "";
        return !/connecting|scanning/i.test(s)
          && c.includes("cameras →")
          && !/cameras → 0/.test(c);
      },
      { timeout: SCAN_TIMEOUT },
    );
    pass(`loaded ${URL}`);
    console.log("\n=== Scan Philly (cameras + context) ===");
    const counts = await page.textContent("#counts");
    if (/camera/i.test(counts || "")) pass(`counts: ${(counts || "").trim().slice(0, 80)}`);
    else errors.push(fail(`counts missing cameras: ${counts}`));

    const ctxHtml = await page.innerHTML("#context");
    if (ctxHtml && ctxHtml.length > 40) pass(`context panel: ${ctxHtml.length} chars`);
    else errors.push(fail("context panel empty after scan"));

    console.log("\n=== Camera pin click → info box + feed panel ===");
    const cam = await hook(page, () => {
      const ent = window.__gridlandTest.selectFirstEntity("cameras");
      if (!ent) return { ok: false, reason: "no camera entities" };
      return {
        ok: true,
        id: ent.id,
        hasData: !!(ent.data?.source && ent.data?.lat != null),
        panelHidden: ent.panelHidden,
        panelText: ent.panelText || "",
      };
    });
    if (!cam?.ok) errors.push(fail(`camera: ${cam?.reason}`));
    else if (!cam.panelHidden && /Source|Coordinates/i.test(cam.panelText)) {
      pass(`camera ${cam.id} · ${cam.panelText.slice(0, 70)}`);
    } else {
      errors.push(fail(`camera detail empty hidden=${cam.panelHidden}`));
    }

    console.log("\n=== SEPTA transit layer ===");
    await page.check('input[data-layer="transit"]');
    await waitForApi(page, "/api/septa/vehicles", 45_000).catch(() => null);
    await page.waitForTimeout(10_000);
    const transit = await hook(page, () => {
      const ent = window.__gridlandTest.selectFirstEntity("septa-transit");
      if (!ent) return { ok: false, reason: "no transit entities yet" };
      return {
        ok: true,
        id: ent.id,
        route: ent.name,
        panelHidden: ent.panelHidden,
        panelText: ent.panelText || "",
        hasRoute: !!(ent.data?.route),
      };
    });
    if (!transit?.ok) errors.push(fail(`transit: ${transit?.reason}`));
    else if (!transit.panelHidden && /Route|Destination|Position/i.test(transit.panelText)) {
      pass(`transit ${transit.id} · ${transit.panelText.slice(0, 80)}`);
    } else {
      errors.push(fail(`transit detail empty hidden=${transit.panelHidden}`));
    }

    console.log("\n=== Indego layer ===");
    await page.check('input[data-layer="indego"]');
    await waitForApi(page, "/api/indego/stations", 30_000).catch(() => null);
    await page.waitForTimeout(3000);
    const indego = await hook(page, () => {
      const ent = window.__gridlandTest.selectFirstEntity("indego");
      if (!ent) return { ok: false, reason: "no indego entities" };
      return {
        ok: true,
        name: ent.name,
        panelText: ent.panelText || "",
        panelHidden: ent.panelHidden,
      };
    });
    if (!indego?.ok) errors.push(fail(`indego: ${indego?.reason}`));
    else if (!indego.panelHidden && /Bikes|Docks/i.test(indego.panelText)) {
      pass(`indego ${indego.name} · ${indego.panelText.slice(0, 60)}`);
    } else errors.push(fail("indego detail missing live counts"));

    console.log("\n=== What's here (ground click API + panel) ===");
    const wh = await hook(page, async () => {
      const lat = parseFloat(document.getElementById("lat").value);
      const lon = parseFloat(document.getElementById("lon").value);
      const payload = await window.__gridlandTest.runWhatsHere(lat, lon, 1);
      const cams = payload.cameras?.results?.length ?? 0;
      const text = document.getElementById("whats-here")?.textContent || "";
      return { cams, text: text.slice(0, 120), hidden: document.getElementById("whats-here")?.hidden };
    });
    if (!wh?.hidden && wh?.cams > 0 && /What's here/i.test(wh.text || "")) {
      pass(`whats-here: ${wh.cams} cameras · ${wh.text}`);
    } else {
      errors.push(fail(`whats-here: cams=${wh?.cams} hidden=${wh?.hidden}`));
    }

    console.log("\n=== Context-live POIs ===");
    await page.check('input[data-layer="context-live-pois"]');
    await page.waitForTimeout(2000);
    const livePoi = await hook(page, () => {
      const ent = window.__gridlandTest.selectFirstEntity("context-live-pois");
      if (!ent) return { ok: false, reason: "no context-live entities" };
      return {
        ok: true,
        name: ent.name,
        panelText: ent.panelText || "",
        panelHidden: ent.panelHidden,
      };
    });
    if (livePoi?.ok && !livePoi.panelHidden && livePoi.panelText.length > 5) {
      pass(`context-live: ${livePoi.name} · ${livePoi.panelText.slice(0, 50)}`);
    } else {
      errors.push(fail(`context-live: ${livePoi?.reason || "empty panel"}`));
    }

    console.log("\n=== Summary ===");
    if (errors.length) {
      console.log(`FAILED: ${errors.length} UI check(s)`);
      process.exitCode = 1;
    } else {
      console.log("All UI click surfaces returned live data.");
    }
  } finally {
    await browser.close();
  }
}

main().catch((e) => {
  console.error("ERROR:", e.message);
  process.exit(1);
});
