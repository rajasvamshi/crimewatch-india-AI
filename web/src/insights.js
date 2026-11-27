// Analytics computed in the browser from the same JSON the map uses, so every number on the
// Intelligence page matches the map exactly. Methods are simple and stated on the page.

const HOUR = 3600e3;
const DAY = 24 * HOUR;

/** Density hotspots: reports binned on a ~40 km grid, then ranked. */
export function hotspots(incidents, { cell = 0.35, top = 8, now = Date.now() } = {}) {
  const cells = new Map();
  for (const i of incidents) {
    if (i.precision === 'state') continue; // a state centre is not a hotspot
    const k = `${Math.round(i.lat / cell)}:${Math.round(i.lon / cell)}`;
    if (!cells.has(k)) cells.set(k, []);
    cells.get(k).push(i);
  }
  const out = [];
  for (const list of cells.values()) {
    const places = tally(list.map((i) => i.place.split(',')[0]));
    const cats = tally(list.map((i) => i.category));
    out.push({
      name: places[0][0],
      state: list[0].state,
      lat: avg(list.map((i) => i.lat)),
      lon: avg(list.map((i) => i.lon)),
      count: list.length,
      last24: list.filter((i) => now - Date.parse(i.ts) < DAY).length,
      cats,
      top: cats[0][0],
    });
  }
  return out.sort((a, b) => b.count - a.count).slice(0, top);
}

/** States with more reports in the last 24 hours than their recent daily average (Poisson test). */
export function spikes(incidents, now = Date.now()) {
  const first = Math.min(...incidents.map((i) => Date.parse(i.ts)));
  const historyDays = Math.min(7, Math.floor((now - DAY - first) / DAY));
  const by = new Map();
  for (const i of incidents) {
    if (!i.state) continue;
    const age = now - Date.parse(i.ts);
    const s = by.get(i.state) || { recent: 0, before: 0 };
    if (age < DAY) s.recent += 1;
    else if (age < DAY * (1 + historyDays)) s.before += 1;
    by.set(i.state, s);
  }
  const rows = [];
  for (const [state, s] of by) {
    const base = historyDays > 0 ? s.before / historyDays : null;
    const p = base != null ? poissonTail(s.recent, Math.max(base, 0.5)) : null;
    rows.push({ state, recent: s.recent, base, ratio: base ? s.recent / base : null, p });
  }
  return {
    historyDays,
    rows: rows.filter((r) => r.recent >= 3 && r.p != null && r.p < 0.05).sort((a, b) => a.p - b.p),
    all: rows.sort((a, b) => b.recent - a.recent),
  };
}

/** When reports appear, by hour of day in India Standard Time. */
export function clock(incidents) {
  const bins = new Array(24).fill(0);
  for (const i of incidents) bins[(new Date(i.ts).getUTCHours() + 5 + (new Date(i.ts).getUTCMinutes() >= 30 ? 1 : 0)) % 24] += 1;
  return bins;
}

/** News attention per crore people vs the official NCRB crime rate, per state. */
export function attention(byState, officialRows) {
  const year = Math.max(0, ...officialRows.filter((r) => r.level === 'state').map((r) => r.year));
  const off = new Map(officialRows.filter((r) => r.level === 'state' && r.year === year).map((r) => [r.name, r]));
  const pts = [];
  for (const [state, n] of byState) {
    const o = off.get(state);
    if (!o || !o.crime_rate) continue;
    const popCrore = o.total_cases / o.crime_rate / 100; // total / (per lakh) = lakh people; /100 = crore
    if (popCrore < 0.1) continue; // tiny UTs swing wildly
    pts.push({ state, reports: n, perCrore: n / popCrore, rate: o.crime_rate, popCrore });
  }
  const x = pts.map((p) => p.perCrore), y = pts.map((p) => p.rate);
  return { year, pts, r: pearson(x, y), rho: pearson(ranks(x), ranks(y)) };
}

/** Category counts per day (for the stacked stream). */
export function categoryDays(incidents, cats) {
  const days = new Map();
  for (const i of incidents) {
    const d = istDay(i.ts);
    if (!days.has(d)) days.set(d, Object.fromEntries(cats.map((c) => [c, 0])));
    const row = days.get(d);
    if (i.category in row) row[i.category] += 1;
  }
  return [...days.entries()].sort().map(([day, v]) => ({ day, ...v }));
}

export const latest = (incidents, n = 30) =>
  [...incidents].filter((i) => i.title).sort((a, b) => b.ts.localeCompare(a.ts)).slice(0, n);

// ---------- helpers ----------
export const istDay = (iso) => new Date(Date.parse(iso) + 5.5 * HOUR).toISOString().slice(0, 10);
const avg = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;
function tally(xs) {
  const m = new Map();
  xs.forEach((x) => m.set(x, (m.get(x) || 0) + 1));
  return [...m.entries()].sort((a, b) => b[1] - a[1]);
}
function poissonTail(k, lambda) {
  // P(X >= k) for X ~ Poisson(lambda)
  let term = Math.exp(-lambda), cdf = 0;
  for (let i = 0; i < k; i += 1) { cdf += term; term *= lambda / (i + 1); }
  return Math.max(0, 1 - cdf);
}
function ranks(xs) {
  const idx = xs.map((v, i) => [v, i]).sort((a, b) => a[0] - b[0]);
  const r = new Array(xs.length);
  idx.forEach(([, i], k) => { r[i] = k + 1; });
  return r;
}
export function pearson(x, y) {
  const n = x.length;
  if (n < 3) return null;
  const mx = avg(x), my = avg(y);
  let sxy = 0, sxx = 0, syy = 0;
  for (let i = 0; i < n; i += 1) { sxy += (x[i] - mx) * (y[i] - my); sxx += (x[i] - mx) ** 2; syy += (y[i] - my) ** 2; }
  return sxx && syy ? sxy / Math.sqrt(sxx * syy) : null;
}
