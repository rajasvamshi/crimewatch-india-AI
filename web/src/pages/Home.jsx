import { useMemo, useState } from 'react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { HexagonLayer } from '@deck.gl/aggregation-layers';
import MapView from '../components/MapView.jsx';
import Ticker from '../components/Ticker.jsx';
import { useJson, spread, timeAgo } from '../data.js';
import { useLang, colorOf, rgb } from '../i18n.js';
import { useClock, useReveal, useActiveStep, useCountUp } from '../motion.js';
import { hotspots, spikes, attention } from '../insights.js';

const HOUR = 3600e3;
const HEX_COLORS = [[255, 237, 160], [254, 217, 118], [254, 178, 76], [253, 141, 60], [240, 59, 32], [189, 0, 38]];
const INDIA = { center: [80.2, 22.4], zoom: 4.1, pitch: 50, bearing: -12 };

function Count({ to, dp = 0 }) {
  const v = useCountUp(to);
  return <>{to == null ? '–' : Number(v.toFixed(dp)).toLocaleString('en-IN', { minimumFractionDigits: dp, maximumFractionDigits: dp })}</>;
}

/** Expanding rings on reports from the last 24 hours. */
function ringLayer(id, data, t, now) {
  return new ScatterplotLayer({
    id, data, getPosition: (d) => [d.plon ?? d.lon, d.plat ?? d.lat], radiusUnits: 'pixels', stroked: true, filled: false,
    lineWidthUnits: 'pixels', getLineWidth: 1.5,
    getRadius: (d) => 3 + ((t * 0.45 + (d.phase || 0)) % 1) * 22,
    getLineColor: (d) => [...colorOf(d.category), 230 * (1 - ((t * 0.45 + (d.phase || 0)) % 1))],
    updateTriggers: { getRadius: t, getLineColor: t },
    parameters: { depthTest: false },
    visible: data.length > 0 && now > 0,
  });
}

export default function Home({ go }) {
  const { t, cat, num, lang } = useLang();
  const [inc] = useJson('incidents.json');
  const [sum] = useJson('summary.json');
  const [off] = useJson('official.json');
  const [pv] = useJson('prevent.json');
  const [q, setQ] = useState('');
  const clockT = useClock(true);
  useReveal([!!inc, !!off, !!pv]);

  const now = inc ? Date.parse(inc.generated_at) : 0;
  const all = useMemo(() => (inc ? spread(inc.incidents).map((d, k) => ({ ...d, phase: (k * 0.618) % 1 })) : []), [inc]);
  const recent = useMemo(() => all.filter((d) => now - Date.parse(d.ts) < 24 * HOUR), [all, now]);
  const hot = useMemo(() => (inc ? hotspots(inc.incidents, { now }) : []), [inc, now]);
  const sp = useMemo(() => (inc ? spikes(inc.incidents, now) : null), [inc, now]);
  const att = useMemo(() => (sum && off ? attention(sum.by_state, off.rows) : null), [sum, off]);

  // ---------- hero map ----------
  const heroLayers = useMemo(() => (all.length ? [
    new HexagonLayer({ id: 'hero-hex', data: all, getPosition: (d) => [d.lon, d.lat], radius: 26000, extruded: true,
      elevationScale: 650, coverage: 0.78, opacity: 0.92, colorRange: HEX_COLORS, material: { ambient: 0.55, diffuse: 0.7, shininess: 40 } }),
  ] : []), [all]);
  const heroRings = useMemo(() => (recent.length ? [ringLayer('hero-rings', recent.slice(0, 160), clockT, now)] : []), [recent, clockT, now]);

  // ---------- story ----------
  const focus = sp?.rows[0] || (sp?.all[0] && { ...sp.all[0], quiet: true });
  // chapters are memoised so their camera targets keep the same identity between animation frames
  const chapters = useMemo(() => {
    const pts = focus ? all.filter((d) => d.state === focus.state) : [];
    const centre = pts.length ? [pts.reduce((a, d) => a + d.lon, 0) / pts.length, pts.reduce((a, d) => a + d.lat, 0) / pts.length] : INDIA.center;
    return [
      { view: INDIA, kind: 'hex' },
      hot[0] && { view: { center: [hot[0].lon, hot[0].lat], zoom: 9.6, pitch: 62, bearing: 24 }, kind: 'pts', spot: hot[0] },
      hot[1] && { view: { center: [hot[1].lon, hot[1].lat], zoom: 9.6, pitch: 60, bearing: -30 }, kind: 'pts', spot: hot[1] },
      focus && { view: { center: centre, zoom: 6.2, pitch: 55, bearing: 10 }, kind: 'state', state: focus.state },
      { view: { ...INDIA, pitch: 30, bearing: 0, zoom: 4.3 }, kind: 'cats' },
    ].filter(Boolean).map((c) => (window.innerWidth > 900
      ? { ...c, view: { ...c.view, padding: { left: Math.round(window.innerWidth * 0.36), right: 40, top: 40, bottom: 40 } } } : c));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [all, hot, focus?.state]);
  const [active, stepRef] = useActiveStep(chapters.length);
  const ch = chapters[Math.min(active, chapters.length - 1)];

  const storyLayers = useMemo(() => {
    if (!all.length || !ch) return [];
    if (ch.kind === 'hex') {
      return [new HexagonLayer({ id: 'story-hex', data: all, getPosition: (d) => [d.lon, d.lat], radius: 26000, extruded: true,
        elevationScale: 1100, coverage: 0.8, colorRange: HEX_COLORS, transitions: { elevationScale: { duration: 1400 } } })];
    }
    const inFocus = (d) => (ch.kind === 'state' ? d.state === ch.state : ch.kind === 'pts' ? Math.abs(d.lat - ch.spot.lat) < 0.6 && Math.abs(d.lon - ch.spot.lon) < 0.6 : true);
    return [
      new ScatterplotLayer({ id: 'story-pts', data: all, getPosition: (d) => [d.plon, d.plat], radiusUnits: 'pixels',
        getRadius: (d) => (inFocus(d) ? 6 : 2.5), getFillColor: (d) => [...colorOf(d.category), inFocus(d) ? 240 : 70],
        stroked: true, getLineColor: [7, 9, 13, 200], lineWidthUnits: 'pixels', getLineWidth: 1,
        updateTriggers: { getRadius: active, getFillColor: active }, transitions: { getRadius: 600, getFillColor: 600 } }),
      ringLayer('story-rings', all.filter(inFocus).slice(0, 120), clockT, now),
    ];
  }, [all, ch, active, clockT, now]);

  const nat = (off?.rows || []).filter((r) => r.level === 'national').sort((a, b) => a.year - b.year);
  const metro = (off?.rows || []).filter((r) => r.level === 'metro_aggregate').sort((a, b) => a.year - b.year);
  const last = nat.at(-1), prev = nat.at(-2), m = metro.at(-1), mp = metro.at(-2);
  const pct = (a, b) => (a && b ? `${a >= b ? '+' : ''}${((a / b - 1) * 100).toFixed(1)}%` : '');

  const submit = (e) => { e.preventDefault(); go('map', q); };
  const words = (s, base = 0) => s.split(' ').map((w, k) => <span key={k}><span className="w" style={{ animationDelay: `${(base + k) * 70 + 200}ms` }}>{w}</span>{' '}</span>);
  const wide = typeof window !== 'undefined' && window.innerWidth > 1100;
  const heroView = useMemo(() => (wide
    ? { center: [80.5, 22.5], zoom: 4.15, pitch: 56, bearing: -20, padding: { left: Math.round(window.innerWidth * 0.4), right: 380, top: 80, bottom: 60 } }
    : { center: [80.5, 21], zoom: 3.6, pitch: 50, bearing: -15 }), [wide]);

  return (
    <>
      {/* ================= HERO ================= */}
      <section className="hero" aria-labelledby="hero-title">
        <div className="map-bg"><MapView layers={[...heroLayers, ...heroRings]} interactive={false} spin intro
          view={heroView} /></div>
        <div className="shade" />
        <div className="hud-corner tl" aria-hidden="true" /><div className="hud-corner br" aria-hidden="true" />
        <div className="copy">
          <div className="eyebrow live-eyebrow"><span className="pulse" />{t('hero_eyebrow')}</div>
          <h1 id="hero-title" className="display">
            {words(t('hero_title_1'))}<em>{words(t('hero_title_2'), 4)}</em> {words(t('hero_title_3'), 6)}
          </h1>
          <p className="lead">{t('hero_lead')}</p>
          <div className="counter" aria-live="polite">
            <div><div className="n"><Count to={sum?.last_24h} /></div><div className="l">{t('c_24h')}</div></div>
            <div><div className="n"><Count to={sum?.states_last_24h} /></div><div className="l">{t('c_states')}</div></div>
            <div><div className="n"><Count to={sum?.total} /></div><div className="l">{t('c_30d')}</div></div>
          </div>
          <form className="search glow" onSubmit={submit} role="search">
            <span aria-hidden="true">⌕</span>
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('search_ph')} aria-label={t('search_ph')} />
            <button className="btn primary magnetic" type="submit">{t('open_map')} <span aria-hidden="true">→</span></button>
          </form>
        </div>
        {recent[0] && (
          <aside className="hud-feed" aria-label={t('latest')}>
            <div className="hud-title"><span className="pulse" />{t('latest')}</div>
            {[...recent].sort((a, b) => b.ts.localeCompare(a.ts)).filter((d) => d.title).slice(0, 4).map((d) => (
              <button key={d.id} className="hud-item" onClick={() => go('map', d.place.split(',')[0])}>
                <span className="tag" style={{ color: rgb(d.category), borderColor: rgb(d.category, 0.4) }}>{cat(d.category)}</span>
                <span className="ttl">{d.title}</span>
                <span className="meta">{d.place} · {timeAgo(d.ts, lang)}</span>
              </button>))}
          </aside>)}
        <Ticker items={inc?.incidents} go={go} />
      </section>

      {/* ================= STORY (scroll-driven map) ================= */}
      <section className="story" aria-labelledby="story-title">
        <div className="story-map" aria-hidden="true">
          <MapView layers={storyLayers} interactive={false} view={INDIA} flyTo={ch?.view} />
          <div className="story-shade" />
          <div className="story-progress">{chapters.map((_, k) => <i key={k} className={k === active ? 'on' : ''} />)}</div>
        </div>
        <div className="story-steps">
          <h2 id="story-title" className="sr-only">{t('story_title')}</h2>
          {chapters.map((c, k) => (
            <div key={k} className={`step-card${k === active ? ' on' : ''}`} data-step={k} ref={stepRef(k)}>
              <div className="glass spot">
                <div className="kicker">0{k + 1} / 0{chapters.length}</div>
                {c.kind === 'hex' && <>
                  <h3>{t('ch1_t')}</h3>
                  <p><b className="big-n"><Count to={sum?.total} /></b> {t('ch1_a')} <b>{sum?.by_state?.length}</b> {t('ch1_b')}</p>
                  <p className="muted">{t('ch1_c')}</p></>}
                {c.kind === 'pts' && <>
                  <h3>{c.spot.name}</h3>
                  <p><b className="big-n">{num(c.spot.count)}</b> {t('ch_spot_a')} <b>{num(c.spot.last24)}</b> {t('ch_spot_b')}</p>
                  <div className="mix">{c.spot.cats.slice(0, 5).map(([k2, v]) => (
                    <span key={k2} style={{ flex: v, background: rgb(k2) }} title={`${cat(k2)}: ${v}`} />))}</div>
                  <div className="mix-legend">{c.spot.cats.slice(0, 4).map(([k2, v]) => <span key={k2}><i style={{ background: rgb(k2) }} />{cat(k2)} {v}</span>)}</div></>}
                {c.kind === 'state' && <>
                  <h3>{focus.state}</h3>
                  {focus.quiet
                    ? <p><b className="big-n">{focus.recent}</b> {t('ch_busy')}</p>
                    : <p><b className="big-n">{focus.ratio.toFixed(1)}×</b> {t('ch_spike_a')} ({focus.recent} {t('ch_spike_b')} {focus.base.toFixed(1)}).</p>}
                  <p className="muted">{t('ch_spike_c')}</p></>}
                {c.kind === 'cats' && <>
                  <h3>{t('ch5_t')}</h3>
                  <div className="cat-cloud">{(sum?.by_category || []).slice(0, 10).map(([k2, v]) => (
                    <span key={k2}><i style={{ background: rgb(k2) }} />{cat(k2)} <b>{v}</b></span>))}</div>
                  <button className="btn primary magnetic" onClick={() => go('map')}>{t('open_map')} →</button></>}
              </div>
            </div>))}
        </div>
      </section>

      {/* ================= INTELLIGENCE TEASER ================= */}
      <section className="section" aria-labelledby="intel-title">
        <div className="reveal"><div className="eyebrow">{t('intel_eyebrow')}</div>
          <h2 id="intel-title" className="display">{t('intel_title')}</h2><p className="sub">{t('intel_sub')}</p></div>
        <div className="bento">
          {hot[0] && (
            <button className="tile spot tilt reveal" onClick={() => go('intel')}>
              <div className="tile-k">{t('i_hotspot')}</div>
              <div className="tile-n">{hot[0].name}</div>
              <div className="tile-s">{hot[0].count} {t('ch_spot_a')} · {cat(hot[0].top)}</div>
              <div className="spark">{hot.slice(0, 6).map((h) => <span key={h.name} style={{ height: `${(h.count / hot[0].count) * 100}%` }} title={h.name} />)}</div>
            </button>)}
          {sp && (
            <button className="tile spot tilt reveal" onClick={() => go('intel')}>
              <div className="tile-k">{t('i_spike')}</div>
              <div className="tile-n">{sp.rows[0] ? sp.rows[0].state : t('i_nospike')}</div>
              <div className="tile-s">{sp.rows[0] ? `${sp.rows[0].ratio.toFixed(1)}× ${t('i_usual')} · p = ${sp.rows[0].p.toFixed(4)}` : t('i_nospike_s')}</div>
            </button>)}
          {att?.rho != null && (
            <button className="tile spot tilt reveal" onClick={() => go('intel')}>
              <div className="tile-k">{t('i_corr')}</div>
              <div className="tile-n mono">ρ = {att.rho.toFixed(2)}</div>
              <div className="tile-s">{t('i_corr_s')}</div>
            </button>)}
          <button className="tile spot tilt reveal accent" onClick={() => go('intel')}>
            <div className="tile-k">{t('nav_intel')}</div>
            <div className="tile-n">{t('i_open')} →</div>
            <div className="tile-s">{t('i_open_s')}</div>
          </button>
        </div>
      </section>

      {/* ================= PREVENT TEASER ================= */}
      {pv && (
        <section className="section" aria-labelledby="pv-title" style={{ paddingTop: 0 }}>
          <div className="reveal"><div className="eyebrow">{t('pv_eyebrow')}</div>
            <h2 id="pv-title" className="display">{t('pv_teaser_t')}</h2><p className="sub">{t('pv_teaser_s')}</p></div>
          <div className="bento">
            {pv.scams[0] && (
              <button className="tile spot tilt reveal" onClick={() => go('prevent')}>
                <div className="tile-k">{t('pv_scam_t')}</div>
                <div className="tile-n">{pv.scams[0].type}</div>
                <div className="tile-s">{pv.scams[0].this_week} {t('pv_this_week')} · {t(`tr_${pv.scams[0].trend}`)}</div>
              </button>)}
            {pv.forecast[0] && (
              <button className="tile spot tilt reveal" onClick={() => go('prevent')}>
                <div className="tile-k">{t('pv_fc_t')}</div>
                <div className="tile-n">{pv.forecast[0].name.split(',')[0]}</div>
                <div className="tile-s">{t(`lv_${pv.forecast[0].level}`)} · {cat(pv.forecast[0].top_category)}</div>
              </button>)}
            <button className="tile spot tilt reveal" onClick={() => go('prevent')}>
              <div className="tile-k">{t('pv_audit_t')}</div>
              <div className="tile-n mono">2 min</div>
              <div className="tile-s">{t('pv_audit_s')}</div>
            </button>
            <button className="tile spot tilt reveal accent" onClick={() => go('prevent')}>
              <div className="tile-k">{t('nav_prevent')}</div>
              <div className="tile-n">{t('pv_open')} →</div>
              <div className="tile-s">112 · 1930 · 181 · 1098</div>
            </button>
          </div>
        </section>)}

      {/* ================= OFFICIAL FACTS ================= */}
      <section className="section" aria-labelledby="facts-title" style={{ paddingTop: 0 }}>
        <div className="reveal"><div className="eyebrow">{t('facts_eyebrow')}</div>
          <h2 id="facts-title" className="display">{t('facts_title')}</h2><p className="sub">{t('facts_sub')}</p></div>
        <div className="facts">
          <div className="fact spot reveal"><div><div className="big"><Count to={last?.total_cases} /></div><div className="what">{t('f_total')}</div></div>
            <div><div className="delta">{pct(last?.total_cases, prev?.total_cases)} {t('vs')} {prev?.year}</div><div className="src">NCRB, Crime in India 2024, Table 1.1</div></div></div>
          <div className="fact spot reveal"><div><div className="big"><Count to={last?.crime_rate} dp={1} /></div><div className="what">{t('f_rate')}</div></div>
            <div><div className="delta">{prev && last ? `${last.crime_rate >= prev.crime_rate ? '+' : ''}${(last.crime_rate - prev.crime_rate).toFixed(1)}` : ''} {t('vs')} {prev?.year}</div><div className="src">NCRB, Crime in India 2024, Table 1.1</div></div></div>
          <div className="fact spot reveal"><div><div className="big"><Count to={m?.total_cases} /></div><div className="what">{t('f_metro')}</div></div>
            <div><div className="delta">{pct(m?.total_cases, mp?.total_cases)} {t('vs')} {mp?.year}</div><div className="src">NCRB, Crime in India 2024</div></div></div>
        </div>
      </section>

      {/* ================= HOW IT WORKS ================= */}
      <section className="section" aria-labelledby="how-title" style={{ paddingTop: 0 }}>
        <div className="reveal"><div className="eyebrow">{t('how_eyebrow')}</div><h2 id="how-title" className="display">{t('how_title')}</h2></div>
        <div className="pipeline">
          {[1, 2, 3, 4].map((k) => (
            <div key={k} className="pipe spot reveal" style={{ transitionDelay: `${k * 90}ms` }}>
              <div className="k mono">0{k}</div><h3>{t(`s${k}t`)}</h3><p>{t(`s${k}`)}</p>
              {k < 4 && <span className="flow" aria-hidden="true" />}
            </div>))}
        </div>
      </section>

      <section className="cta-band reveal">
        <h2 className="display">{t('cta_title')}</h2>
        <div><button className="btn primary magnetic" onClick={() => go('map')}>{t('open_map')} →</button>{' '}
          <button className="btn ghost" onClick={() => go('about')}>{t('nav_about')}</button></div>
        <p className="muted">{t('footer_2')}</p>
      </section>
    </>
  );
}
