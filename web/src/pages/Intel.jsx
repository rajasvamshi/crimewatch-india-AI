import { useMemo, useState } from 'react';
import { useJson } from '../data.js';
import { useLang, rgb } from '../i18n.js';
import { useReveal, useCountUp } from '../motion.js';
import { hotspots, spikes, clock, attention, categoryDays } from '../insights.js';

const Num = ({ to, dp = 0 }) => { const v = useCountUp(to); return <>{to == null ? '–' : v.toFixed(dp)}</>; };

/** Polar bar chart: reports by hour of day (IST). */
function Clock({ bins, label }) {
  const [hover, setHover] = useState(null);
  const S = 350, c = S / 2, r0 = 58, r1 = 146, max = Math.max(1, ...bins);
  const peak = bins.indexOf(max);
  const arc = (h, v) => {
    const a0 = ((h - 0.42) / 24) * 2 * Math.PI - Math.PI / 2, a1 = ((h + 0.42) / 24) * 2 * Math.PI - Math.PI / 2;
    const r = r0 + (v / max) * (r1 - r0);
    const p = (a, rr) => `${c + rr * Math.cos(a)},${c + rr * Math.sin(a)}`;
    return `M${p(a0, r0)} L${p(a0, r)} A${r},${r} 0 0 1 ${p(a1, r)} L${p(a1, r0)} A${r0},${r0} 0 0 0 ${p(a0, r0)}Z`;
  };
  const h = hover ?? peak;
  return (
    <svg viewBox={`0 0 ${S} ${S}`} className="clock" role="img" aria-label={label}>
      {[0.33, 0.66, 1].map((f) => <circle key={f} cx={c} cy={c} r={r0 + f * (r1 - r0)} className="ring" />)}
      {bins.map((v, k) => (
        <path key={k} d={arc(k, v)} className={k === h ? 'bar on' : 'bar'} onPointerEnter={() => setHover(k)} onPointerLeave={() => setHover(null)}>
          <title>{`${String(k).padStart(2, '0')}:00 IST · ${v}`}</title></path>))}
      {[0, 6, 12, 18].map((k) => {
        const a = (k / 24) * 2 * Math.PI - Math.PI / 2;
        return <text key={k} x={c + (r1 + 14) * Math.cos(a)} y={c + (r1 + 14) * Math.sin(a) + 4} className="tick" textAnchor="middle">{String(k).padStart(2, '0')}</text>;
      })}
      <text x={c} y={c - 6} textAnchor="middle" className="centre-n">{bins[h]}</text>
      <text x={c} y={c + 16} textAnchor="middle" className="centre-l">{String(h).padStart(2, '0')}:00 IST</text>
    </svg>
  );
}

/** Scatter: news reports per crore people (log) vs NCRB crime rate. */
function Scatter({ att }) {
  const [hover, setHover] = useState(null);
  const W = 640, H = 360, L = 52, B = 40, T = 16, R = 16;
  const xs = att.pts.map((p) => Math.log10(p.perCrore)), ys = att.pts.map((p) => p.rate);
  const x0 = Math.floor(Math.min(...xs)), x1 = Math.ceil(Math.max(...xs)), y1 = Math.ceil(Math.max(...ys) / 200) * 200;
  const X = (v) => L + ((Math.log10(v) - x0) / (x1 - x0 || 1)) * (W - L - R);
  const Y = (v) => H - B - (v / y1) * (H - B - T);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="scatter" role="img" aria-label="News reports per crore people against official crime rate">
      {[0, 0.25, 0.5, 0.75, 1].map((f) => <g key={f}><line x1={L} x2={W - R} y1={Y(y1 * f)} y2={Y(y1 * f)} className="grid" />
        <text x={L - 8} y={Y(y1 * f) + 4} textAnchor="end" className="tick">{Math.round(y1 * f)}</text></g>)}
      {Array.from({ length: x1 - x0 + 1 }, (_, k) => x0 + k).map((e) => <g key={e}><line x1={X(10 ** e)} x2={X(10 ** e)} y1={T} y2={H - B} className="grid" />
        <text x={X(10 ** e)} y={H - B + 18} textAnchor="middle" className="tick">{10 ** e >= 1 ? 10 ** e : (10 ** e).toFixed(e < -1 ? 2 : 1)}</text></g>)}
      <text x={(W + L) / 2} y={H - 4} textAnchor="middle" className="axis">News reports per crore people (30 days, log scale)</text>
      <text x={14} y={(H - B) / 2} textAnchor="middle" className="axis" transform={`rotate(-90 14 ${(H - B) / 2})`}>NCRB crimes per lakh</text>
      {att.pts.map((p) => (
        <g key={p.state} onPointerEnter={() => setHover(p)} onPointerLeave={() => setHover(null)}>
          <circle cx={X(p.perCrore)} cy={Y(p.rate)} r={4 + Math.sqrt(p.popCrore) * 1.6} className={hover === p ? 'dot on' : 'dot'} />
          {(hover === p || p.reports >= 20) && <text x={X(p.perCrore) + 9} y={Y(p.rate) - 8} className="lbl">{p.state}</text>}
        </g>))}
      {hover && <text x={W - R} y={T + 12} textAnchor="end" className="lbl">{hover.state}: {hover.reports} reports · {hover.perCrore.toFixed(1)}/crore · NCRB {hover.rate}</text>}
    </svg>
  );
}

function Stream({ rows, cats }) {
  const max = Math.max(1, ...rows.map((r) => cats.reduce((a, c) => a + r[c], 0)));
  return (
    <div className="stream" role="img" aria-label="Reports per day by crime type">
      {rows.map((r) => (
        <div key={r.day} className="col" title={r.day}>
          <div className="stack" style={{ height: `${(cats.reduce((a, c) => a + r[c], 0) / max) * 100}%` }}>
            {cats.map((c) => r[c] > 0 && <span key={c} style={{ flex: r[c], background: rgb(c) }} title={`${c}: ${r[c]}`} />)}
          </div>
          <small>{r.day.slice(8)}</small>
        </div>))}
    </div>
  );
}

export default function Intel({ go }) {
  const { t, cat, num } = useLang();
  const [inc] = useJson('incidents.json');
  const [sum] = useJson('summary.json');
  const [off] = useJson('official.json');
  useReveal([!!inc, !!off]);
  const now = inc ? Date.parse(inc.generated_at) : 0;
  const hot = useMemo(() => (inc ? hotspots(inc.incidents, { now, top: 10 }) : []), [inc, now]);
  const sp = useMemo(() => (inc ? spikes(inc.incidents, now) : null), [inc, now]);
  const bins = useMemo(() => (inc ? clock(inc.incidents) : new Array(24).fill(0)), [inc]);
  const att = useMemo(() => (sum && off ? attention(sum.by_state, off.rows) : null), [sum, off]);
  const cats = (sum?.by_category || []).slice(0, 8).map(([c]) => c);
  const days = useMemo(() => (inc ? categoryDays(inc.incidents, cats) : []), [inc, cats.join()]); // eslint-disable-line react-hooks/exhaustive-deps
  const perDay = sum?.by_day?.length ? sum.total / sum.by_day.length : null;

  return (
    <main id="main" className="page intel">
      <div className="eyebrow">{t('intel_eyebrow')}</div>
      <h1 className="display">{t('intel_title')}</h1>
      <p className="sub">{t('intel_sub')}</p>

      <div className="kpis reveal">
        <div className="kpi spot"><div className="n mono"><Num to={sum?.total} /></div><div className="l">{t('c_30d')}</div></div>
        <div className="kpi spot"><div className="n mono"><Num to={sum?.last_24h} /></div><div className="l">{t('c_24h')}</div></div>
        <div className="kpi spot"><div className="n mono"><Num to={perDay} dp={1} /></div><div className="l">{t('k_perday')}</div></div>
        <div className="kpi spot"><div className="n mono"><Num to={sp?.rows.length} /></div><div className="l">{t('k_spikes')}</div></div>
      </div>

      <div className="intel-grid">
        <section className="panel spot reveal wide2">
          <header><h3>{t('i_hot_title')}</h3><span className="badge">{t('i_hot_method')}</span></header>
          <ol className="leader">
            {hot.map((h, k) => (
              <li key={h.name + k}>
                <button onClick={() => go('map', h.name)}>
                  <span className="rk mono">{String(k + 1).padStart(2, '0')}</span>
                  <span className="nm">{h.name}<small>{h.state}</small></span>
                  <span className="mixbar">{h.cats.slice(0, 6).map(([c, v]) => <i key={c} style={{ flex: v, background: rgb(c) }} title={`${cat(c)} ${v}`} />)}</span>
                  <span className="ct mono">{h.count}<small>+{h.last24} {t('i_today')}</small></span>
                </button>
              </li>))}
          </ol>
        </section>

        <section className="panel spot reveal">
          <header><h3>{t('i_clock_title')}</h3><span className="badge">IST</span></header>
          <Clock bins={bins} label={t('i_clock_title')} />
          <p className="cap">{t('i_clock_cap')}</p>
        </section>

        <section className="panel spot reveal wide2">
          <header><h3>{t('i_spike_title')}</h3><span className="badge">{t('i_spike_method')}</span></header>
          {sp && sp.historyDays < 1 ? <p className="cap">{t('i_spike_wait')}</p> : (
            <table className="data compact">
              <thead><tr><th>{t('i_state')}</th><th>{t('i_24h')}</th><th>{t('i_base')}</th><th>{t('i_ratio')}</th><th>p</th><th /></tr></thead>
              <tbody>{(sp?.all || []).filter((r) => r.base != null).slice(0, 10).map((r) => {
                const hotRow = r.p != null && r.p < 0.05 && r.recent >= 3;
                return (
                  <tr key={r.state} className={hotRow ? 'alert' : ''}>
                    <td>{r.state}</td><td className="mono">{r.recent}</td><td className="mono">{r.base.toFixed(1)}</td>
                    <td className="mono">{r.ratio != null ? `${r.ratio.toFixed(2)}×` : '–'}</td>
                    <td className="mono">{r.p != null ? r.p.toFixed(3) : '–'}</td>
                    <td>{hotRow ? <span className="pill hot">{t('i_unusual')}</span> : <span className="pill">{t('i_normal')}</span>}</td>
                  </tr>);
              })}</tbody>
            </table>)}
          <p className="cap">{t('i_spike_cap').replace('{d}', sp?.historyDays ?? 0)}</p>
        </section>

        <section className="panel spot reveal">
          <header><h3>{t('i_mix_title')}</h3><span className="badge">{days.length} {t('i_days')}</span></header>
          <Stream rows={days} cats={cats} />
          <div className="mix-legend">{cats.map((c) => <span key={c}><i style={{ background: rgb(c) }} />{cat(c)}</span>)}</div>
        </section>

        {att && att.pts.length > 3 && (
          <section className="panel spot reveal full">
            <header><h3>{t('i_att_title')}</h3>
              <span className="badge mono">r = {att.r?.toFixed(2)} · ρ = {att.rho?.toFixed(2)} · n = {att.pts.length}</span></header>
            <Scatter att={att} />
            <p className="cap">{t('i_att_cap').replace('{y}', att.year)}</p>
          </section>)}

        <section className="panel reveal full methods">
          <h3>{t('i_methods')}</h3>
          <ul>
            <li><b>{t('i_hot_title')}.</b> {t('m_hot')}</li>
            <li><b>{t('i_spike_title')}.</b> {t('m_spike')}</li>
            <li><b>{t('i_att_title')}.</b> {t('m_att')}</li>
            <li><b>{t('m_class_t')}.</b> {t('m_class')}</li>
          </ul>
        </section>
      </div>
      <p className="muted" style={{ marginTop: 24 }}>{num(sum?.total)} · {t('map_note')}</p>
    </main>
  );
}
