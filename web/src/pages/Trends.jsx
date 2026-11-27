import { useJson } from '../data.js';
import { useLang, rgb } from '../i18n.js';

function Bars({ rows, color = () => 'var(--accent)', fmt = (v) => v.toLocaleString('en-IN'), label = (k) => k }) {
  const max = Math.max(1, ...rows.map((r) => r[1]));
  return rows.map(([k, v]) => (
    <div key={k} className="hbar"><span>{label(k)}</span>
      <div><div className="b" style={{ width: `${(v / max) * 100}%`, background: color(k) }} /></div>
      <span className="v">{fmt(v)}</span></div>
  ));
}

function Daily({ days }) {
  if (!days?.length) return null;
  const W = 1100, H = 220, pad = 28;
  const max = Math.max(1, ...days.map((d) => d.total));
  const x = (i) => pad + (i * (W - 2 * pad)) / Math.max(1, days.length - 1);
  const y = (v) => H - pad - (v / max) * (H - 2 * pad);
  const path = days.map((d, i) => `${i ? 'L' : 'M'}${x(i)},${y(d.total)}`).join('');
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Reported incidents per day">
      <defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="#ff5a36" stopOpacity="0.35" /><stop offset="1" stopColor="#ff5a36" stopOpacity="0" /></linearGradient></defs>
      {[0.25, 0.5, 0.75, 1].map((f) => <line key={f} x1={pad} x2={W - pad} y1={y(max * f)} y2={y(max * f)} stroke="rgba(255,255,255,0.07)" />)}
      <path d={`${path}L${x(days.length - 1)},${H - pad}L${pad},${H - pad}Z`} fill="url(#g)" />
      <path d={path} fill="none" stroke="#ff5a36" strokeWidth="2.5" />
      {days.map((d, i) => (i % Math.ceil(days.length / 8) === 0 || i === days.length - 1) && (
        <text key={d.day} x={x(i)} y={H - 6} fill="#677184" fontSize="12" textAnchor="middle">{d.day.slice(5)}</text>))}
      <text x={pad} y={y(max) - 8} fill="#9aa4b2" fontSize="12">{max}</text>
    </svg>
  );
}

export default function Trends() {
  const { t, cat, num } = useLang();
  const [sum] = useJson('summary.json');
  const [off] = useJson('official.json');
  const rows = off?.rows || [];
  const latestStateYear = Math.max(0, ...rows.filter((r) => r.level === 'state').map((r) => r.year));
  const states = rows.filter((r) => r.level === 'state' && r.year === latestStateYear).sort((a, b) => b.crime_rate - a.crime_rate);
  const nat = rows.filter((r) => r.level === 'national').sort((a, b) => a.year - b.year);
  return (
    <main id="main" className="page">
      <div className="eyebrow">CrimeWatch India</div>
      <h1>{t('trends_title')}</h1>
      <p className="sub" style={{ color: 'var(--muted)', fontSize: 18, maxWidth: 680 }}>{t('trends_sub')}</p>
      <div className="grid2">
        <div className="card wide"><h3>{t('t_daily')}</h3><p className="cap">{t('t_daily_cap')}</p><Daily days={sum?.by_day} /></div>
        <div className="card"><h3>{t('t_cats')}</h3><p className="cap">{t('t_cats_cap')}</p>
          <Bars rows={sum?.by_category || []} color={(k) => rgb(k)} label={cat} /></div>
        <div className="card"><h3>{t('t_states')}</h3><p className="cap">{t('t_states_cap')}</p>
          <Bars rows={(sum?.by_state || []).slice(0, 15)} /></div>
        <div className="card"><h3>{t('t_nat')}</h3><p className="cap">{t('t_nat_cap')}</p>
          <Bars rows={nat.map((r) => [String(r.year), r.total_cases])} color={() => 'var(--info)'} fmt={num} /></div>
        <div className="card"><h3>{t('t_ncrb')}</h3><p className="cap">{t('t_ncrb_cap')}</p>
          <Bars rows={states.slice(0, 36).map((r) => [r.name, r.crime_rate])} color={() => 'var(--accent-2)'} fmt={(v) => v.toFixed(1)} /></div>
      </div>
    </main>
  );
}
