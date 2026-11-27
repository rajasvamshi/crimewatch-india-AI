import { useEffect, useMemo, useState } from 'react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { HexagonLayer, HeatmapLayer } from '@deck.gl/aggregation-layers';
import MapView, { INDIA_VIEW } from '../components/MapView.jsx';
import { useJson, spread, timeAgo, fmtIST } from '../data.js';
import { useLang, colorOf, rgb } from '../i18n.js';

const PERIODS = { h24: 24, d7: 24 * 7, d30: 24 * 30 };
const HOUR = 3600e3;

export default function LiveMap({ query }) {
  const { t, cat, num, lang } = useLang();
  const [data] = useJson('incidents.json');
  const [mode, setMode] = useState('points');
  const [period, setPeriod] = useState('d7');
  const [cats, setCats] = useState(null); // null = all
  const [origins, setOrigins] = useState({ news: true, police: true });
  const [q, setQ] = useState(query || '');
  const [selected, setSelected] = useState(null);
  const [flyTo, setFlyTo] = useState(null);
  const [cursor, setCursor] = useState(1); // 0..1 position of the timeline's end handle
  const [playing, setPlaying] = useState(false);

  const all = useMemo(() => (data ? spread(data.incidents) : []), [data]);
  const now = data ? Date.parse(data.generated_at) : Date.now();
  const span = PERIODS[period] * HOUR;
  const end = now - (1 - cursor) * span;
  const start = playing || cursor < 1 ? end - Math.max(span / 12, 6 * HOUR) : now - span;

  const inPeriod = useMemo(
    () => all.filter((i) => { const ts = Date.parse(i.ts); return ts >= now - span && ts <= now; }),
    [all, now, span],
  );
  const counts = useMemo(() => {
    const c = {};
    inPeriod.forEach((i) => { c[i.category] = (c[i.category] || 0) + 1; });
    return Object.entries(c).sort((a, b) => b[1] - a[1]);
  }, [inPeriod]);

  const needle = q.trim().toLowerCase();
  const visible = useMemo(() => inPeriod.filter((i) => {
    const ts = Date.parse(i.ts);
    if (ts < start || ts > end) return false;
    if (cats && !cats.has(i.category)) return false;
    if (!origins[i.origin === 'police' ? 'police' : 'news']) return false;
    if (needle && !`${i.place} ${i.state || ''}`.toLowerCase().includes(needle)) return false;
    return true;
  }), [inPeriod, start, end, cats, origins, needle]);

  // search: fly to the first matching place
  useEffect(() => {
    if (!needle || !visible.length) return;
    const id = setTimeout(() => {
      const f = visible[0];
      setFlyTo({ center: [f.lon, f.lat], zoom: f.precision === 'state' ? 6 : 11.5, pitch: 60 });
    }, 500);
    return () => clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [needle]);

  // playback: sweep a window across the period
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setCursor((c) => { if (c >= 1) { setPlaying(false); return 1; } return Math.min(1, c + 0.01); }), 80);
    return () => clearInterval(id);
  }, [playing]);

  const bins = useMemo(() => {
    const n = 48, out = new Array(n).fill(0);
    inPeriod.forEach((i) => { const k = Math.floor(((Date.parse(i.ts) - (now - span)) / span) * n); if (k >= 0 && k < n) out[k] += 1; });
    return out;
  }, [inPeriod, now, span]);
  const maxBin = Math.max(1, ...bins);

  const layers = useMemo(() => {
    const pick = ({ object }) => object && setSelected(object.points ? null : object);
    if (mode === 'columns') {
      return [new HexagonLayer({
        id: 'hex', data: visible, getPosition: (d) => [d.lon, d.lat], radius: 12000, extruded: true, elevationScale: 60,
        coverage: 0.85, upperPercentile: 99, pickable: true, opacity: 0.85,
        colorRange: [[255, 237, 160], [254, 217, 118], [254, 178, 76], [253, 141, 60], [240, 59, 32], [189, 0, 38]],
        material: { ambient: 0.6, diffuse: 0.6, shininess: 24 },
        transitions: { elevationScale: 600 },
      })];
    }
    if (mode === 'heat') {
      return [new HeatmapLayer({ id: 'heat', data: visible, getPosition: (d) => [d.lon, d.lat], radiusPixels: 45, intensity: 1.2, threshold: 0.04,
        colorRange: [[40, 20, 60], [120, 30, 90], [200, 40, 70], [255, 90, 54], [255, 176, 32], [255, 240, 180]] })];
    }
    const recent = now - 24 * HOUR;
    return [
      new ScatterplotLayer({
        id: 'glow', data: visible.filter((d) => Date.parse(d.ts) >= recent), getPosition: (d) => [d.plon, d.plat],
        getRadius: 9, radiusUnits: 'pixels', getFillColor: (d) => [...colorOf(d.category), 60], stroked: false,
      }),
      new ScatterplotLayer({
        id: 'pts', data: visible, getPosition: (d) => [d.plon, d.plat], pickable: true, onClick: pick,
        radiusUnits: 'pixels', getRadius: (d) => (selected && d.id === selected.id ? 8 : 4.5),
        getFillColor: (d) => [...colorOf(d.category), 235], stroked: true, getLineColor: [7, 9, 13, 220], lineWidthUnits: 'pixels', getLineWidth: 1,
        updateTriggers: { getRadius: selected?.id },
      }),
    ];
  }, [mode, visible, selected, now]);

  const toggleCat = (c) => setCats((s) => {
    const next = new Set(s || counts.map(([k]) => k));
    if (s === null) { return new Set([c]); }
    next.has(c) ? next.delete(c) : next.add(c);
    return next.size ? next : null;
  });

  const nearby = selected ? all.filter((i) => i.place === selected.place && i.id !== selected.id).slice(0, 6) : [];
  const places = new Set(visible.map((i) => i.place)).size;

  return (
    <div className="map-page">
      <MapView layers={layers} view={INDIA_VIEW} flyTo={flyTo} />

      <aside className="float toolbar" aria-label="Map controls">
        <div className="search" role="search">
          <span aria-hidden="true">⌕</span>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('search_ph')} aria-label={t('search_ph')} />
          {q && <button className="chip" onClick={() => { setQ(''); setFlyTo({ ...INDIA_VIEW }); }} aria-label="Clear search">✕</button>}
        </div>
        <div className="stat-row">
          <div><div className="n">{num(visible.length)}</div><div className="l">{t('shown')}</div></div>
          <div><div className="n">{num(places)}</div><div className="l">{t('places')}</div></div>
        </div>
        <div className="group"><h4>{t('layers')}</h4>
          <div className="seg">{['points', 'columns', 'heat'].map((m) => (
            <button key={m} aria-pressed={mode === m} onClick={() => setMode(m)}>{t(m)}</button>))}</div>
        </div>
        <div className="group"><h4>{t('period')}</h4>
          <div className="seg">{Object.keys(PERIODS).map((p) => (
            <button key={p} aria-pressed={period === p} onClick={() => { setPeriod(p); setCursor(1); }}>{t(p)}</button>))}</div>
        </div>
        <div className="group"><h4>{t('types')}</h4>
          <div className="chips">
            <button className="chip" aria-pressed={cats === null} onClick={() => setCats(null)}>{t('all')}</button>
            {counts.map(([c, n]) => (
              <button key={c} className="chip" aria-pressed={cats === null || cats.has(c)} onClick={() => toggleCat(c)}>
                <i style={{ background: rgb(c) }} />{cat(c)} <span className="c">{n}</span>
              </button>))}
          </div>
        </div>
        <div className="group"><h4>{t('sources')}</h4>
          <div className="chips">{['news', 'police'].map((o) => (
            <button key={o} className="chip" aria-pressed={origins[o]} onClick={() => setOrigins((s) => ({ ...s, [o]: !s[o] }))}>{t(o)}</button>))}</div>
        </div>
        <p className="note">{t('map_note')} {data && <>· {t('updated')} {timeAgo(data.generated_at, lang)}</>}</p>
      </aside>

      {selected && (
        <aside className="float sheet" aria-label="Incident details">
          <button className="close" onClick={() => setSelected(null)} aria-label="Close">✕</button>
          <div className="cat" style={{ color: rgb(selected.category) }}><i className="pulse" style={{ background: rgb(selected.category) }} />{cat(selected.category)}</div>
          <h3>{selected.title || <span style={{ color: 'var(--muted)', fontWeight: 500 }}>{t('no_title')}</span>}</h3>
          <dl>
            <dt>{t('when')}</dt><dd>{fmtIST(selected.ts)} · {timeAgo(selected.ts, lang)}</dd>
            <dt>{t('where')}</dt><dd>{selected.place}</dd>
            <dt>{t('precision')}</dt><dd>{t(`p_${selected.precision}`)}</dd>
            <dt>{t('source')}</dt><dd>{t(`o_${selected.origin}`)} · {selected.source}</dd>
          </dl>
          <a className="btn primary" href={selected.url} target="_blank" rel="noopener noreferrer">{t('read')} ↗</a>
          {nearby.length > 0 && (
            <div className="list"><h4 className="group" style={{ margin: '4px 0' }}>{t('nearby')}</h4>
              {nearby.map((i) => (
                <button key={i.id} className="item" onClick={() => setSelected(i)}>
                  <span style={{ color: rgb(i.category) }}>●</span> {i.title || cat(i.category)}
                  <small>{cat(i.category)} · {timeAgo(i.ts, lang)}</small>
                </button>))}
            </div>)}
        </aside>
      )}

      <div className="float timeline" aria-label="Timeline">
        <button className="play" onClick={() => { if (cursor >= 1) setCursor(0.05); setPlaying((p) => !p); }} aria-label={playing ? t('pause') : t('play')}>{playing ? '❚❚' : '▶'}</button>
        <div className="track">
          <div className="bars" aria-hidden="true">{bins.map((b, k) => {
            const binEnd = (k + 1) / bins.length;
            const on = (cursor >= 1 && !playing) || (binEnd <= cursor + 0.001 && binEnd >= cursor - Math.max(1 / 12, (6 * HOUR) / span));
            return <span key={k} className={on ? 'on' : ''} style={{ height: `${(b / maxBin) * 100}%` }} />;
          })}</div>
          <input type="range" min="0" max="1" step="0.005" value={cursor} onChange={(e) => { setPlaying(false); setCursor(+e.target.value); }} aria-label="Move through time" />
          <div className="when"><span>{fmtIST(new Date(now - span).toISOString())}</span><span>{cursor < 1 ? fmtIST(new Date(end).toISOString()) : t('updated') + ' ' + fmtIST(new Date(now).toISOString())}</span></div>
        </div>
      </div>
    </div>
  );
}
