import { useEffect, useMemo, useRef, useState } from 'react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { HexagonLayer } from '@deck.gl/aggregation-layers';
import MapView from '../components/MapView.jsx';
import { useJson } from '../data.js';
import { useLang } from '../i18n.js';

function CountUp({ to, ms = 1400 }) {
  const [v, setV] = useState(0);
  useEffect(() => {
    if (to == null) return;
    const t0 = performance.now();
    let raf;
    const tick = (t) => { const p = Math.min(1, (t - t0) / ms); setV(Math.round(to * (1 - Math.pow(1 - p, 3)))); if (p < 1) raf = requestAnimationFrame(tick); };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [to, ms]);
  return <>{to == null ? '–' : v.toLocaleString('en-IN')}</>;
}

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll('.reveal');
    const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && e.target.classList.add('in')), { threshold: 0.15 });
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
  });
}

export default function Home({ go }) {
  const { t, num } = useLang();
  const [inc] = useJson('incidents.json');
  const [sum] = useJson('summary.json');
  const [off] = useJson('official.json');
  const [q, setQ] = useState('');
  const input = useRef(null);
  useReveal();

  const layers = useMemo(() => {
    if (!inc) return [];
    return [
      new HexagonLayer({ id: 'hero-hex', data: inc.incidents, getPosition: (d) => [d.lon, d.lat], radius: 22000, extruded: true,
        elevationScale: 120, coverage: 0.8, opacity: 0.9,
        colorRange: [[255, 237, 160], [254, 217, 118], [254, 178, 76], [253, 141, 60], [240, 59, 32], [189, 0, 38]] }),
      new ScatterplotLayer({ id: 'hero-pts', data: inc.incidents.slice(0, 400), getPosition: (d) => [d.lon, d.lat], getRadius: 2.5,
        radiusUnits: 'pixels', getFillColor: [255, 255, 255, 140] }),
    ];
  }, [inc]);

  const nat = (off?.rows || []).filter((r) => r.level === 'national').sort((a, b) => a.year - b.year);
  const metro = (off?.rows || []).filter((r) => r.level === 'metro_aggregate').sort((a, b) => a.year - b.year);
  const last = nat.at(-1), prev = nat.at(-2), m = metro.at(-1), mp = metro.at(-2);
  const pct = (a, b) => (a && b ? `${((a / b - 1) * 100).toFixed(1)}%` : '');

  const submit = (e) => { e.preventDefault(); go('map', q); };

  return (
    <>
      <section className="hero" aria-labelledby="hero-title">
        <div className="map-bg"><MapView layers={layers} interactive={false} spin view={{ center: [79.5, 21.5], zoom: 4.3, pitch: 58, bearing: -20 }} /></div>
        <div className="shade" />
        <div className="copy">
          <div className="eyebrow">{t('hero_eyebrow')}</div>
          <h1 id="hero-title">{t('hero_title_1')} <em>{t('hero_title_2')}</em> {t('hero_title_3')}</h1>
          <p className="lead">{t('hero_lead')}</p>
          <div className="counter" aria-live="polite">
            <div><div className="n"><CountUp to={sum?.last_24h} /></div><div className="l">{t('c_24h')}</div></div>
            <div><div className="n"><CountUp to={sum?.states_last_24h} /></div><div className="l">{t('c_states')}</div></div>
            <div><div className="n"><CountUp to={sum?.total} /></div><div className="l">{t('c_30d')}</div></div>
          </div>
          <form className="search" onSubmit={submit} role="search">
            <span aria-hidden="true">⌕</span>
            <input ref={input} value={q} onChange={(e) => setQ(e.target.value)} placeholder={t('search_ph')} aria-label={t('search_ph')} />
            <button className="btn primary" type="submit">{t('open_map')} →</button>
          </form>
        </div>
        <div className="scroll-cue">{t('explore')} ↓</div>
      </section>

      <section className="section" aria-labelledby="facts-title">
        <div className="reveal"><div className="eyebrow">{t('facts_eyebrow')}</div>
          <h2 id="facts-title">{t('facts_title')}</h2><p className="sub">{t('facts_sub')}</p></div>
        <div className="facts">
          <div className="fact reveal"><div><div className="big">{num(last?.total_cases)}</div><div className="what">{t('f_total')}</div></div>
            <div><div className="delta">{pct(last?.total_cases, prev?.total_cases)} {t('vs')} {prev?.year}</div><div className="src">NCRB, Crime in India 2024, Table 1.1</div></div></div>
          <div className="fact reveal"><div><div className="big">{last?.crime_rate ?? '–'}</div><div className="what">{t('f_rate')}</div></div>
            <div><div className="delta">{prev && last ? (last.crime_rate - prev.crime_rate).toFixed(1) : ''} {t('vs')} {prev?.year}</div><div className="src">NCRB, Crime in India 2024, Table 1.1</div></div></div>
          <div className="fact reveal"><div><div className="big">{num(m?.total_cases)}</div><div className="what">{t('f_metro')}</div></div>
            <div><div className="delta">{pct(m?.total_cases, mp?.total_cases)} {t('vs')} {mp?.year}</div><div className="src">NCRB, Crime in India 2024</div></div></div>
        </div>
      </section>

      <section className="section" aria-labelledby="how-title" style={{ paddingTop: 0 }}>
        <div className="reveal"><div className="eyebrow">{t('how_eyebrow')}</div><h2 id="how-title">{t('how_title')}</h2></div>
        <div className="steps">
          {[1, 2, 3, 4].map((k) => (
            <div key={k} className="step reveal"><div className="k">0{k}</div><h3>{t(`s${k}t`)}</h3><p>{t(`s${k}`)}</p></div>))}
        </div>
        <div style={{ marginTop: 48 }} className="reveal">
          <button className="btn primary" onClick={() => go('map')}>{t('open_map')} →</button>{' '}
          <button className="btn ghost" onClick={() => go('about')}>{t('nav_about')}</button>
        </div>
      </section>
    </>
  );
}
