import { useEffect, useState } from 'react';

const cache = {};
export function useJson(name) {
  const [data, setData] = useState(cache[name] ?? null);
  const [error, setError] = useState(null);
  useEffect(() => {
    if (cache[name]) return;
    fetch(`./data/${name}`, { cache: 'no-cache' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
      .then((d) => { cache[name] = d; setData(d); })
      .catch(setError);
  }, [name]);
  return [data, error];
}

// Many reports share one city centre. Spread them in a small, stable circle (~1.5 km)
// so they can be clicked, without implying a more exact location than the source gave.
export function spread(incidents) {
  const groups = new Map();
  for (const i of incidents) {
    const k = `${i.lat},${i.lon}`;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(i);
  }
  const out = [];
  for (const list of groups.values()) {
    list.forEach((i, n) => {
      if (n === 0) { out.push({ ...i, plat: i.lat, plon: i.lon }); return; }
      const ring = Math.ceil(Math.sqrt(n));
      const ang = n * 2.399963; // golden angle
      const r = 0.0045 * ring * (i.precision === 'state' ? 4 : 1);
      out.push({ ...i, plat: i.lat + r * Math.sin(ang), plon: i.lon + (r * Math.cos(ang)) / Math.cos((i.lat * Math.PI) / 180) });
    });
  }
  return out;
}

export const timeAgo = (iso, lang = 'en') => {
  const s = (Date.now() - Date.parse(iso)) / 1000;
  const hi = lang === 'hi';
  if (s < 3600) return hi ? `${Math.max(1, Math.round(s / 60))} मिनट पहले` : `${Math.max(1, Math.round(s / 60))} min ago`;
  if (s < 86400) return hi ? `${Math.round(s / 3600)} घंटे पहले` : `${Math.round(s / 3600)} h ago`;
  return hi ? `${Math.round(s / 86400)} दिन पहले` : `${Math.round(s / 86400)} days ago`;
};

export const fmtIST = (iso) =>
  new Date(iso).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) + ' IST';
